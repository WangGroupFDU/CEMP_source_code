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


def get_gaussian_optfreq_database_paths(settings_result: Dict[str, object]) -> Tuple[str, str]:
    root = _normalize_database_root(settings_result, "gaussian_database_path", "Gaussian_database")
    optfreq = root / "opt+freq"
    optfreq.mkdir(parents=True, exist_ok=True)
    excel_path = ensure_database_excel(str(optfreq))
    return str(optfreq), excel_path


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
        unique_df.groupby("FileName")["SMILES"].nunique().loc[lambda series: series > 1].index
    )
    ambiguous_smiles = set(
        unique_df.groupby("SMILES")["FileName"].nunique().loc[lambda series: series > 1].index
    )
    clean_df = unique_df[
        ~unique_df["FileName"].isin(ambiguous_filenames)
        & ~unique_df["SMILES"].isin(ambiguous_smiles)
    ].copy()
    return clean_df


def load_clean_database_mapping(database_excel_path: str) -> Dict[str, str]:
    df = _load_database_dataframe(database_excel_path)
    clean_df = _filter_clean_database_rows(df)
    return dict(zip(clean_df["SMILES"], clean_df["FileName"]))


def collect_small_molecule_rows(df: pd.DataFrame) -> List[Dict[str, str]]:
    required_columns = {"Name", "SMILES", "is polymer"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise KeyError(f"System.xlsx is missing required columns: {sorted(missing_columns)}")

    records: List[Dict[str, str]] = []
    for _, row in df[df["is polymer"] == False].iterrows():
        records.append(
            {
                "Name": str(row["Name"]),
                "SMILES": "" if pd.isna(row["SMILES"]) else str(row["SMILES"]),
            }
        )
    return records


def _iter_stem_files(directory: str, stem: str) -> List[Path]:
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    matched_files = [
        path for path in dir_path.iterdir()
        if path.is_file() and path.name != "molecule.xlsx" and path.stem == stem
    ]
    return sorted(matched_files, key=lambda path: path.name)


def build_stable_storage_name(smiles: str) -> str:
    digest = hashlib.sha256(smiles.encode("utf-8")).hexdigest()[:12]
    return f"g16_optfreq_{digest}"


def copy_reusable_results_to_success(
    rows: List[Dict[str, str]],
    database_directory: str,
    database_excel_path: str,
    destination_directory: str,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    destination = Path(destination_directory)
    if not destination.exists():
        raise FileNotFoundError(f"{destination_directory} does not exist")

    database_mapping = load_clean_database_mapping(database_excel_path)
    missing_rows: List[Dict[str, str]] = []
    found_rows: List[Dict[str, str]] = []

    for row in rows:
        name = row["Name"]
        smiles = row["SMILES"]
        canonical_smiles = canonicalize_smiles(smiles)
        if canonical_smiles is None:
            print(f"Name={name} 的 SMILES 非法，跳过数据库命中并进入新计算。")
            missing_rows.append(row)
            continue

        storage_name = database_mapping.get(canonical_smiles)
        if not storage_name:
            missing_rows.append(row)
            continue

        source_files = _iter_stem_files(database_directory, storage_name)
        if not source_files:
            print(f"数据库中 stable_name={storage_name} 的物理文件缺失，Name={name} 将进入新计算。")
            missing_rows.append(row)
            continue

        target_stem = sanitize_working_name(name)
        for source_path in source_files:
            target_path = destination / f"{target_stem}{source_path.suffix}"
            shutil.copy2(source_path, target_path)
            print(f"数据库文件 {source_path.name} 已复制为本地文件 {target_path.name}")
        found_rows.append(row)

    return missing_rows, found_rows


def collect_missing_rows(
    rows: List[Dict[str, str]],
    database_excel_path: str,
) -> List[Dict[str, str]]:
    database_mapping = load_clean_database_mapping(database_excel_path)
    missing_rows: List[Dict[str, str]] = []
    for row in rows:
        canonical_smiles = canonicalize_smiles(row["SMILES"])
        if canonical_smiles is None or canonical_smiles not in database_mapping:
            missing_rows.append(row)
    return missing_rows


def store_success_results_to_database(
    rows: List[Dict[str, str]],
    source_directory: str,
    database_directory: str,
    database_excel_path: str,
) -> None:
    ensure_database_excel(database_directory)
    database_dir = Path(database_directory)
    df_database = _load_database_dataframe(database_excel_path)
    existing_mapping = load_clean_database_mapping(database_excel_path)
    new_rows: List[Dict[str, str]] = []

    for row in rows:
        name = row["Name"]
        smiles = row["SMILES"]
        canonical_smiles = canonicalize_smiles(smiles)
        if canonical_smiles is None:
            print(f"Name={name} 的 SMILES 非法，跳过入库。")
            continue

        if canonical_smiles in existing_mapping:
            print(f"SMILES={canonical_smiles} 已存在于共享数据库中，跳过重复入库。")
            continue

        storage_name = build_stable_storage_name(canonical_smiles)
        working_stem = sanitize_working_name(name)
        source_files = _iter_stem_files(source_directory, working_stem)
        if not source_files:
            print(f"Name={name} 对应的成功结果文件不存在，无法入库。")
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
