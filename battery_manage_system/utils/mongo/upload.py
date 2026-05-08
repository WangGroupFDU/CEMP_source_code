import pickle
import numpy as np
import pandas as pd  
from pymongo import MongoClient
import matplotlib.pyplot as plt  



def convert_numpy(obj):
    if isinstance(obj, (np.ndarray, pd.Series)):  
        
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(item) for item in obj]
    elif obj is None:
        return ""  
    elif isinstance(obj, (np.int64, np.float64)):  
        return int(obj) if isinstance(obj, np.int64) else float(obj)
    return obj


pkl_path = "/path/to/example/media/bms/pkl_file/battery_data_full_0225_modified_sort_by_cathode.pkl"
with open(pkl_path, "rb") as f:
    data = pickle.load(f)



client = MongoClient("mongodb://localhost:27017/")
db = client["battery_db"]
cycles_col = db["battery_cycles"]
metadata_col = db["battery_metadata"]
cycles_col.delete_many({})
metadata_col.delete_many({})


for bat_key, bat_data in data.items():
    
    metadata_col.insert_one(
        {
        "file_name":data[bat_key]["file_name"], 
        "info":convert_numpy(data[bat_key]["info"]), 
        "bat_key": bat_key,
        }
        )
    for cycle_num, cycle_data in bat_data["cycledata"].items():
        try:
            
            doc = {
                **{k: convert_numpy(v) for k, v in cycle_data.items()},  
                "cycle_num": int(cycle_num),  
                "bat_key": bat_key,
            }
            cycles_col.insert_one(doc)
        except Exception as e:
            print(f"插入失败 {bat_key}-{cycle_num}: {str(e)[:200]}")
    print(f"不管成功还是失败，{bat_key}已经插入完成")

print(f"插入完成！cycle总文档数: {cycles_col.count_documents({})};metadata总文档数: {metadata_col.count_documents({})}")