import matplotlib.pyplot as plt
import numpy as np
from math import sqrt, ceil
from pymongo import MongoClient
from pprint import pprint


MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "battery_db"


def query_file_name_by_bat_key(bat_key):
    
    client = MongoClient('mongodb://localhost:27017/')
    
    
    db = client['battery_db']
    metadata_col = db['battery_metadata']
    
    
    result = metadata_col.find_one(
        {"bat_key": bat_key},
        {"file_name": 1, "info": 1, "_id": 0}
    )
    
    if result:
        
        return {
            "filename": result.get('file_name', ''),
            "info": {
                "self_made": result.get('info', {}).get('self_made', ''),
                "size": result.get('info', {}).get('size', ''),
                "temperature": result.get('info', {}).get('temperature', ''),
                "specific_capacity": result.get('info', {}).get('specific_capacity', ''),
                "area_living_material": result.get('info', {}).get('area_living_material', ''),
                "c_rate": result.get('info', {}).get('c_rate', '')
            }
        }
    else:
        return None


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
    
    if len(field_value_pairs) > 3:
        raise ValueError("最多只能选择三个查询条件")
    
    
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
    
    
    results = list(metadata_col.find(
        query,
        {"bat_key": 1, "file_name": 1, "_id": 0}
    ))
    
    return results

def filter_batcycle(type,lowest_value):
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client["battery_db"]
    cycles_col = db["battery_cycles"]
    filtered_data = []
    bat_keys = [f"b{i}" for i in range(110)] 
    
    field_name = "Qdlin" if type == "Qdlin" else "Qclin"
    
    pipeline = [
        
        {"$match": {
            "bat_key": {"$in": bat_keys},
            "cycle_num": {"$lte": 25}
        }},
        
        {"$addFields": {
            "q_max": {"$max": f"${field_name}"}
        }},
        
        {"$match": {
            "q_max": {"$lt": float(lowest_value)}
        }},
        
        {"$group": {
            "_id": "$bat_key",
            "cycles": {"$push": {
                "cycle_num": "$cycle_num",
                "q_max": "$q_max"
            }}
        }},
        
        {"$sort": {"_id": 1}}
    ]
    agg_result = list(cycles_col.aggregate(pipeline))
    
    for doc in agg_result:
        bat_key = doc["_id"]
        
        sorted_cycles = sorted(doc["cycles"], key=lambda x: x["cycle_num"])
        cycle_data = [f"{c['cycle_num']}_{round(c['q_max'], 3)}" for c in sorted_cycles]
        fd_per_cycle = {"bat_key": bat_key, "cycle_data": cycle_data}
        filtered_data.append(fd_per_cycle)
    if not filtered_data:
        return "未查询到对应数据"
    return filtered_data

TITLE_MAP={
    "qdlin_voltage":["Discharge capcity(Interpolated)","Voltage"],
    "qclin_voltage":["Charge capcity(Interpolated)","Voltage"],
    "voltage_qdlin":["Voltage","Discharge capcity(Interpolated)"],
    "voltage_qclin":["Voltage","Charge capcity(Interpolated)"],
    "raw_qd_voltage":["Discharge capcity(raw)","Voltage"],
    "raw_qc_voltage":["Charge capcity(raw)","Voltage"],
    "voltage_raw_qd":["Voltage","Discharge capcity(raw)"],
    "voltage_raw_qc":["Voltage","Charge capcity(raw)"],
}

def fetch_cycles_data(bat_keys,property):
    PROPERTY_MAP={
        "qdlin_voltage":["Qdlin","Voltage"],
        "qclin_voltage":["Qclin","Voltage"],
        "voltage_qdlin":["Voltage","Qdlin"],
        "voltage_qclin":["Voltage","Qclin"],
        "raw_qd_voltage":["raw_qd","raw_qd_voltage"],
        "raw_qc_voltage":["raw_qc","raw_qc_voltage"],
        "voltage_raw_qd":["raw_qd_voltage","raw_qd"],
        "voltage_raw_qc":["raw_qc_voltage","Voltraw_qcage"],
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
        battery_data[bat_key] = cycles
    
    return battery_data,property,axis_for_plot

import io
import base64
def plot_battery_curves(battery_data,property,axis_for_plot):
    plt.style.use('/home/jju/custom.mplstyle')
    if not battery_data:
        print("没有可用的电池数据。")
        return
    print("开始绘制电池曲线...")
    num_batteries = len(battery_data)
    bat_keys = list(battery_data.keys())
    
    
    buffer = io.BytesIO()

    
    cols = ceil(sqrt(num_batteries))
    rows = ceil(num_batteries / cols)
    
    
    fig, axes = plt.subplots(rows, cols, figsize=(cols*6, rows*4))
    fig.subplots_adjust(hspace=0.4, wspace=0.3) 
    
    
    if num_batteries == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    
    for idx, bat_key in enumerate(bat_keys):
        cycles = battery_data[bat_key]
        ax = axes[idx]  
        
        if not cycles:
            ax.text(0.5, 0.5, f"No data for {bat_key}", ha='center', va='center')
            ax.set_title(bat_key)
            continue
            
        
        cmap = plt.cm.viridis
        max_cycle = max([cycle["cycle_num"] for cycle in cycles])
        
        
        for cycle in cycles:
            
            x_ = cycle.get(axis_for_plot[0], [])
            y_ = cycle.get(axis_for_plot[1], [])
            if x_ and y_:
                color = cmap(cycle["cycle_num"] / max_cycle)
                ax.plot(x_, y_, color=color, alpha=0.7, linewidth=1,
                       label=f"Cycle {cycle['cycle_num']}" if cycle['cycle_num'] % 50 == 0 else "")
        
        
        norm = plt.Normalize(1, max_cycle)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        fig.colorbar(sm, ax=ax, label="Cycle Number")
        
        title_for_plot=TITLE_MAP[property]
        
        ax.set_title(f"Battery {bat_key}")
        ax.set_xlabel(title_for_plot[0])
        ax.set_ylabel(title_for_plot[1])
        ax.grid(True)
    
    
    for idx in range(num_batteries, rows*cols):
        axes[idx].axis('off')  
    
    
    
    
    
    plt.savefig(buffer, dpi=300, format='png', bbox_inches='tight')
    plt.close(fig)  
    print("结束电池曲线绘制")
    
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    return image_base64

def interactive_query_and_plot(bat_keys,property="raw_qc_voltage"):
    print("可用查询字段: material, percent, self_made, size, specific_capacity, temperature")
    print("示例输入: material=LFP temperature=28")
    
    try:
        battery_data,property,axis_for_plot = fetch_cycles_data(bat_keys,property)
        image_base64=plot_battery_curves(battery_data,property,axis_for_plot)
        return image_base64
    except ValueError as e:
        print(f"输入错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    
    
    
    
    results=query_battery_info({
        'material': 'LFP',
        'temperature': 28,
        
        'size': "55"
    })
    print(query_file_name_by_bat_key("b1"))
    print(results[0]["bat_key"])
    print(list(result["bat_key"] for result in results))
    
    
    
