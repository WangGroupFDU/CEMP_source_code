from rdkit import Chem as Chem
from rdkit.Chem import Draw
from rdkit.Chem.Descriptors3D import Asphericity, Eccentricity,InertialShapeFactor,NPR1,NPR2,PMI1,PMI2,PMI3,RadiusOfGyration,SpherocityIndex
from rdkit.Chem import AllChem, rdDistGeom
from rdkit.Chem.Draw import rdMolDraw2D, MolToFile, MolToImage
import pandas as pd
from pandas import DataFrame
import numpy as np
from rdkit.ML.Descriptors.MoleculeDescriptors import MolecularDescriptorCalculator
import cairosvg
import io
import traceback


def drawSMILEs(smiles, width=600, height=600):
    
    m = Chem.MolFromSmiles(smiles)
    return_path = "images/error.png"
    full_path = "./home/static/smiles_figures/" + smiles + ".png"
    try:
        MolToFile(m, full_path, size = (width,height))
        return_path = "smiles_figures/" + smiles + ".png"
    except Exception:
        print(traceback.format_exc())
    return return_path



def cal3Ddescriptor(sml):
    try:
        m = Chem.MolFromSmiles(sml)
        AllChem.EmbedMolecule(m, useRandomCoords=True,maxAttempts=5000)
        AllChem.UFFOptimizeMolecule(m)
        m2=Chem.AddHs(m)
        AllChem.EmbedMolecule(m2, AllChem.ETKDG())
        
        Descriptors_3d = []
        Descriptors_3d.append(Asphericity(m2))
        Descriptors_3d.append(Eccentricity(m2))
        Descriptors_3d.append(InertialShapeFactor(m2))
        Descriptors_3d.append(NPR1(m2))
        Descriptors_3d.append(NPR2(m2))
        Descriptors_3d.append(PMI1(m2))
        Descriptors_3d.append(PMI2(m2))
        Descriptors_3d.append(PMI3(m2))
        Descriptors_3d.append(RadiusOfGyration(m2))
        Descriptors_3d.append(SpherocityIndex(m2))
    except:
        print("Failure to embed molecule!")
        Descriptors_3d = []*10
    return Descriptors_3d


def calMoldescriptor(sml):
    try:
        m = Chem.MolFromSmiles(sml)
        AllChem.EmbedMolecule(m, useRandomCoords=True,maxAttempts=5000)
        AllChem.UFFOptimizeMolecule(m)
        m2=Chem.AddHs(m)
        AllChem.EmbedMolecule(m2, AllChem.ETKDG())
        
        Descriptors_mol = MolecularDescriptorCalculator(["ExactMolWt", "FpDensityMorgan1", "FpDensityMorgan2",
                                                         "HeavyAtomMolWt", "MaxAbsPartialCharge","MaxPartialCharge",
                                                         "MinPartialCharge", "NumRadicalElectrons",
                                                         "NumValenceElectrons"]).CalcDescriptors(m2)
        Descriptors_mol_list = list(Descriptors_mol)
        Descriptors_mol_list.append(AllChem.ComputeMolVolume(m2))
    except:
        Descriptors_mol_list = []*10
    return Descriptors_mol_list

import psi4
from psikit import Psikit

def psi4Calculation(smiles, basis_sets="b3lyp/6-31pg**", method = "single-point"):
    pk = Psikit()
    pk.read_from_smiles(smiles)
    if method == "single-point":
        energy = pk.energy(basis_sets=basis_sets)
    else:
        energy = pk.optimize(basis_sets=basis_sets)
    HOMO = pk.HOMO
    LUMO = pk.LUMO
    Dipole_x = pk.dipolemoment[0]
    Dipole_y = pk.dipolemoment[1]
    Dipole_z = pk.dipolemoment[2]
    Dipole_Total = pk.dipolemoment[3]
    return [method, basis_sets, energy, HOMO, LUMO, Dipole_x, Dipole_y,Dipole_z, Dipole_Total]


import pandas as pd
from pandas import DataFrame
from bs4 import BeautifulSoup, SoupStrainer
import urllib.request
import numpy as np
import os
import itertools
pd.options.mode.chained_assignment = None
from rdkit.Chem.Descriptors3D import Asphericity,Eccentricity,InertialShapeFactor,NPR1,NPR2,PMI1,PMI2,PMI3,RadiusOfGyration,SpherocityIndex
from rdkit.Chem import AllChem, rdDistGeom
from rdkit.ML.Descriptors.MoleculeDescriptors import MolecularDescriptorCalculator
from psikit import Psikit
from bs4 import BeautifulSoup, SoupStrainer
import urllib.request
pd.options.mode.chained_assignment = None
from sklearn.ensemble import VotingClassifier,RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor, GradientBoostingClassifier
import glob
from sklearn.ensemble import VotingRegressor
from pandas.plotting import scatter_matrix
from sklearn.model_selection import cross_val_score, GridSearchCV, cross_val_predict, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR, SVC
from sklearn.model_selection import RandomizedSearchCV
from xgboost import XGBClassifier,XGBRegressor
import itertools
from pandas import DataFrame, Series
from scipy.cluster.hierarchy import dendrogram
from sklearn.cluster import AgglomerativeClustering
from sklearn import preprocessing

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score

