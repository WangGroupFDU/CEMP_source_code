import torch
from rdkit import Chem
import os
import pandas as pd
from torch_geometric.data import Data
import numpy as np
from torch_geometric.data import DataLoader
from sklearn.model_selection import train_test_split
from openbabel import openbabel, pybel


def add_hydrogens_to_smiles(smiles):
    mol = Chem.MolFromSmiles(smiles)  
    mol = Chem.AddHs(mol)  
    smiles_with_h = Chem.MolToSmiles(mol)  
    return smiles_with_h

def get_node_features(smiles):
    
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)  
    
    atoms = mol.GetAtoms()
    
    features = []
    for atom in atoms:
        
        atomic_number = atom.GetAtomicNum()
        
        chiral_tag = int(atom.GetChiralTag())
        
        hybridization = int(atom.GetHybridization())
        
        is_aromatic = int(atom.GetIsAromatic())
        
        is_in_ring = int(atom.IsInRing())
        
        features.append([atomic_number, chiral_tag, hybridization, is_aromatic, is_in_ring])
    
    node_features = torch.tensor(features, dtype=torch.long)
    return node_features

def get_edge_index(smiles):
    
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)  
    
    edge_index = []
    
    for bond in mol.GetBonds():
        
        start_atom = bond.GetBeginAtomIdx()
        end_atom = bond.GetEndAtomIdx()
        
        edge_index.append([start_atom, end_atom])
        edge_index.append([end_atom, start_atom])
    
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    return edge_index


import torch  
from rdkit import Chem  
from rdkit.Chem import AllChem  

def smiles_to_morgan_fingerprint(smiles, radius=2, n_bits=2048):
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"无效的SMILES字符串: {smiles}")
    
    
    fingerprint = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    
    
    array = list(fingerprint.ToBitString())  
    array = [int(bit) for bit in array]  
    
    
    tensor = torch.tensor(array, dtype=torch.float32).unsqueeze(0)  
    
    
    
    
    return tensor

def cap_smiles(smiles):
    
    if not isinstance(smiles, str) or pd.isnull(smiles) or smiles.strip() == "":
        return np.nan

    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return np.nan

    
    rw_mol = Chem.RWMol(mol)
    modified = False  

    
    for atom in rw_mol.GetAtoms():
        if atom.GetAtomicNum() == 0:  
            
            atom.SetAtomicNum(1)
            modified = True

    
    if not modified:
        return smiles

    
    new_mol = rw_mol.GetMol()
    try:
        
        Chem.SanitizeMol(new_mol)
    except Exception as e:
        return np.nan

    
    new_smiles = Chem.MolToSmiles(new_mol, canonical=True, isomericSmiles=True)
    
    
    if Chem.MolFromSmiles(new_smiles) is None:
        return np.nan
    
    return new_smiles


def create_total_train_val_test_dataset(data_list):
    
    val_ratio=0.1
    test_ratio=0.1
    train_val_list, test_list = train_test_split(data_list, test_size=test_ratio, random_state=42)
    train_list, val_list = train_test_split(train_val_list, test_size=val_ratio / (1 - test_ratio), random_state=42)
    print(len(data_list))
    print(len(train_list))
    print(len(val_list))
    print(len(test_list))
    return data_list, train_list, val_list, test_list

def save_data_list(data_list, file_path):
    torch.save(data_list, file_path)



