from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from rdkit import Chem


DATABASE_COLUMNS = ["FileName", "SMILES"]


def _normalize_database_root(settings_result: Dict[str, object], key: str, database_name: str) -> Path:
    if not isinstance(settings_result, dict):
        raise TypeError("settings_result must be the dict returned by load_and_apply_settings()")
    raw_root = settings_result.get(key)
    if not raw_root:
        raise KeyError(f"Missing database root in settings result: {key}")
    return Path(str(raw_root)).expanduser().resolve() / database_name


def get_gaussian_database_paths(settings_result: Dict[str, object]) -> Tuple[str, str, str]:
    root = _normalize_database_root(settings_result, "gaussian_database_path", "Gaussian_database")
    optfreq = root / "opt+freq"
    resppolymer = root / "RESPpolymer"
    optfreq.mkdir(parents=True, exist_ok=True)
    resppolymer.mkdir(parents=True, exist_ok=True)
    return str(root), str(optfreq), str(resppolymer)


def get_orca_database_paths(settings_result: Dict[str, object]) -> Tuple[str, str, str]:
    root = _normalize_database_root(settings_result, "orca_database_path", "ORCA_database")
    optfreq = root / "opt+freq"
    resppolymer = root / "RESPpolymer"
    optfreq.mkdir(parents=True, exist_ok=True)
    resppolymer.mkdir(parents=True, exist_ok=True)
    return str(root), str(optfreq), str(resppolymer)


def ensure_database_excel(database_directory: str) -> str:
    directory = Path(database_directory)
    directory.mkdir(parents=True, exist_ok=True)
    excel_path = directory / "molecule.xlsx"
    if not excel_path.exists():
        pd.DataFrame(columns=DATABASE_COLUMNS).to_excel(excel_path, index=False)
        return str(excel_path)

    df = pd.read_excel(excel_path)
    changed = False
    for column in DATABASE_COLUMNS:
        if column not in df.columns:
            df[column] = ""
            changed = True
    if changed:
        df = df[DATABASE_COLUMNS]
        df.to_excel(excel_path, index=False)
    return str(excel_path)


def canonicalize_smiles(smiles: object) -> Optional[str]:
    if smiles is None or (isinstance(smiles, float) and pd.isna(smiles)):
        return None
    text = str(smiles).strip()
    if not text:
        return None
    mol = Chem.MolFromSmiles(text)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol)


def sanitize_working_name(name: object) -> str:
    return str(name).strip().replace(" ", "_")


def _load_database_dataframe(database_excel_path: str) -> pd.DataFrame:
    excel_path = Path(database_excel_path)
    ensure_database_excel(str(excel_path.parent))
    df = pd.read_excel(excel_path)
    for column in DATABASE_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    df = df[DATABASE_COLUMNS].copy()
    df["FileName"] = df["FileName"].fillna("").astype(str).str.strip()
    df["SMILES"] = df["SMILES"].apply(canonicalize_smiles)
    df = df[(df["FileName"] != "") & df["SMILES"].notna()].copy()
    return df


def _filter_clean_database_rows(df: pd.DataFrame) -> pd.DataFrame:
    unique_df = df.drop_duplicates(subset=DATABASE_COLUMNS, keep="first").copy()
    if unique_df.empty:
        return unique_df

    ambiguous_filenames = set(
        unique_df.groupby("FileName")["SMILES"].nunique().loc[lambda s: s > 1].index
    )
    ambiguous_smiles = set(
        unique_df.groupby("SMILES")["FileName"].nunique().loc[lambda s: s > 1].index
    )
    clean_df = unique_df[
        ~unique_df["FileName"].isin(ambiguous_filenames)
        & ~unique_df["SMILES"].isin(ambiguous_smiles)
    ].copy()
    return clean_df


def read_database_excel_to_dict(database_path: str) -> Dict[str, str]:
    df = _load_database_dataframe(database_path)
    clean_df = _filter_clean_database_rows(df)
    return dict(zip(clean_df["SMILES"], clean_df["FileName"]))


