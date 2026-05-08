import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from polymer.models import experiment_polymer_data


SCHEMA = [
    "Name", "PSMILES",
    "Atomization_Energy_eV",
    "Bandgap_eV", "Bandgap_Bulk_eV", "Bandgap_Chain_eV",
    "CH4_Permeability_Barrer", "CO2_Permeability_Barrer", "Compressive_Strength_MPa",
    "Crystallization_Temperature_K", "Crystallization_Tendency_percentage",
    "Dielectric_Constant_Electronic", "Dielectric_Constant_Ionic", "Dielectric_Constant_Total",
    "Density", "Electron_Affinity_eV", "Elongation_at_Break_percentage", "Flexural_Strength_MPa",
    "Tg_K", "H2_Permeability_Barrer", "Hardness_MPa", "He_Permeability_Barrer",
    "Impact_Strength_kJ_per_m2", "Ion_Exchange_Capacity_meq_per_g", "Ionization_Energy_eV",
    "Limiting_Oxygen_Index_percentage", "Lower_Critical_Solution_Temperature_K",
    "Tm_K", "Methanol_Permeability_cm2_per_s", "N2_Permeability_Barrer",
    "O2_Permeability_Barrer", "Refractive_Index", "Swelling_Degree_percentage",
    "Thermal_Conductivity_W_per_mK", "Tensile_Strength_MPa", "Td_K",
    "Upper_Critical_Solution_Temperature_K", "Water_Contact_Angle",
    "Water_Uptake_percentage", "Youngs_Modulus_MPa", "Reference",
]
NUMERIC_COLS = [c for c in SCHEMA if c not in ("Name", "PSMILES", "Reference")]


ALIASES = {
    "name": "Name", "smiles": "PSMILES", "psmiles": "PSMILES",
    "reference": "Reference", "source": "Reference",

    "bandgap (eV)".lower(): "Bandgap_eV",
    "band gap (eV)".lower(): "Bandgap_eV",
    "band gap bulk (eV)".lower(): "Bandgap_Bulk_eV",
    "band gap chain (eV)".lower(): "Bandgap_Chain_eV",
    "atomization energy (eV)".lower(): "Atomization_Energy_eV",
    "electron affinity (eV)".lower(): "Electron_Affinity_eV",
    "ionization energy (eV)".lower(): "Ionization_Energy_eV",

    "refractive index".lower(): "Refractive_Index",
    "density (g/cm3)".lower(): "Density",

    "co2 permeability (barrer)": "CO2_Permeability_Barrer",
    "h2 permeability (barrer)": "H2_Permeability_Barrer",
    "o2 permeability (barrer)": "O2_Permeability_Barrer",
    "n2 permeability (barrer)": "N2_Permeability_Barrer",
    "he permeability (barrer)": "He_Permeability_Barrer",
    "ch4 permeability (barrer)": "CH4_Permeability_Barrer",

    "crystallization temperature (k)".lower(): "Crystallization_Temperature_K",
    "crystallization tendency (%)".lower(): "Crystallization_Tendency_percentage",
    "tg (k)".lower(): "Tg_K", "tm (k)".lower(): "Tm_K", "td (k)".lower(): "Td_K",
    "upper critical solution temperature (k)".lower(): "Upper_Critical_Solution_Temperature_K",
    "lower critical solution temperature (k)".lower(): "Lower_Critical_Solution_Temperature_K",

    "compressive strength (mpa)".lower(): "Compressive_Strength_MPa",
    "flexural strength (mpa)".lower(): "Flexural_Strength_MPa",
    "tensile strength (mpa)".lower(): "Tensile_Strength_MPa",
    "youngs modulus (mpa)".lower(): "Youngs_Modulus_MPa",
    "hardness (mpa)".lower(): "Hardness_MPa",
    "impact strength (kj/m2)".lower(): "Impact_Strength_kJ_per_m2",

    "dielectric constant electronic".lower(): "Dielectric_Constant_Electronic",
    "dielectric constant ionic".lower(): "Dielectric_Constant_Ionic",
    "dielectric constant total".lower(): "Dielectric_Constant_Total",

    "methanol permeability (cm2/s)".lower(): "Methanol_Permeability_cm2_per_s",
    "swelling degree (%)".lower(): "Swelling_Degree_percentage",
    "water uptake (%)".lower(): "Water_Uptake_percentage",
    "water contact angle".lower(): "Water_Contact_Angle",
    "thermal conductivity (w/m k)".lower(): "Thermal_Conductivity_W_per_mK",
    "limiting oxygen index (%)".lower(): "Limiting_Oxygen_Index_percentage",
    "ion exchange capacity (meq/g)".lower(): "Ion_Exchange_Capacity_meq_per_g",
}

