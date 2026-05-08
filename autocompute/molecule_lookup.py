
from __future__ import annotations

import datetime as _datetime
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable

from django.apps import apps
from django.db import DatabaseError, models

try:
    from rdkit import Chem, DataStructs
    from rdkit.Chem import AllChem
except Exception:  
    Chem = None
    DataStructs = None
    AllChem = None


DEFAULT_RADIUS = 2
DEFAULT_N_BITS = 2048
DEFAULT_TOPK = 3
EXACT_MATCH_THRESHOLD = 0.999999


@dataclass(frozen=True)
class MoleculeDatasetSpec:

    app_label: str
    model_name: str
    smiles_field: str
    name_field: str | None
    molecule_role: str

    @property
    def database_name(self) -> str:

        return f"{self.app_label}.{self.model_name}"

    @property
    def search_scope(self) -> str:

        return f"{self.database_name}.{self.smiles_field}"


@dataclass
class MoleculeCandidate:

    database: str
    molecule_role: str
    name: str
    smiles: str
    properties: dict[str, Any]
    fingerprint: Any



DATASET_REGISTRY: tuple[MoleculeDatasetSpec, ...] = (
    MoleculeDatasetSpec("ionic_liquid", "IL_smiles_psi4", "smile_form", "name", "SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "IL_smiles_rdkit", "smile_form", "name", "SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "IL", "SMILES", "Name", "SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "Cation", "SMILES", "Name", "SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "Anion", "SMILES", "Name", "SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "electrolyte", "Component_SMILES_B", "Component_Name_B", "Component_SMILES_B"),
    MoleculeDatasetSpec("ionic_liquid", "Li_electrolyte", "Dimer_SMILES", "Dimer_Name", "Dimer_SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "Li_electrolyte", "Component_SMILES_A", "Component_Name_A", "Component_SMILES_A"),
    MoleculeDatasetSpec("ionic_liquid", "Li_electrolyte", "Component_SMILES_B", "Component_Name_B", "Component_SMILES_B"),
    MoleculeDatasetSpec("ionic_liquid", "metal_anion_energy", "Dimer_SMILES", "Dimer_Name", "Dimer_SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "metal_anion_energy", "Component_SMILES_A", "Component_Name_A", "Component_SMILES_A"),
    MoleculeDatasetSpec("ionic_liquid", "metal_anion_energy", "Component_SMILES_B", "Component_Name_B", "Component_SMILES_B"),
    MoleculeDatasetSpec("ionic_liquid", "IL_ML_data", "SMILES", "Name", "SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "IL_ML_data", "Anion_SMILES", "Name", "Anion_SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "IL_ML_data", "Cation_SMILES", "Name", "Cation_SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "Cation_QC_data", "SMILES", "Name", "SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "Anion_QC_data", "SMILES", "Name", "SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "IL_Tm_conductivity_ECW_data", "SMILES", "Name", "SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "IL_Tm_conductivity_ECW_data", "Anion_SMILES", "Name", "Anion_SMILES"),
    MoleculeDatasetSpec("ionic_liquid", "IL_Tm_conductivity_ECW_data", "Cation_SMILES", "Name", "Cation_SMILES"),
    MoleculeDatasetSpec("polymer", "polymer_smiles_psi4", "smile_form", "name", "SMILES"),
    MoleculeDatasetSpec("polymer", "polymer_smiles_rdkit", "smile_form", "name", "SMILES"),
    MoleculeDatasetSpec("polymer", "experiment_polymer_data", "PSMILES", "Name", "PSMILES"),
    MoleculeDatasetSpec("polymer", "calculated_monomer_data", "SMILES", "Name", "SMILES"),
    MoleculeDatasetSpec("polymer", "calculated_polymer_data", "psmiles", "Name", "PSMILES"),
    MoleculeDatasetSpec("polymer", "calculated_polymer_data", "SMILES", "Name", "SMILES"),
    MoleculeDatasetSpec("crystals", "Crystal_smiles_psi4", "smile_form", "name", "SMILES"),
    MoleculeDatasetSpec("crystals", "Crystal_smiles_rdkit", "smile_form", "name", "SMILES"),
)


_CANDIDATE_CACHE: dict[tuple[int, int], tuple[list[MoleculeCandidate], list[str], list[dict[str, str]]]] = {}


def clear_molecule_lookup_cache() -> None:

    _CANDIDATE_CACHE.clear()


def lookup_molecule_property_similarity(
    smiles: str,
    *,
    topk: int = DEFAULT_TOPK,
    method: str = "tanimoto",
    radius: int = DEFAULT_RADIUS,
    n_bits: int = DEFAULT_N_BITS,
) -> dict[str, Any]:

    query_smiles = str(smiles or "").strip()
    if not query_smiles:
        raise ValueError("Missing required field: smiles")

    topk_value = _normalize_topk(topk)
    method_value = _normalize_method(method)
    query_fp = _smiles_to_fingerprint(query_smiles, radius=radius, n_bits=n_bits, fail_fast=True)
    candidates, searched, dataset_errors = _get_candidates(radius=radius, n_bits=n_bits)

    scored_matches: list[dict[str, Any]] = []
    for candidate in candidates:
        score = _similarity(query_fp, candidate.fingerprint, method_value)
        scored_matches.append(_format_match(candidate, score))

    scored_matches.sort(key=lambda item: item["similarity"], reverse=True)
    exact_matches = [item for item in scored_matches if item["similarity"] >= EXACT_MATCH_THRESHOLD]
    has_exact_match = bool(exact_matches)

    return {
        "status": "found" if has_exact_match else "similar",
        "has_exact_match": has_exact_match,
        "needs_qc_prompt": not has_exact_match,
        "query": {
            "smiles": query_smiles,
            "method": method_value,
            "radius": int(radius),
            "n_bits": int(n_bits),
        },
        "exact_matches": exact_matches,
        "similar_matches": [] if has_exact_match else scored_matches[:topk_value],
        "databases_searched": searched,
        "database_errors": dataset_errors,
        "candidate_count": len(candidates),
    }


def _normalize_topk(topk: Any) -> int:

    try:
        value = int(topk)
    except (TypeError, ValueError):
        value = DEFAULT_TOPK
    return max(1, min(value, 20))


def _normalize_method(method: Any) -> str:

    value = str(method or "tanimoto").strip().lower()
    if value not in {"tanimoto", "dice", "cosine", "tversky"}:
        raise ValueError("Unsupported similarity method. Allowed: tanimoto, dice, cosine, tversky")
    return value


def _smiles_to_fingerprint(smiles: str, *, radius: int, n_bits: int, fail_fast: bool) -> Any:

    if Chem is None or AllChem is None:
        raise RuntimeError("RDKit is not available on this server; molecule similarity search cannot run.")
    mol = Chem.MolFromSmiles(str(smiles or "").strip())
    if mol is None:
        if fail_fast:
            raise ValueError(f"Invalid SMILES/PSMILES: {smiles}")
        return None
    return AllChem.GetMorganFingerprintAsBitVect(mol, radius=int(radius), nBits=int(n_bits))


def _get_candidates(*, radius: int, n_bits: int) -> tuple[list[MoleculeCandidate], list[str], list[dict[str, str]]]:

    cache_key = (int(radius), int(n_bits))
    if cache_key in _CANDIDATE_CACHE:
        return _CANDIDATE_CACHE[cache_key]

    candidates: list[MoleculeCandidate] = []
    searched: list[str] = []
    errors: list[dict[str, str]] = []

    for spec in DATASET_REGISTRY:
        try:
            model = apps.get_model(spec.app_label, spec.model_name)
            _validate_dataset_fields(model, spec)
            candidates.extend(_iter_candidates_for_spec(model, spec, radius=radius, n_bits=n_bits))
            searched.append(spec.search_scope)
        except Exception as exc:
            
            
            errors.append({"database": spec.search_scope, "error": str(exc)})

    result = (candidates, searched, errors)
    _CANDIDATE_CACHE[cache_key] = result
    return result


def _validate_dataset_fields(model: type[models.Model], spec: MoleculeDatasetSpec) -> None:

    try:
        model._meta.get_field(spec.smiles_field)
        if spec.name_field:
            model._meta.get_field(spec.name_field)
    except Exception as exc:
        raise ValueError(f"Invalid dataset registry entry for {spec.search_scope}: {exc}") from exc


def _iter_candidates_for_spec(
    model: type[models.Model],
    spec: MoleculeDatasetSpec,
    *,
    radius: int,
    n_bits: int,
) -> Iterable[MoleculeCandidate]:

    for obj in model.objects.all().iterator(chunk_size=1000):
        smiles = str(getattr(obj, spec.smiles_field, "") or "").strip()
        if not smiles:
            continue
        fingerprint = _smiles_to_fingerprint(smiles, radius=radius, n_bits=n_bits, fail_fast=False)
        if fingerprint is None:
            continue
        yield MoleculeCandidate(
            database=spec.database_name,
            molecule_role=spec.molecule_role,
            name=_extract_name(obj, spec),
            smiles=smiles,
            properties=_extract_properties(obj, spec),
            fingerprint=fingerprint,
        )


def _extract_name(obj: models.Model, spec: MoleculeDatasetSpec) -> str:

    candidate_fields = [
        spec.name_field,
        "Name",
        "name",
        "Dimer_Name",
        "Component_Name_A",
        "Component_Name_B",
    ]
    for field_name in candidate_fields:
        if not field_name:
            continue
        value = getattr(obj, field_name, None)
        if value not in (None, ""):
            return str(value)
    return ""


def _extract_properties(obj: models.Model, spec: MoleculeDatasetSpec) -> dict[str, Any]:

    excluded = {"id", spec.smiles_field}
    properties: dict[str, Any] = {}
    for field in obj._meta.concrete_fields:
        field_name = field.name
        if field_name in excluded:
            continue
        properties[field_name] = _json_value(getattr(obj, field_name, None))
    return properties


def _json_value(value: Any) -> Any:

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (_datetime.datetime, _datetime.date, _datetime.time)):
        return value.isoformat()
    return str(value)


def _similarity(fp_a: Any, fp_b: Any, method: str) -> float:

    if method == "tanimoto":
        return float(DataStructs.TanimotoSimilarity(fp_a, fp_b))
    if method == "dice":
        return float(DataStructs.DiceSimilarity(fp_a, fp_b))
    if method == "cosine":
        return float(DataStructs.CosineSimilarity(fp_a, fp_b))
    if method == "tversky":
        return float(DataStructs.TverskySimilarity(fp_a, fp_b, 0.5, 0.5))
    raise ValueError(f"Unsupported similarity method: {method}")


def _format_match(candidate: MoleculeCandidate, score: float) -> dict[str, Any]:

    return {
        "database": candidate.database,
        "molecule_role": candidate.molecule_role,
        "name": candidate.name,
        "smiles": candidate.smiles,
        "similarity": score,
        "similarity_percent": f"{score * 100:.2f}%",
        "properties": candidate.properties,
    }
