import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset



cut_off_voltage = {
    "ncm": [3.0, 4.25],
    "lnmo": [3.3, 4.75],
    "lfp": [2.5, 4.25]
}

class TransformerEncoderOnly(nn.Module):
    def __init__(self, input_dim, emb_dim, n_heads, n_layers):
        super(TransformerEncoderOnly, self).__init__()
        self.embedding = nn.Linear(input_dim, emb_dim)
        self.transformer_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(emb_dim, n_heads), 
            n_layers
        )
        self.linear = nn.Linear(emb_dim, 2)

    def forward(self, x):
        x = self.embedding(x)
        x = self.transformer_encoder(x)
        x = self.linear(x)
        return x

def normalize_voltage(row):
    if row["material"].lower() == "ncm":
        return (row["voltage"] - cut_off_voltage["ncm"][0]) / (cut_off_voltage["ncm"][1] - cut_off_voltage["ncm"][0])
    elif row["material"].lower() == "lfp":
        return (row["voltage"] - cut_off_voltage["lfp"][0]) / (cut_off_voltage["lfp"][1] - cut_off_voltage["lfp"][0])
    elif row["material"].lower() == "lnmo":
        return (row["voltage"] - cut_off_voltage["lnmo"][0]) / (cut_off_voltage["lnmo"][1] - cut_off_voltage["lnmo"][0])
    else:
        return row["voltage"]

def float_size(row):
    return float(row["size"].replace("um", ""))

def preprocess_data(data_train):
    df_train_deduped = data_train.drop_duplicates(
        subset=[
            "file_name", "material", "size", "specific_capacity",
            'temperature', "percent", "cathode_area", "area_living_material",
            "rate_cycle", "rate_rating", "cycle_num", "chargeOrDischarge",
            "voltage"
        ])
    return df_train_deduped

def generate_prediction_data(params):
    """Generate test data based on user parameters"""
    n = 25000  
    
    
    material = params.get('material', 'LFP')
    size = params.get('size', '100um')
    specific_capacity = params.get('specific_capacity', 150)
    temperature = params.get('temperature', 28)
    percent = params.get('percent', 15)
    cathode_area = params.get('cathode_area', 0.1256)
    area_living_material = params.get('area_living_material', 5.830149)
    
    
    file_name_arr = np.full(n, f"{material}_Li(180)_{percent}%_{size}_2C_{temperature}℃_127.0.0.1-BTS83-39-6-5-87")
    material_arr = np.full(n, material) 
    size_arr = np.full(n, size) 
    specific_capacity_arr = np.full(n, specific_capacity)
    temperature_arr = np.full(n, temperature)
    percent_arr = np.full(n, percent)
    cathode_area_arr = np.full(n, cathode_area) 
    area_living_material_arr = np.full(n, area_living_material)
    
    
    
    group_rate_cycle = [1]*1000 + [2]*1000 + [3]*1000 + [4]*1000 + [5]*1000
    rate_cycle_arr = group_rate_cycle * 5
    
    
    group_rate_rating = [0.1]*5000 + [0.5]*5000 + [1]*5000 + [2]*5000 + [3]*5000
    rate_rating_arr = group_rate_rating
    
    cycle_num_arr = []
    for i in range(1, 26):
        cycle_num_arr += [i] * 1000
    
    
    cov=cut_off_voltage[material.lower()]
    voltage_group = np.linspace(cov[0], cov[1], 1000)
    voltage_arr = np.tile(voltage_group, 25)

    chargeOrDischarge_arr = np.full(n, 1)
    capacity_arr = np.full(n, np.nan)
    
    df = pd.DataFrame({
        "file_name": file_name_arr, 
        "material": material_arr, 
        "size": size_arr,
        "specific_capacity": specific_capacity_arr,
        "temperature": temperature_arr,
        "percent": percent_arr,
        "cathode_area": cathode_area_arr,
        "area_living_material": area_living_material_arr,
        "rate_cycle": rate_cycle_arr,
        "rate_rating": rate_rating_arr,
        "cycle_num": cycle_num_arr,
        "chargeOrDischarge": chargeOrDischarge_arr,
        "voltage": voltage_arr,
        "capacity": capacity_arr
    })
    return df,voltage_group

from django.conf import settings
import os
def make_predictions(params):
    """Main function to generate predictions"""
    
    df_test,voltage_group = generate_prediction_data(params)
    
    
    df_test["voltage"] = df_test.apply(normalize_voltage, axis=1)
    df_test["size"] = df_test.apply(float_size, axis=1)
    df_test_deduped = preprocess_data(df_test)
    print(torch.cuda.is_available())
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    model = TransformerEncoderOnly(input_dim=11,
                                    emb_dim=512,
                                    n_heads=8, 
                                    n_layers=4).to(device)
    
    model_path = os.path.join(settings.BASE_DIR, 'battery_manage_system','static', 'battery_manage_system', 'models', '1743010298360', 'best_model_2outs.pth')
    x_scaler_path = os.path.join(settings.BASE_DIR, 'battery_manage_system','static', 'battery_manage_system', 'scaler', '1743010298360', 'x_scaler_2outs.pkl')
    y_scaler_path = os.path.join(settings.BASE_DIR, 'battery_manage_system','static', 'battery_manage_system', 'scaler', '1743010298360', 'y_scaler_2outs.pkl')
    
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")
    
    
    model.load_state_dict(torch.load(model_path))
    model.eval()
    
    
    with open(x_scaler_path, 'rb') as f:
        x_scaler = pickle.load(f)
    
    with open(y_scaler_path, 'rb') as f:
        y_scaler = pickle.load(f)
    
    
    X_test_new = df_test_deduped.iloc[:, 2:-1].values
    X_test_new = x_scaler.transform(X_test_new)
    X_test_new = torch.tensor(X_test_new, dtype=torch.float32).to(device)

    
    
    model.eval()

    
    model = model.to(device)

    
    predictions_list = []

    
    batch_size = 32

    
    for i in range(0, len(X_test_new), batch_size):
        
        batch = X_test_new[i:i+batch_size]
        
        
        batch = batch.to(device)
        
        
        with torch.no_grad():
            
            outputs = model(batch)
    
        
        predictions_batch = outputs.cpu().numpy()
        predictions_list.append(predictions_batch)

    
    predictions = np.concatenate(predictions_list, axis=0)
    print("len(predictions):",len(predictions))
    
    predictions_second_col = predictions[:, 1].reshape(-1, 1)
    predictions_second_col_original = y_scaler.inverse_transform(predictions_second_col)
    
    predictions_combined = np.hstack((predictions[:, 0].reshape(-1, 1), predictions_second_col_original))
    print("len(predictions_combined):",len(predictions_combined))
    
    y_preds_restored = []
    window_size = 1000
    for i in range(0, len(predictions_combined), window_size):
        window_preds = predictions_combined[i:i + window_size]
        max_value = window_preds[:, 1].mean() 
        restored_window = window_preds[:, 0] * max_value
        y_preds_restored.extend(restored_window)
        print(len(y_preds_restored))
    return y_preds_restored,voltage_group