NULL_STRINGS = {"", "na", "n/a", "null", "none", "-", "—", "--"}

def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for c in df.columns:
        key = str(c).strip()
        lk = key.lower()
        rename[c] = ALIASES.get(lk, key)
    df = df.rename(columns=rename)
    
    for col in SCHEMA:
        if col not in df.columns:
            df[col] = pd.NA
    return df

def to_float(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    if s.lower() in NULL_STRINGS:
        return None
    try:
        return float(s)
    except Exception:
        return None

def norm_psmiles(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    t = str(s).strip()
    if not t:
        return None
    
    t = " ".join(t.split())
    return t

class Command(BaseCommand):
    help = "把 cleaned_homo_polymer_dataset.csv 和 2_Tg.csv 非破坏性导入到现有数据库（不删除已有行）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--homopolymer-csv", dest="homo", default="polymer/cleaned_homo_polymer_dataset.csv", type=str,
            help="Homopolymer 数据 CSV 的文件路径"
        )
        parser.add_argument(
            "--tg-csv", dest="tg", default="polymer/2_Tg.csv", type=str,
            help="Tg 数据 CSV 的文件路径"
        )
        parser.add_argument("--overwrite", action="store_true",
                            help="覆盖已有非空字段（默认只补空）")
        parser.add_argument("--batch", type=int, default=500,
                            help="bulk_update 批大小，默认 500")

    @transaction.atomic
    def handle(self, *args, **opt):
        paths = [p for p in (opt["homo"], opt["tg"]) if Path(p).exists()]
        if not paths:
            self.stderr.write("未找到输入 CSV（请检查 --homo / --tg 路径）")
            return

        frames = []
        for p in paths:
            df = pd.read_csv(p)
            df = normalize_cols(df)
            df["Name"] = df["Name"].astype(str).str.strip().where(df["Name"].notna(), None)
            df["PSMILES"] = df["PSMILES"].apply(norm_psmiles)
            for c in NUMERIC_COLS:
                df[c] = df[c].apply(to_float)
            frames.append(df[SCHEMA])

        data = pd.concat(frames, ignore_index=True)

        
        existing = {}
        qs = experiment_polymer_data.objects.all().only("id", "Name", "PSMILES")
        for obj in qs:
            existing[(obj.PSMILES or "", obj.Name or "")] = obj

        created = updated = skipped = 0
        to_update = []

        for _, r in data.iterrows():
            name = (r["Name"] if pd.notna(r["Name"]) else None) or "Unknown"
            psmiles = norm_psmiles(r["PSMILES"])
            if not psmiles:
                print(f"跳过记录 - 原始PSMILES: '{r['PSMILES']}' (类型: {type(r['PSMILES'])}), Name: '{name}'")
                skipped += 1
                continue

            key = (psmiles, name)
            obj = existing.get(key)

            if obj is None:
                
                obj = experiment_polymer_data(Name=name, PSMILES=psmiles)
                for col in SCHEMA:
                    if col in ("Name", "PSMILES"): 
                        continue
                    v = r[col]
                    if pd.notna(v):
                        setattr(obj, col, v)
                obj.save()
                existing[key] = obj
                created += 1
                continue

            
            changed = False
            for col in SCHEMA:
                if col in ("Name", "PSMILES"):
                    continue
                newv = r[col]
                if pd.isna(newv):
                    continue
                oldv = getattr(obj, col, None)
                if opt["overwrite"]:
                    if oldv != newv:
                        setattr(obj, col, newv); changed = True
                else:
                    if oldv is None:
                        setattr(obj, col, newv); changed = True

            if changed:
                to_update.append(obj)
                if len(to_update) >= opt["batch"]:
                    experiment_polymer_data.objects.bulk_update(
                        to_update, [c for c in SCHEMA if c not in ("Name", "PSMILES")]
                    )
                    to_update.clear()
                updated += 1
            else:
                skipped += 1

        if to_update:
            experiment_polymer_data.objects.bulk_update(
                to_update, [c for c in SCHEMA if c not in ("Name", "PSMILES")]
            )

        self.stdout.write(self.style.SUCCESS(
            f"完成：新增 {created} 条，更新 {updated} 条，跳过 {skipped} 条。"
        ))