def compare_smiles_dicts(system_dict: Dict[str, str], database_dict: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    normalized_system: Dict[str, str] = {}
    for smiles, name in system_dict.items():
        canonical_smiles = canonicalize_smiles(smiles)
        if canonical_smiles is None:
            continue
        normalized_system.setdefault(canonical_smiles, name)

    not_found: Dict[str, str] = {}
    found: Dict[str, str] = {}
    for smiles, name in normalized_system.items():
        if smiles in database_dict:
            found[smiles] = name
        else:
            not_found[smiles] = name
    return not_found, found


def _iter_stem_files(directory: str, stem: str) -> List[Path]:
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    matched_files = [
        path for path in dir_path.iterdir()
        if path.is_file() and path.name != "molecule.xlsx" and path.stem == stem
    ]
    return sorted(matched_files, key=lambda path: path.name)


def _storage_prefix_for_database(database_directory: str) -> str:
    normalized_path = Path(database_directory).as_posix().lower()
    if "gaussian_database" in normalized_path and normalized_path.endswith("/opt+freq"):
        return "g16_optfreq_"
    if "gaussian_database" in normalized_path and normalized_path.endswith("/resppolymer"):
        return "g16_resppolymer_"
    if "orca_database" in normalized_path and normalized_path.endswith("/opt+freq"):
        return "orca_optfreq_"
    if "orca_database" in normalized_path and normalized_path.endswith("/resppolymer"):
        return "orca_resppolymer_"
    raise ValueError(f"Unable to infer storage prefix from database directory: {database_directory}")


def build_stable_storage_name(smiles: str, database_directory: str) -> str:
    prefix = _storage_prefix_for_database(database_directory)
    digest = hashlib.sha256(smiles.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}{digest}"


def copy_files_based_on_smiles(
    database_directory: str,
    database_excel_path: str,
    found_molecule_dict: Dict[str, str],
    destination_directory: str,
) -> None:
    destination = Path(destination_directory)
    if not destination.exists():
        raise FileNotFoundError(f"{destination_directory} does not exist")

    database_mapping = read_database_excel_to_dict(database_excel_path)
    for smiles, name in found_molecule_dict.items():
        canonical_smiles = canonicalize_smiles(smiles)
        if canonical_smiles is None:
            print(f"非法 SMILES {smiles}，跳过数据库复制。")
            continue
        storage_name = database_mapping.get(canonical_smiles)
        if not storage_name:
            print(f"数据库中未找到唯一可复用记录：{canonical_smiles}")
            continue

        source_files = _iter_stem_files(database_directory, storage_name)
        if not source_files:
            print(f"数据库稳定名 {storage_name} 对应文件不存在，跳过复制。")
            continue

        target_stem = sanitize_working_name(name)
        for source_path in source_files:
            target_path = destination / f"{target_stem}{source_path.suffix}"
            shutil.copy2(source_path, target_path)
            print(f"文件 {target_path.name} （即数据库中的 {source_path.name} ）已被复制到路径：{destination_directory}")


def add_and_normalize_smiles(
    not_found_molecule_dict: Dict[str, str],
    source_directory: str,
    database_directory: str,
    database_excel_path: str,
) -> None:
    ensure_database_excel(database_directory)
    database_dir = Path(database_directory)
    df_database = _load_database_dataframe(database_excel_path)
    existing_mapping = read_database_excel_to_dict(database_excel_path)

    new_rows: List[Dict[str, str]] = []
    for smiles, file_name in not_found_molecule_dict.items():
        canonical_smiles = canonicalize_smiles(smiles)
        if canonical_smiles is None:
            print(f"SMILES {smiles} 非法，跳过入库。")
            continue

        if canonical_smiles in existing_mapping:
            print(f"SMILES: {canonical_smiles} 已存在于数据库中，跳过重复入库。")
            continue

        storage_name = build_stable_storage_name(canonical_smiles, database_directory)
        working_stem = sanitize_working_name(file_name)
        source_files = _iter_stem_files(source_directory, working_stem)
        if not source_files:
            print(f"文件 {working_stem} 对应结果不存在，无法写入数据库。")
            continue

        copied_any = False
        for source_path in source_files:
            destination_path = database_dir / f"{storage_name}{source_path.suffix}"
            shutil.copy2(source_path, destination_path)
            print(f"文件 {source_path.name} 已入库为 {destination_path.name}")
            copied_any = True

        if copied_any:
            new_rows.append({"FileName": storage_name, "SMILES": canonical_smiles})
            existing_mapping[canonical_smiles] = storage_name

    if not new_rows:
        return

    updated_df = pd.concat([df_database, pd.DataFrame(new_rows)], ignore_index=True)
    updated_df["SMILES"] = updated_df["SMILES"].apply(canonicalize_smiles)
    updated_df["FileName"] = updated_df["FileName"].fillna("").astype(str).str.strip()
    updated_df = updated_df[
        (updated_df["FileName"] != "") & updated_df["SMILES"].notna()
    ].drop_duplicates(subset=DATABASE_COLUMNS, keep="first")
    updated_df.to_excel(database_excel_path, index=False)