def generate_lowest_energy_conformer_openbabel(smiles: str, 
                                               opt: bool = True, 
                                               num_confs: int = 50, 
                                               forcefield: str = "UFF"):
    
    obConversion = openbabel.OBConversion()
    obConversion.SetInFormat("smi")
    
    
    obmol = openbabel.OBMol()
    obConversion.ReadString(obmol, smiles)
    obmol.AddHydrogens()
    
    
    builder = openbabel.OBBuilder()
    builder.Build(obmol)
    
    
    cs = openbabel.OBConformerSearch()
    cs.Setup(obmol, num_confs, True)
    cs.Search()
    cs.GetConformers(obmol)
    
    
    ff_name = forcefield.upper()
    if ff_name == "MMFF94":
        ff = openbabel.OBForceField.FindForceField("mmff94")
    elif ff_name == "UFF":
        ff = openbabel.OBForceField.FindForceField("uff")
    else:
        raise ValueError("不支持的力场类型，请选择 'MMFF94' 或 'UFF'")
    
    nconfs = obmol.NumConformers()
    
    if opt:
        
        lowest_energy = float('inf')
        lowest_conf_index = None
        for i in range(nconfs):
            obmol.SetConformer(i)
            if not ff.Setup(obmol):
                print(f"构象 {i} 力场设置失败，跳过")
                continue
            ff.ConjugateGradients(250, 1.0e-4)
            ff.GetCoordinates(obmol)
            energy = ff.Energy()
            if energy < lowest_energy:
                lowest_energy = energy
                lowest_conf_index = i
        
        
        if lowest_conf_index is None:
            return None, None, None

    else:
        
        lowest_conf_index = 0
        lowest_energy = None
    
    
    atomic_number_to_symbol = {
        1: "H",    2: "He",   3: "Li",   4: "Be",   5: "B",    6: "C",    7: "N",    8: "O",    9: "F",    10: "Ne",
        11: "Na",  12: "Mg",  13: "Al",  14: "Si",  15: "P",   16: "S",   17: "Cl",  18: "Ar",  19: "K",   20: "Ca",
        21: "Sc",  22: "Ti",  23: "V",   24: "Cr",  25: "Mn",  26: "Fe",  27: "Co",  28: "Ni",  29: "Cu",  30: "Zn",
        31: "Ga",  32: "Ge",  33: "As",  34: "Se",  35: "Br",  36: "Kr",  37: "Rb",  38: "Sr",  39: "Y",   40: "Zr",
        41: "Nb",  42: "Mo",  43: "Tc",  44: "Ru",  45: "Rh",  46: "Pd",  47: "Ag",  48: "Cd",  49: "In",  50: "Sn",
        51: "Sb",  52: "Te",  53: "I",   54: "Xe",  55: "Cs",  56: "Ba",  57: "La",  58: "Ce",  59: "Pr",  60: "Nd",
        61: "Pm",  62: "Sm",  63: "Eu",  64: "Gd",  65: "Tb",  66: "Dy",  67: "Ho",  68: "Er",  69: "Tm",  70: "Yb",
        71: "Lu",  72: "Hf",  73: "Ta",  74: "W",   75: "Re",  76: "Os",  77: "Ir",  78: "Pt",  79: "Au",  80: "Hg",
        81: "Tl",  82: "Pb",  83: "Bi",  84: "Po",  85: "At",  86: "Rn",  87: "Fr",  88: "Ra",  89: "Ac",  90: "Th",
        91: "Pa",  92: "U",   93: "Np",  94: "Pu",  95: "Am",  96: "Cm",  97: "Bk",  98: "Cf",  99: "Es", 100: "Fm",
        101: "Md", 102: "No", 103: "Lr", 104: "Rf", 105: "Db", 106: "Sg", 107: "Bh", 108: "Hs", 109: "Mt", 110: "Ds",
        111: "Rg", 112: "Cn", 113: "Nh", 114: "Fl", 115: "Mc", 116: "Lv", 117: "Ts", 118: "Og"
    }
    
    
    obmol.SetConformer(lowest_conf_index)
    coordinates = []
    
    for atom in pybel.ob.OBMolAtomIter(obmol):
        atomic_num = atom.GetAtomicNum()
        symbol = atomic_number_to_symbol.get(atomic_num, str(atomic_num))  
        x = atom.GetX()
        y = atom.GetY()
        z = atom.GetZ()
        coordinates.append((symbol, x, y, z))
    
    return lowest_conf_index, lowest_energy, coordinates
