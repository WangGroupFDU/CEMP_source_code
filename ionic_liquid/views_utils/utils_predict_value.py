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
from collections import Counter
import re
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import RobustScaler
from matplotlib.ticker import ScalarFormatter
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.preprocessing import LabelEncoder
from matplotlib.colors import ListedColormap
import seaborn as sns
import matplotlib.pyplot as plt
import seaborn as sns
from .MLPModel import MLP

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
input_size = 2048
hidden_sizes = [256, 64]
output_size = 1
model_conductivity_MLP = MLP(input_size=input_size, hidden_sizes=hidden_sizes, output_size=output_size).to(device)
MODEL_PATH = os.environ.get(
    "CEMP_IL_MODEL_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "model")),
)
_MODEL_CACHE = {}


def get_prediction_models():
    """
    功能目的：
        懒加载离子液体生成器所需的公开模型资产。
    输入参数：
        无，模型目录来自 CEMP_IL_MODEL_DIR 或 ionic_liquid/static/model。
    返回值：
        ECW 模型、Tm 模型和电导率 MLP 模型。
    关键流程：
        首次调用时检查文件存在并加载，后续从内存缓存返回。
    可能报错或边界情况：
        模型资产未下载或文件名不匹配时抛出 FileNotFoundError，提示用户下载 release 资产。
    """
    if _MODEL_CACHE:
        return _MODEL_CACHE["ecw"], _MODEL_CACHE["tm"], _MODEL_CACHE["conductivity"]

    required_files = {
        "ecw": os.path.join(MODEL_PATH, "IL_ECW_xgb_model.joblib"),
        "tm": os.path.join(MODEL_PATH, "Tm_xgb_model.joblib"),
        "conductivity": os.path.join(MODEL_PATH, "conductivity_MLP_model_fp.pt"),
    }
    missing_files = [path for path in required_files.values() if not os.path.exists(path)]
    if missing_files:
        raise FileNotFoundError(
            "Missing CEMP ionic-liquid model assets. Download the release model package "
            f"or set CEMP_IL_MODEL_DIR. Missing: {missing_files}"
        )

    ecw_model = joblib.load(required_files["ecw"])
    tm_model = joblib.load(required_files["tm"])
    state_dict = torch.load(required_files["conductivity"], map_location=device)
    model_conductivity_MLP.load_state_dict(state_dict)
    model_conductivity_MLP.eval()

    _MODEL_CACHE["ecw"] = ecw_model
    _MODEL_CACHE["tm"] = tm_model
    _MODEL_CACHE["conductivity"] = model_conductivity_MLP
    return ecw_model, tm_model, model_conductivity_MLP


def add_hydrogens_to_smiles(smiles):
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)
    smiles_with_h = Chem.MolToSmiles(mol)
    return smiles_with_h

def extract_features_targets(data_list, feature = "fp"):
    X = []

    for data in data_list:
        if feature == "2Ddescriptors":
            moldescriptor = data.moldescriptor.numpy().flatten()
            X.append(moldescriptor)

        elif feature == "fp":
            fp = data.morgan_fp.numpy().flatten()
            X.append(fp)

    X = np.array(X)
    return X

def smiles_to_morgan_fingerprint(smiles, radius=2, n_bits=2048):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"failed SMILES: {smiles}")

    fingerprint = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)

    array = list(fingerprint.ToBitString())
    array = [int(bit) for bit in array]

    tensor = torch.tensor(array, dtype=torch.float32).unsqueeze(0)

    return tensor

def create_molecule_data_quantum_chemistry_data(df):

    data_list = []

    idx_counter = 0

    for _, row in df.iterrows():
        name = row['Name']
        smiles = row['SMILES']
        smiles = add_hydrogens_to_smiles(smiles)

        morgan_fp_tensor = smiles_to_morgan_fingerprint(smiles, radius=2, n_bits=2048)

        tensors_to_check = [
            morgan_fp_tensor,
        ]

        if any(torch.isnan(t).any() or torch.isinf(t).any() for t in tensors_to_check):
            print(f"{name} contain NaN or Inf.")
            continue

        data = Data(
            idx=torch.tensor([idx_counter], dtype=torch.long),
            name=name,
            smiles=smiles,
            morgan_fp = morgan_fp_tensor,
        )

        data_list.append(data)
        idx_counter += 1

    return data_list

def add_predictions_to_df(df: pd.DataFrame,
                          y_ECW: np.ndarray,
                          y_Tm: np.ndarray,
                          y_conductivity: np.ndarray) -> pd.DataFrame:


    n_rows = len(df)
    if not (len(y_ECW) == n_rows and len(y_Tm) == n_rows and len(y_conductivity) == n_rows):
        raise ValueError("len(df) != len(y_ECW) or len(df) != len(y_Tm) or len(df) != len(y_conductivity)")

    df_updated = df.copy()

    df_updated["ECW (V)"] = y_ECW
    df_updated["Tm (K)"] = y_Tm
    df_updated["conductivity (mS/cm)"] = y_conductivity

    return df_updated

def predict_property(df, output_file_path):
    IL_ECW_xgb_model, Tm_xgb_model, conductivity_model = get_prediction_models()
    data_list = create_molecule_data_quantum_chemistry_data(df)
    X = extract_features_targets(data_list)

    y_ECW = IL_ECW_xgb_model.predict(X)
    y_Tm = Tm_xgb_model.predict(X)
    conductivity_model.eval()
    y_conductivity = []

    for data in data_list:
        data = data.to(device)
        data.morgan_fp = data.morgan_fp.float()
        out = conductivity_model(data)

        y_conductivity.append(out.detach().cpu().numpy())
    y_conductivity = np.concatenate(y_conductivity, axis=0)
    y_conductivity = y_conductivity.flatten()

    df_result = add_predictions_to_df(df, y_ECW, y_Tm, y_conductivity)
    df_result.to_csv(output_file_path, index=None)