from rdkit import Chem
from rdkit.Chem.rdmolops import GetAdjacencyMatrix
from ILP import ILP

def modelPrediction(cation_smile, anion_smile):
    m = ILP()
    
    
    
    
    
    
    
    
    
    state, type = m.modelPrediction(cation_smile, anion_smile)
    return state, type
    return state, type


def modelPredictionTest():
    m = ILP()
    
    
    
    
    
    
    
    m.machineLearning("conductivity_reg")
    m.screenIL()
    m.combineILthermo()
    
    print("Done!")

    return







import os
import json
import gzip
from typing import Dict, List, Optional, Sequence, Any
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import DataStructs
import re
import math

def load_morgan_fp_data_list(path: str) -> List[Dict[str, str]]:
    """Load Morgan fingerprint data from compressed JSON file."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        payload = json.load(f)
    print(path)
    print(type(payload))
    return list(payload.get("data_list", []))


def topk_similar_smiles(
    query_smiles: str,
    data_list: List[Dict[str, str]],
    topk: int = 10,
    method: str = "tanimoto",
    radius: int = 2,
    n_bits: Optional[int] = None,
    tversky_alpha: float = 0.5,
    tversky_beta: float = 0.5,
    property_col_list: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Query similar molecules by SMILES using Morgan fingerprint similarity.

    Args:
        query_smiles: Query SMILES string
        data_list: List of molecule data dictionaries
        topk: Number of top results to return
        method: Similarity method - "tanimoto", "dice", "cosine", or "tversky"
        radius: Morgan fingerprint radius
        n_bits: Fingerprint bit length (auto-inferred if None)
        tversky_alpha: Tversky alpha parameter
        tversky_beta: Tversky beta parameter
        property_col_list: List of property column names to return

    Returns:
        List of dicts with SMILES, similarity, Name, CAS, and properties
    """
    
    if query_smiles is None:
        raise ValueError("Input SMILES is None")
    smi_q = str(query_smiles).strip()
    if smi_q == "":
        raise ValueError("Input SMILES is empty string")

    
    mol_q = Chem.MolFromSmiles(smi_q)
    if mol_q is None:
        raise ValueError("Input SMILES cannot be parsed by RDKit")

    
    if n_bits is None:
        inferred = None
        for item in data_list:
            bitstr = str(item.get("morgan_fp", "") or "")
            if bitstr != "":
                inferred = len(bitstr)
                break
        n_bits = inferred if inferred is not None else 2048

    
    if property_col_list is None:
        property_col_list = []
    else:
        property_col_list = [str(c).strip() for c in property_col_list if str(c).strip() != ""]
        _seen = set()
        property_col_list = [c for c in property_col_list if (c not in _seen and not _seen.add(c))]

    
    def _to_str_or_empty(v: Any) -> str:
        if v is None:
            return ""
        s = str(v).strip()
        if s.lower() in {"", "nan", "none", "na"}:
            return ""
        return s

    
    qfp = AllChem.GetMorganFingerprintAsBitVect(mol_q, radius=radius, nBits=int(n_bits))

    
    candidates = []
    for item in data_list:
        smi = str(item.get("SMILES", "") or "").strip()
        nm = str(item.get("Name", "") or "").strip()
        cas = str(item.get("CAS", "") or "").strip()
        bitstr = str(item.get("morgan_fp", "") or "")
        if smi == "" or bitstr == "":
            continue
        try:
            fp = DataStructs.CreateFromBitString(bitstr)
        except Exception:
            from rdkit.DataStructs.cDataStructs import ExplicitBitVect
            fp = ExplicitBitVect(len(bitstr))
            for i, ch in enumerate(bitstr):
                if ch == '1':
                    fp.SetBit(i)
        candidates.append((smi, nm, cas, fp, item))

    if not candidates:
        return []

    
    method_norm = method.lower().strip()
    fps = [c[3] for c in candidates]
    if method_norm == "tanimoto":
        scores = DataStructs.BulkTanimotoSimilarity(qfp, fps)
    elif method_norm == "dice":
        scores = [DataStructs.DiceSimilarity(qfp, fp) for fp in fps]
    elif method_norm == "cosine":
        scores = [DataStructs.CosineSimilarity(qfp, fp) for fp in fps]
    elif method_norm == "tversky":
        scores = [DataStructs.TverskySimilarity(qfp, fp, tversky_alpha, tversky_beta) for fp in fps]
    else:
        raise ValueError(f"Unsupported similarity method: {method}")

    
    paired = list(zip(candidates, scores))
    paired.sort(key=lambda x: x[1], reverse=True)
    topk = max(0, min(int(topk), len(paired)))

    results: List[Dict[str, Any]] = []
    for (smi, nm, cas, _fp, _item), sc in paired[:topk]:
        
        props: Dict[str, str] = {}
        _nested = _item.get("properties", {}) if isinstance(_item.get("properties"), dict) else {}

        for col in property_col_list:
            if col in _nested:
                val = _nested.get(col, "")
            else:
                val = _item.get(col, "")
            props[col] = _to_str_or_empty(val)

        results.append({
            "SMILES": smi,
            "similarity": f"{sc * 100:.2f}%",
            "Name": nm or "",
            "CAS": cas or "",
            "properties": props
        })

    return results


