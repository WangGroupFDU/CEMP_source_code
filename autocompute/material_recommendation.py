
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable

from django.apps import apps
from django.db import models

from autocompute.molecule_lookup import _similarity, _smiles_to_fingerprint


DEFAULT_TOPK_POOL = 40
MAX_TOPK_POOL = 100
DEFAULT_RADIUS = 2
DEFAULT_N_BITS = 2048
ALLOWED_DOMAINS = {"auto", "ionic_liquid", "polymer", "crystal", "molecule"}


@dataclass(frozen=True)
class MaterialDatasetSpec:

    app_label: str
    model_name: str
    domain: str
    identifier_fields: tuple[str, ...]
    property_fields: tuple[str, ...]
    metadata_fields: tuple[str, ...] = ()
    smiles_fields: tuple[str, ...] = ()
    psmiles_fields: tuple[str, ...] = ()
    formula_fields: tuple[str, ...] = ()

    @property
    def source_table(self) -> str:

        return f"{self.app_label}.{self.model_name}"


DATASET_REGISTRY: tuple[MaterialDatasetSpec, ...] = (
    MaterialDatasetSpec(
        "ionic_liquid",
        "IL_properties",
        "ionic_liquid",
        ("label", "formula", "cation", "anion"),
        (
            "cation_type",
            "anion_type",
            "ECW",
            "melting_point",
            "conductivity",
            "viscosity",
            "density",
            "T_conductivity",
            "T_viscosity",
            "T_density",
            "conductivity_norm",
            "viscosity_norm",
            "density_norm",
        ),
        formula_fields=("formula",),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "IL_smiles_psi4",
        "ionic_liquid",
        ("name", "smile_form", "type"),
        ("*",),
        smiles_fields=("smile_form",),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "IL_smiles_rdkit",
        "ionic_liquid",
        ("name", "smile_form", "type"),
        ("*",),
        smiles_fields=("smile_form",),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "IL",
        "ionic_liquid",
        ("Name", "SMILES"),
        ("*",),
        metadata_fields=("Software", "Theory_Level", "Source"),
        smiles_fields=("SMILES",),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "Cation",
        "ionic_liquid",
        ("Name", "SMILES"),
        ("*",),
        metadata_fields=("Software", "Theory_Level", "Source"),
        smiles_fields=("SMILES",),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "Anion",
        "ionic_liquid",
        ("Name", "SMILES"),
        ("*",),
        metadata_fields=("Software", "Theory_Level", "Source"),
        smiles_fields=("SMILES",),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "IL_ML_data",
        "ionic_liquid",
        ("Name", "SMILES", "Anion_SMILES", "Cation_SMILES", "Type"),
        ("Conductivity_mS_per_cm", "Tm_K", "ECW_V"),
        metadata_fields=("Source",),
        smiles_fields=("SMILES", "Anion_SMILES", "Cation_SMILES"),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "IL_Tm_conductivity_ECW_data",
        "ionic_liquid",
        ("Name", "SMILES", "Anion_SMILES", "Cation_SMILES", "Type"),
        ("Conductivity_mS_per_cm", "Tm_K", "ECW_V"),
        metadata_fields=("Source",),
        smiles_fields=("SMILES", "Anion_SMILES", "Cation_SMILES"),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "Li_electrolyte",
        "ionic_liquid",
        ("Dimer_Name", "Dimer_SMILES", "Component_Name_A", "Component_SMILES_A", "Component_Name_B", "Component_SMILES_B"),
        ("*",),
        metadata_fields=("Software", "Theory_Level", "Source"),
        smiles_fields=("Dimer_SMILES", "Component_SMILES_A", "Component_SMILES_B"),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "metal_anion_energy",
        "ionic_liquid",
        ("Dimer_Name", "Dimer_SMILES", "Component_Name_A", "Component_SMILES_A", "Component_Name_B", "Component_SMILES_B"),
        ("*",),
        metadata_fields=("Software", "Theory_Level", "Source"),
        smiles_fields=("Dimer_SMILES", "Component_SMILES_A", "Component_SMILES_B"),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "electrolyte",
        "ionic_liquid",
        ("Component_Name_B", "Component_SMILES_B"),
        ("*",),
        metadata_fields=("Software", "Theory_Level", "Source"),
        smiles_fields=("Component_SMILES_B",),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "ILgenerator_IL",
        "ionic_liquid",
        ("Name", "SMILES", "Anion_Name", "Cation_Name", "Anion_SMILES", "Cation_SMILES"),
        ("*",),
        smiles_fields=("SMILES", "Anion_SMILES", "Cation_SMILES"),
    ),
    MaterialDatasetSpec(
        "polymer",
        "polymer_properties",
        "polymer",
        ("label", "formula"),
        ("*",),
        formula_fields=("formula",),
    ),
    MaterialDatasetSpec(
        "polymer",
        "polymer_smiles_psi4",
        "polymer",
        ("name", "smile_form", "type"),
        ("*",),
        smiles_fields=("smile_form",),
    ),
    MaterialDatasetSpec(
        "polymer",
        "polymer_smiles_rdkit",
        "polymer",
        ("name", "smile_form", "type"),
        ("*",),
        smiles_fields=("smile_form",),
    ),
    MaterialDatasetSpec(
        "polymer",
        "polyelectrolyte",
        "polymer",
        ("polyelectrolyte", "copolymer", "cation", "anion", "repeat_unit", "chemical_structure", "synonyms"),
        ("*",),
        metadata_fields=("reference",),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "Cation_QC_data",
        "ionic_liquid",
        ("Name", "SMILES", "Cation_type"),
        (
            "Energy_Hatree",
            "Thermal_correction_to_Gibbs_Free_Energy_Hatree",
            "Thermal_correction_to_Enthalpy_Hatree",
            "Entropy_J_per_mol_K",
            "HOMO_Hatree",
            "LUMO_Hatree",
            "Dipole_Debye",
            "Gibbs_Free_Energy_Hatree",
            "Enthalpy_Hatree",
            "HOMO_LUMO_Gap_eV",
        ),
        metadata_fields=("Software", "Theory_Level", "Source"),
        smiles_fields=("SMILES",),
    ),
    MaterialDatasetSpec(
        "ionic_liquid",
        "Anion_QC_data",
        "ionic_liquid",
        ("Name", "SMILES", "Anion_type"),
        (
            "Energy_Hatree",
            "Thermal_correction_to_Gibbs_Free_Energy_Hatree",
            "Thermal_correction_to_Enthalpy_Hatree",
            "Entropy_J_per_mol_K",
            "HOMO_Hatree",
            "LUMO_Hatree",
            "Dipole_Debye",
            "Gibbs_Free_Energy_Hatree",
            "Enthalpy_Hatree",
            "HOMO_LUMO_Gap_eV",
        ),
        metadata_fields=("Software", "Theory_Level", "Source"),
        smiles_fields=("SMILES",),
    ),
    MaterialDatasetSpec(
        "polymer",
        "experiment_polymer_data",
        "polymer",
        ("Name", "PSMILES"),
        (
            "Atomization_Energy_eV",
            "Bandgap_eV",
            "Bandgap_Bulk_eV",
            "Bandgap_Chain_eV",
            "CH4_Permeability_Barrer",
            "CO2_Permeability_Barrer",
            "Compressive_Strength_MPa",
            "Crystallization_Temperature_K",
            "Crystallization_Tendency_percentage",
            "Dielectric_Constant_Electronic",
            "Dielectric_Constant_Ionic",
            "Dielectric_Constant_Total",
            "Density",
            "Electron_Affinity_eV",
            "Elongation_at_Break_percentage",
            "Flexural_Strength_MPa",
            "Tg_K",
            "H2_Permeability_Barrer",
            "Hardness_MPa",
            "He_Permeability_Barrer",
            "Impact_Strength_kJ_per_m2",
            "Ion_Exchange_Capacity_meq_per_g",
            "Ionization_Energy_eV",
            "Limiting_Oxygen_Index_percentage",
            "Lower_Critical_Solution_Temperature_K",
            "Tm_K",
            "Methanol_Permeability_cm2_per_s",
            "N2_Permeability_Barrer",
            "O2_Permeability_Barrer",
            "Refractive_Index",
            "Swelling_Degree_percentage",
            "Thermal_Conductivity_W_per_mK",
            "Tensile_Strength_MPa",
            "Td_K",
            "Upper_Critical_Solution_Temperature_K",
            "Water_Contact_Angle",
            "Water_Uptake_percentage",
            "Youngs_Modulus_MPa",
        ),
        metadata_fields=("Reference",),
        psmiles_fields=("PSMILES",),
    ),
    MaterialDatasetSpec(
        "polymer",
        "calculated_monomer_data",
        "polymer",
        ("Name", "SMILES", "Monomer_Type"),
        (
            "Neutral_Energy_Hatree",
            "Oxidation_Energy_Hatree",
            "Reduction_Energy_Hatree",
            "HOMO_eV",
            "LUMO_eV",
            "Dipole_Debye",
            "Gibbs_Free_Energy_Hatree",
            "Enthalpy_Hatree",
            "HOMO_LUMO_Gap_eV",
            "Oxidation_Potential_V",
            "Reduction_Potential_V",
            "Redox_Window_V",
            "Corrected_Redox_Window_V",
            "Water_Solvation_Free_Energy_kJ_per_mol",
            "DMSO_Solvation_Free_Energy_kJ_per_mol",
            "DMF_Solvation_Free_Energy_kJ_per_mol",
        ),
        metadata_fields=("Software", "Theory_Level", "Source"),
        smiles_fields=("SMILES",),
    ),
    MaterialDatasetSpec(
        "polymer",
        "calculated_polymer_data",
        "polymer",
        ("Name", "psmiles", "SMILES", "reaction_type"),
        (
            "Energy_Hatree",
            "es",
            "Isotropic_Polarizability_au",
            "HOMO_eV",
            "LUMO_eV",
            "Dipole_Debye",
            "Gibbs_Free_Energy_Hatree",
            "Enthalpy_Hatree",
            "HOMO_LUMO_Gap_eV",
        ),
        metadata_fields=("Software", "Theory_Level", "Source"),
        smiles_fields=("SMILES",),
        psmiles_fields=("psmiles",),
    ),
    MaterialDatasetSpec(
        "crystals",
        "Crystal",
        "crystal",
        (
            "crystal",
            "label",
            "chemsys",
            "formula_pretty",
            "is_gap_direct",
            "is_magnetic",
            "is_metal",
            "is_stable",
            "ordering",
            "theoretical",
        ),
        (
            "band_gap",
            "density",
            "density_atomic",
            "efermi",
            "energy_above_hull",
            "energy_per_atom",
            "formation_energy_per_atom",
            "nelements",
            "nsites",
            "num_magnetic_sites",
            "num_unique_magnetic_sites",
            "total_magnetization",
            "volume",
        ),
        formula_fields=("formula_pretty",),
    ),
    MaterialDatasetSpec(
        "crystals",
        "Crystal_properties",
        "crystal",
        ("label", "formula"),
        ("*",),
        formula_fields=("formula",),
    ),
    MaterialDatasetSpec(
        "crystals",
        "Crystal_smiles_psi4",
        "crystal",
        ("name", "smile_form", "type"),
        ("energy", "HOMO", "LUMO", "dipole_x", "dipole_y", "dipole_z", "dipole_total"),
        smiles_fields=("smile_form",),
    ),
    MaterialDatasetSpec(
        "crystals",
        "Crystal_smiles_rdkit",
        "crystal",
        ("name", "smile_form", "type"),
        (
            "Asphericity",
            "Eccentricity",
            "NPR1",
            "NPR2",
            "PMI1",
            "PMI2",
            "PMI3",
            "RadiusOfGyration",
            "SpherocityIndex",
            "ExactMolWt",
            "FpDensityMorgan1",
            "FpDensityMorgan2",
            "HeavyAtomMolWt",
            "MaxAbsPartialCharge",
            "MaxPartialCharge",
            "MinPartialCharge",
            "NumRadicalElectrons",
            "NumValenceElectrons",
            "volume",
        ),
        smiles_fields=("smile_form",),
    ),
)


