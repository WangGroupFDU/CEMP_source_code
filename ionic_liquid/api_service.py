import torch
import torch.nn as nn
import torch.nn.functional as F
import joblib
from rdkit import Chem
from rdkit.Chem import AllChem  
import os
from torch_geometric.data import Data, DataLoader
import pandas as pd
import numpy as np

class MLP(nn.Module):
    def __init__(self, input_size, hidden_sizes, output_size, dropout_rate=0.3):
        super(MLP, self).__init__()
        layers = []
        in_dim = input_size  
        
        
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(in_dim, hidden_size))            
            layers.append(nn.BatchNorm1d(hidden_size))                 
            layers.append(nn.ReLU())                                   
            layers.append(nn.Dropout(dropout_rate))                    
            in_dim = hidden_size                                      
        
        
        layers.append(nn.Linear(in_dim, output_size))
        
        
        self.network = nn.Sequential(*layers)

    def forward(self, data):
        x = data.morgan_fp  
        out = self.network(x)  
        return out


def add_hydrogens_to_smiles(smiles):
    mol = Chem.MolFromSmiles(smiles)  
    mol = Chem.AddHs(mol)  
    smiles_with_h = Chem.MolToSmiles(mol)  
    return smiles_with_h

def smiles_to_morgan_fingerprint(smiles, radius=2, n_bits=2048):
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"无效的SMILES字符串: {smiles}")
    
    
    fingerprint = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    
    
    array = list(fingerprint.ToBitString())  
    array = [int(bit) for bit in array]  
    
    
    tensor = torch.tensor(array, dtype=torch.float32).unsqueeze(0)  
    
    return tensor

def create_morgan_fp_tensor(smiles):
    smiles = add_hydrogens_to_smiles(smiles) 
    
    
    morgan_fp_tensor = smiles_to_morgan_fingerprint(smiles, radius=2, n_bits=2048)
        
    return morgan_fp_tensor