def filter_il_by_property_ranges(
    ecw_range: Optional[Sequence[Optional[float]]] = None,
    conductivity_range: Optional[Sequence[Optional[float]]] = None,
    tm_range: Optional[Sequence[Optional[float]]] = None,
    source: str = "experiment",
    experiment_IL_data_list: Optional[List[Dict]] = None,
    generated_IL_data_list: Optional[List[Dict]] = None
) -> List[Dict[str, Any]]:
    """
    Filter ionic liquids by property ranges.

    Args:
        ecw_range: [min, max] or None for ECW (V)
        conductivity_range: [min, max] or None for Conductivity (mS/cm)
        tm_range: [min, max] or None for Melting point (K)
        source: "experiment" or "generated"
        experiment_IL_data_list: Experimental IL data (if not provided, uses global)
        generated_IL_data_list: Generated IL data (if not provided, uses global)

    Returns:
        List of dicts with Name, SMILES, CAS, and filtered properties
    """
    
    ECW_COL = "ECW (V)"
    TM_COL = "Tm (K)"
    COND_COL = "Conductivity (mS/cm)"

    
    def _norm_range(r: Optional[Sequence[Optional[float]]]) -> tuple:
        if r is None:
            return (None, None)
        if not isinstance(r, (list, tuple)) or len(r) != 2:
            raise ValueError("Range must be (min, max) tuple or None")
        def _to_num(x):
            if x is None or (isinstance(x, str) and x.strip() == ""):
                return None
            return float(x)
        lo, hi = _to_num(r[0]), _to_num(r[1])
        if lo is not None and hi is not None and lo > hi:
            lo, hi = hi, lo
        return lo, hi

    ecw_lo, ecw_hi = _norm_range(ecw_range)
    cond_lo, cond_hi = _norm_range(conductivity_range)
    tm_lo, tm_hi = _norm_range(tm_range)

    
    src = str(source).strip().lower()
    if src not in {"experiment", "generated"}:
        raise ValueError("source must be 'experiment' or 'generated'")

    
    if experiment_IL_data_list is None or generated_IL_data_list is None:
        
        import sys
        frame = sys._getframe(1)
        if 'experiment_IL_data_list' in frame.f_globals:
            experiment_IL_data_list = frame.f_globals['experiment_IL_data_list']
        if 'generated_IL_data_list' in frame.f_globals:
            generated_IL_data_list = frame.f_globals['generated_IL_data_list']

    if src == "experiment":
        if experiment_IL_data_list is None:
            raise RuntimeError("experiment_IL_data_list not provided")
        data_list = experiment_IL_data_list
    else:
        if generated_IL_data_list is None:
            raise RuntimeError("generated_IL_data_list not provided")
        data_list = generated_IL_data_list

    
    num_pat = re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')
    def _to_float(v) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            if isinstance(v, float) and math.isnan(v):
                return None
            return float(v)
        s = str(v).strip().replace(",", "")
        if s == "" or s.lower() in {"nan", "none", "na", "-", "–", "—"}:
            return None
        m = num_pat.search(s)
        return float(m.group(0)) if m else None

    def _get_prop(item: Dict[str, Any], col: str) -> Optional[float]:
        props = item.get("properties")
        if isinstance(props, dict) and col in props:
            val = props.get(col)
        else:
            val = item.get(col)
        return _to_float(val)

    
    def _in_range(val: Optional[float], lo: Optional[float], hi: Optional[float]) -> bool:
        if lo is None and hi is None:
            return True
        if val is None:
            return False
        if lo is not None and val < lo:
            return False
        if hi is not None and val > hi:
            return False
        return True

    
    hits: List[Dict[str, Any]] = []
    for item in data_list:
        ecw_v = _get_prop(item, ECW_COL)
        cond_v = _get_prop(item, COND_COL)
        tm_v = _get_prop(item, TM_COL)

        if not _in_range(ecw_v, ecw_lo, ecw_hi):
            continue
        if not _in_range(cond_v, cond_lo, cond_hi):
            continue
        if not _in_range(tm_v, tm_lo, tm_hi):
            continue

        hits.append({
            "Name": item.get("Name", "") or "",
            "SMILES": item.get("SMILES", "") or "",
            "CAS": item.get("CAS", "") or "",
            "properties": {
                ECW_COL: ecw_v,
                COND_COL: cond_v,
                TM_COL: tm_v
            }
        })

    return hits
