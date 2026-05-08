import matplotlib.pyplot as plt
import numpy as np
from math import sqrt, ceil
from pymongo import MongoClient
from pprint import pprint


MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "battery_db"


def query_battery_info(field_value_pairs):
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client["battery_db"]
    metadata_col = db["battery_metadata"]
    
    
    FIELD_TYPES = {
        'material': str, 
        'percent': int, 
        'self_made': str, 
        'size': int, 
        'specific_capacity': int, 
        'temperature': float 
    }
    
    
    if not field_value_pairs:
        raise ValueError("至少需要提供一个查询条件")
    
    if len(field_value_pairs) > 4:
        raise ValueError("最多只能选择四个查询条件")
    
    
    query = {}
    for field, value in field_value_pairs.items():
        if field not in FIELD_TYPES:
            raise ValueError(f"无效字段 '{field}'，可选: {', '.join(FIELD_TYPES.keys())}")
        expected_type = FIELD_TYPES[field]
        try:
            
            if expected_type == float:
                converted_value = float(value)
            elif expected_type == int:
                converted_value = int(float(value))  
            else:
                converted_value = str(value)
        except (ValueError, TypeError):
            raise ValueError(f"字段 '{field}' 需要 {expected_type.__name__} 类型")
        if field=="size":
            converted_value=str(converted_value)+"um"
        query[f"info.{field}"] = converted_value
    print("query:",query)
    
    results = list(metadata_col.find(
        query,
        {"bat_key": 1, "file_name": 1, "_id": 0}
    ))
    
    return results if results else []


TITLE_MAP={
    "qd_cycle":["Cycle num","Discharge capcity"],
    "qc_cycle":["Cycle num","Charge capcity"],
}

def fetch_overall_data(bat_keys,property):
    PROPERTY_MAP={
        "qd_cycle":["Voltage","Qdlin"],
        "qc_cycle":["Voltage","Qclin"],
    }
    axis_for_plot=PROPERTY_MAP[property]
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    cycles_col = db["battery_cycles"]
    battery_data = {}
    
    for bat_key in bat_keys:
        cycles = list(cycles_col.find(
            {"bat_key": bat_key},
            {axis_for_plot[0]: 1, axis_for_plot[1]: 1, "cycle_num": 1, "_id": 0}
        ).sort("cycle_num"))
        capacity= [max(cycle[axis_for_plot[1]]) for cycle in cycles]
        
        battery_data[bat_key] = capacity
    print("capacity get!")
    return battery_data,property,axis_for_plot

import io
import base64
def plot_overall_curves(battery_data,property,axis_for_plot):
    plt.style.use('/home/jju/custom.mplstyle')
    if not battery_data:
        print("没有可用的电池数据。")
        return
    print("开始绘制电池曲线...")
    num_batteries = len(battery_data)
    bat_keys = list(battery_data.keys())
    print(bat_keys)
    
    buffer = io.BytesIO()

    
    cols = ceil(sqrt(num_batteries))
    rows = ceil(num_batteries / cols)
    
    
    fig, axes = plt.subplots(rows, cols, figsize=(cols*6, rows*4))
    fig.subplots_adjust(hspace=0.4, wspace=0.3) 
    
    
    if num_batteries == 1:
        axes = np.array([[axes]])
    elif rows == 1 or cols == 1:
        axes = axes.reshape(-1, 1)
    
    
    for idx, bat_key in enumerate(bat_keys):
        overall = battery_data[bat_key]
        row = idx // cols
        col = idx % cols
        ax = axes[row, col]
        
        if not overall:
            ax.text(0.5, 0.5, f"No data for {bat_key}", ha='center', va='center')
            ax.set_title(bat_key)
            continue
        x_ = range(1,len(overall)+1,1)
        y_ = overall
        if x_ and y_:
            ax.plot(x_, y_, color="blue", alpha=0.7, linewidth=1)
        
        
        title_for_plot=TITLE_MAP[property]
        
        ax.set_title(f"Battery {bat_key}")
        ax.set_xlabel(title_for_plot[0])
        ax.set_ylabel(title_for_plot[1])
        ax.grid(True)
    
    
    for idx in range(num_batteries, rows*cols):
        axes[idx//cols, idx%cols].axis('off')
    
    
    
    
    
    plt.savefig(buffer, dpi=300, format='png', bbox_inches='tight')
    plt.close(fig)  
    print("结束电池曲线绘制")
    
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    return image_base64

def interactive_query_and_plot_overall(bat_keys,property="raw_qc_voltage"):
    print("可用查询字段: material, percent, self_made, size, specific_capacity, temperature")
    
    try:
        battery_data,property,axis_for_plot = fetch_overall_data(bat_keys,property)
        image_base64=plot_overall_curves(battery_data,property,axis_for_plot)
        return image_base64
    except ValueError as e:
        print(f"输入错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    
    
    
    
    results=query_battery_info({
        'material': 'LFP',
        'temperature': 28,
        'percent': 10,
        
    })
    print(results[0]["bat_key"])
    print(list(result["bat_key"] for result in results))
    
    
    
    