def search_material_recommendation_candidates(
    query: str,
    *,
    domains: Iterable[str] | None = None,
    topk_pool: Any = DEFAULT_TOPK_POOL,
    seed_molecules: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    normalized_query = str(query or "").strip()
    if not normalized_query:
        raise ValueError("Missing required field: query")

    domain_values = _normalize_domains(domains)
    topk_value = _normalize_topk_pool(topk_pool)
    seed_fingerprints = _build_seed_fingerprints(seed_molecules)
    query_profile = _build_query_profile(normalized_query)

    candidates: list[dict[str, Any]] = []
    databases_searched: list[str] = []
    database_errors: list[dict[str, str]] = []

    for spec in _iter_domain_specs(domain_values):
        try:
            model = apps.get_model(spec.app_label, spec.model_name)
            _validate_spec_fields(model, spec)
            table_candidates = list(_iter_candidates(model, spec, seed_fingerprints, query_profile))
            candidates.extend(table_candidates)
            databases_searched.append(spec.source_table)
        except Exception as exc:  
            database_errors.append({"database": spec.source_table, "error": str(exc)})

    candidates.sort(key=lambda item: (float(item.get("_score", 0.0)), str(item.get("candidate_id", ""))), reverse=True)
    trimmed_candidates = [_strip_internal_fields(item) for item in candidates[:topk_value]]

    return {
        "status": "ok",
        "query": normalized_query,
        "domains": sorted(domain_values),
        "topk_pool": topk_value,
        "candidate_pool": trimmed_candidates,
        "candidates": trimmed_candidates,
        "count": len(trimmed_candidates),
        "databases_searched": databases_searched,
        "database_errors": database_errors,
        "candidate_count": len(candidates),
    }


def _normalize_domains(domains: Iterable[str] | None) -> set[str]:

    values = [str(item or "").strip().lower() for item in (domains or ["auto"])]
    cleaned = {item for item in values if item}
    if not cleaned:
        cleaned = {"auto"}
    unsupported = cleaned - ALLOWED_DOMAINS
    if unsupported:
        raise ValueError(f"Unsupported domains: {', '.join(sorted(unsupported))}")
    if "auto" in cleaned:
        return {"ionic_liquid", "polymer", "crystal", "molecule"}
    return cleaned


def _normalize_topk_pool(topk_pool: Any) -> int:

    try:
        value = int(topk_pool)
    except (TypeError, ValueError):
        value = DEFAULT_TOPK_POOL
    return max(1, min(value, MAX_TOPK_POOL))


def _build_seed_fingerprints(seed_molecules: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:

    seeds: list[dict[str, Any]] = []
    for item in seed_molecules or []:
        if not isinstance(item, dict):
            continue
        smiles = str(item.get("smiles", "") or "").strip()
        if not smiles:
            continue
        fingerprint = _smiles_to_fingerprint(smiles, radius=DEFAULT_RADIUS, n_bits=DEFAULT_N_BITS, fail_fast=True)
        seeds.append(
            {
                "name": str(item.get("name", "") or "").strip(),
                "smiles": smiles,
                "fingerprint": fingerprint,
            }
        )
    return seeds


def _iter_domain_specs(domains: set[str]) -> Iterable[MaterialDatasetSpec]:

    for spec in DATASET_REGISTRY:
        if spec.domain in domains:
            yield spec
        elif "molecule" in domains and (spec.smiles_fields or spec.psmiles_fields):
            yield spec


def _validate_spec_fields(model: type[models.Model], spec: MaterialDatasetSpec) -> None:

    missing: list[str] = []
    for field_name in [
        *spec.identifier_fields,
        *spec.property_fields,
        *spec.metadata_fields,
        *spec.smiles_fields,
        *spec.psmiles_fields,
        *spec.formula_fields,
    ]:
        if field_name == "*":
            continue
        try:
            model._meta.get_field(field_name)
        except Exception:
            missing.append(field_name)
    if missing:
        raise ValueError(f"Invalid recommendation dataset fields: {', '.join(missing)}")


def _iter_candidates(
    model: type[models.Model],
    spec: MaterialDatasetSpec,
    seed_fingerprints: list[dict[str, Any]],
    query_profile: dict[str, Any],
) -> Iterable[dict[str, Any]]:

    for obj in model.objects.all().iterator(chunk_size=1000):
        property_fields = _resolve_property_fields(model, spec)
        properties = _extract_fields(obj, property_fields)
        if not properties:
            continue
        identifiers = _extract_fields(obj, spec.identifier_fields)
        metadata = _extract_fields(obj, spec.metadata_fields)
        name = _first_value(identifiers, ("Name", "name", "label", "crystal")) or ""
        smiles = _first_value(identifiers, (*spec.smiles_fields, "SMILES", "smile_form")) or ""
        psmiles = _first_value(identifiers, (*spec.psmiles_fields, "PSMILES", "psmiles")) or ""
        formula = _first_value(identifiers, (*spec.formula_fields, "formula", "formula_pretty")) or ""
        seed_similarity = _max_seed_similarity(str(smiles or psmiles), seed_fingerprints)
        score, score_reasons = _score_candidate(properties, metadata, spec, query_profile, seed_similarity)

        yield {
            "candidate_id": f"{spec.source_table}:{getattr(obj, 'pk', '')}",
            "domain": spec.domain,
            "name": name,
            "smiles": smiles,
            "psmiles": psmiles,
            "formula": formula,
            "source_table": spec.source_table,
            "properties": properties,
            "metadata": metadata,
            "evidence_level": _infer_evidence_level(spec, metadata),
            "seed_similarity": seed_similarity,
            "score_reasons": score_reasons,
            "_score": score,
        }


def _resolve_property_fields(model: type[models.Model], spec: MaterialDatasetSpec) -> tuple[str, ...]:

    if "*" not in spec.property_fields:
        return spec.property_fields
    excluded = {
        "id",
        *spec.identifier_fields,
        *spec.metadata_fields,
        *spec.smiles_fields,
        *spec.psmiles_fields,
        *spec.formula_fields,
    }
    return tuple(field.name for field in model._meta.concrete_fields if field.name not in excluded)


def _extract_fields(obj: models.Model, field_names: Iterable[str]) -> dict[str, Any]:

    result: dict[str, Any] = {}
    for field_name in field_names:
        value = _json_value(getattr(obj, field_name, None))
        if _is_non_empty_value(value):
            result[field_name] = value
    return result


def _first_value(values: dict[str, Any], keys: Iterable[str]) -> Any:

    for key in keys:
        value = values.get(key)
        if _is_non_empty_value(value):
            return value
    return ""


def _is_non_empty_value(value: Any) -> bool:

    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        return bool(stripped) and stripped.lower() not in {"nan", "none", "null"}
    if isinstance(value, float) and math.isnan(value):
        return False
    return True


def _json_value(value: Any) -> Any:

    if isinstance(value, Decimal):
        return float(value)
    return value


def _max_seed_similarity(smiles: str, seed_fingerprints: list[dict[str, Any]]) -> float | None:

    if not seed_fingerprints or not smiles:
        return None
    try:
        candidate_fp = _smiles_to_fingerprint(smiles, radius=DEFAULT_RADIUS, n_bits=DEFAULT_N_BITS, fail_fast=False)
    except Exception:
        return None
    if candidate_fp is None:
        return None
    scores = [_similarity(seed["fingerprint"], candidate_fp, "tanimoto") for seed in seed_fingerprints]
    return max(scores) if scores else None


def _build_query_profile(query: str) -> dict[str, Any]:

    lowered = query.lower()
    fields: dict[str, str] = {}
    marker_groups = [
        (("电导", "conductivity", "离子传导"), ("Conductivity_mS_per_cm", "conductivity", "conductivity_norm"), "high"),
        (("低熔点", "低 tm", "low melting", "low tm"), ("Tm_K", "Tm", "melting_point"), "low"),
        (("熔点", "melting", "tm"), ("Tm_K", "Tm", "melting_point"), "high"),
        (("ecw", "电化学窗口", "redox window", "氧化稳定", "还原稳定"), ("ECW_V", "ECW", "Redox_Window_V", "Corrected_Redox_Window_V", "Component_B_ECW_V"), "high"),
        (("介电", "dielectric"), ("Dielectric_Constant_Total", "Dielectric_Constant_Electronic", "Dielectric_Constant_Ionic", "dielectric_constant"), "high"),
        (("tg", "玻璃化"), ("Tg_K",), "high"),
        (("低 tg", "low tg"), ("Tg_K",), "low"),
        (("力学", "mechanical", "强度", "模量"), ("Youngs_Modulus_MPa", "Tensile_Strength_MPa", "Compressive_Strength_MPa", "Flexural_Strength_MPa", "Hardness_MPa"), "high"),
        (("band gap", "bandgap", "带隙"), ("band_gap", "Bandgap_eV", "Bandgap_Bulk_eV", "Bandgap_Chain_eV", "HOMO_LUMO_Gap_eV"), "high"),
        (("低 band gap", "低带隙", "low band gap", "low bandgap"), ("band_gap", "Bandgap_eV", "Bandgap_Bulk_eV", "Bandgap_Chain_eV"), "low"),
        (("稳定", "stable", "energy above hull"), ("energy_above_hull", "formation_energy_per_atom", "is_stable"), "low"),
        (("粘度", "黏度", "viscosity"), ("viscosity", "viscosity_norm"), "low"),
        (("密度", "density"), ("density", "Density"), "context"),
        (("偶极", "dipole"), ("Dipole_Debye", "dipole_total", "Dimer_Dipole_Debye"), "high"),
        (("溶剂化", "solvation"), ("Water_Solvation_Free_Energy_kJ_per_mol", "DMSO_Solvation_Free_Energy_kJ_per_mol", "DMF_Solvation_Free_Energy_kJ_per_mol"), "context"),
    ]
    for markers, property_fields, direction in marker_groups:
        if any(marker in lowered or marker in query for marker in markers):
            for field_name in property_fields:
                fields[field_name] = direction

    if any(marker in lowered or marker in query for marker in ["电解液", "electrolyte", "锂电池"]):
        fields.setdefault("Conductivity_mS_per_cm", "high")
        fields.setdefault("Tm_K", "low")
        fields.setdefault("ECW_V", "high")
    if any(marker in lowered or marker in query for marker in ["聚合物电解质", "polymer electrolyte"]):
        fields.setdefault("Dielectric_Constant_Total", "high")
        fields.setdefault("Tg_K", "context")
        fields.setdefault("Youngs_Modulus_MPa", "high")
    if any(marker in lowered or marker in query for marker in ["电极", "electrode"]):
        fields.setdefault("energy_above_hull", "low")
        fields.setdefault("band_gap", "context")

    return {"target_fields": fields, "query": query}


def _score_candidate(
    properties: dict[str, Any],
    metadata: dict[str, Any],
    spec: MaterialDatasetSpec,
    query_profile: dict[str, Any],
    seed_similarity: float | None,
) -> tuple[float, list[str]]:

    score = 0.0
    reasons: list[str] = []
    targets: dict[str, str] = query_profile.get("target_fields", {})
    for field_name, direction in targets.items():
        if field_name not in properties:
            continue
        value = properties[field_name]
        score += 3.0
        reasons.append(f"contains target property {field_name}")
        numeric = _to_float(value)
        if numeric is not None:
            score += _directional_numeric_score(field_name, numeric, direction)

    evidence_level = _infer_evidence_level(spec, metadata)
    if evidence_level == "direct_experimental_property":
        score += 4.0
        reasons.append("direct experimental property evidence")
    elif evidence_level == "direct_database_property":
        score += 2.5
        reasons.append("direct database property evidence")
    elif evidence_level == "computed_descriptor":
        score += 1.0
        reasons.append("computed descriptor evidence")

    if seed_similarity is not None:
        score += seed_similarity * 5.0
        reasons.append(f"seed similarity {seed_similarity:.3f}")

    score += min(len(properties), 12) * 0.1
    return score, reasons


def _to_float(value: Any) -> float | None:

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _directional_numeric_score(field_name: str, value: float, direction: str) -> float:

    lower = field_name.lower()
    if direction == "high":
        if "conductivity" in lower:
            return min(max(value, 0.0) / 20.0, 5.0)
        if "ecw" in lower or "redox_window" in lower:
            return min(max(value, 0.0), 8.0) / 1.5
        if "dielectric" in lower:
            return min(max(value, 0.0) / 20.0, 5.0)
        if "tg" in lower or "tm" in lower:
            return min(max(value, 0.0) / 150.0, 5.0)
        if "band" in lower or "gap" in lower:
            return min(max(value, 0.0), 8.0) / 2.0
        return min(abs(value) / 100.0, 2.0)
    if direction == "low":
        if "tm" in lower or "melting" in lower or "tg" in lower:
            return min(max(500.0 - value, 0.0) / 80.0, 5.0)
        if "energy_above_hull" in lower:
            return 6.0 if value <= 0.05 else max(0.0, 2.0 - value)
        if "viscosity" in lower:
            return min(10.0 / max(abs(value), 1.0), 5.0)
        if "band" in lower or "gap" in lower:
            return min(5.0 / max(abs(value), 0.2), 5.0)
    return 0.5


def _infer_evidence_level(spec: MaterialDatasetSpec, metadata: dict[str, Any]) -> str:

    name = spec.model_name.lower()
    if "experiment" in name or "reference" in {key.lower() for key in metadata}:
        return "direct_experimental_property"
    if any(marker in name for marker in ["calculated", "qc", "psi4", "rdkit"]):
        return "computed_descriptor"
    return "direct_database_property"


def _strip_internal_fields(candidate: dict[str, Any]) -> dict[str, Any]:

    cleaned = dict(candidate)
    cleaned.pop("_score", None)
    return cleaned
