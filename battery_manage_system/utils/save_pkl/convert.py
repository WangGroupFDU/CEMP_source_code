















from .get_Qdlin import DataProcessor
from .get_Qdlin import calc_list_properties
from scipy.interpolate import interp1d




cut_off_voltage={
    "ncm":[3.0,4.25],
    "lnmo":[3.3,4.75],
    "lfp":[2.5,4.20]
}






























from IPython.display import display, HTML


display(HTML("<font color='red'>这是红色的文本</font>"))


import re


def extract_info(filename):
    
    
    pattern = r'(?P<material>NCM|LFP|LNMO)(?P<number>\d+)?\((?P<self_made>\d+(\.\d+)?)\)_Li\(\d+\)_(?P<percent>\d+%)_(?P<size>\d+um)(.*?)_(?P<c_rate>[\d.]+C)_(?P<temperature>\d+℃)'
    match = re.search(pattern, filename)
    
    if match:
        info = match.groupdict()
        
        
        info['material'] = 'NCM' if 'NCM' in info['material'] else info['material']
        
        area_capacity_approximate=float(info["self_made"]) 
        
        if info["material"] =="NCM":
            if area_capacity_approximate <5:
                info["specific_capacity"]=200
            elif area_capacity_approximate >5:
                info["specific_capacity"]=188
        elif info["material"]=="LFP":
            if area_capacity_approximate <5:
                info["specific_capacity"]=150
            elif area_capacity_approximate >5:
                info["specific_capacity"]=150
        else: 
            info["specific_capacity"]=120
        
        info['self_made'] = 'SelfMade' if float(info['self_made']) < 5 else 'Commercial'
        
        info['percent'] = int(info['percent'].replace('%', ''))
        
        size_value = int(info['size'].replace('um', ''))
        
        
        if info["material"]=="NCM" and info["percent"]==10:
            info['thickorThin'] = "thin" if size_value <= 75 else ("medium" if size_value < 150 else "thick")
        elif info["material"]=="NCM" and info["percent"]==15:
            info['thickorThin'] = "thin" if size_value <= 75 else ("medium" if size_value <= 165 else "thick")
        else:
            info['thickorThin'] = "thin" if size_value < 75 else ("medium"  if size_value < 150 else "thick")

        
        info['c_rate'] = float(info['c_rate'].replace('C', ''))
        if info['c_rate'] >= 2:
            info['c_rate'] = 3
        
        
        info['temperature'] = int(info['temperature'].replace('℃', ''))

        return info
    else:
        return None




import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import time


def interpolate_interp1d(x, y, interp_dims, xs=0, xe=1):
    if len(x) <= 2:
        return np.zeros(interp_dims)
    func = interp1d(x, y, bounds_error=False)
    new_x = np.linspace(xs, xe, interp_dims)
    return new_x,func(new_x)


def get_LN_data(index, file_path):
    battery_data_dict={}
    battery_data_dict[f"b{index}"]={}
    battery_data_dict[f"b{index}"]["filename"]=file_path
    battery_data_dict[f"b{index}"]["cycledata"]={}
    
    
    
    
    
    
    
    
    
    
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    
    read_start_time = time.time()  
    
    encodings = ['utf-8', 'gbk', 'utf-16', 'latin1']
    for encoding in encodings:
        try:
            battery_data = pd.read_csv(file_path, encoding=encoding)
            
            
            if any(isinstance(col, (int, float)) for col in battery_data.columns):
                
                battery_data = pd.read_csv(file_path, encoding=encoding, header=None)
                if len(battery_data.columns) >= 1:
                    
                    battery_data.columns = ['循环号'] + [f'col_{i}' for i in range(1, len(battery_data.columns))]
            
            
            if '循环号' in battery_data.columns:
                break
                
        except Exception as e:
            continue
            
    else:
        raise ValueError(f"Could not read CSV file with any encoding. Tried: {encodings}")

    read_end_time = time.time()  
    print(f"读取文件 '{file_path}' 耗时: {read_end_time - read_start_time:.2f} 秒")

    
    filter_start_time = time.time()  
    print(battery_data.describe())
    
    print("Actual columns in CSV:", battery_data.columns.tolist())
    
    
    cycle_col_names = ['循环号', '循环号 ', ' 循环号', 'cycle_number', 'Cycle Number']
    cycle_col = None
    
    for col in cycle_col_names:
        if col in battery_data.columns:
            cycle_col = col
            break
            
    if cycle_col is None:
        raise ValueError(f"Could not find cycle number column. Available columns: {battery_data.columns.tolist()}")
        
    max_cycle_num = battery_data[cycle_col].max()
    print(f"最大循环号为:{max_cycle_num}")
    data_filtered = battery_data[(battery_data["循环号"] != max_cycle_num)]
    filter_end_time = time.time()  
    print(f"数据过滤耗时: {filter_end_time - filter_start_time:.2f} 秒")
    print(len(data_filtered))

    
    
    
    filter_end_time = time.time()  
    print(f"数据过滤耗时: {filter_end_time - filter_start_time:.2f} 秒")
    




    
    cycle_data = data_filtered.groupby("循环号")
    
    
    
    

    cycle_data_list = list(cycle_data)  
    for cycle_num, group in cycle_data_list:
        
        if cycle_num <= max_cycle_num:
            
            charge_data = group[group["工步类型"] == "恒流充电"]
            max_charge_capacity=charge_data['充电比容量(mAh/g)'].max()
            max_charge_voltage=charge_data['电压(V)'].max()
            
            

            
            filename = file_path.split("/")[-1].lower()
            if filename.startswith("ncm"):
                processor = DataProcessor(charge_data['电压(V)'], charge_data['充电比容量(mAh/g)'],cut_off_voltage["ncm"],[3.3,0],charge_or_discharge=True)
            elif filename.startswith("lnmo"):
                processor = DataProcessor(charge_data['电压(V)'], charge_data['充电比容量(mAh/g)'],cut_off_voltage["lnmo"],[2.75,0],charge_or_discharge=True)
            elif filename.startswith("lfp"):
                processor = DataProcessor(charge_data['电压(V)'], charge_data['充电比容量(mAh/g)'],cut_off_voltage["lfp"],[3.2,0],charge_or_discharge=True)
            else:
                raise ValueError(f"无法从文件名 {filename} 确定电池材料类型 (应为ncm/lnmo/lfp开头)")
                
                

            xs_charge, ys_charge = processor.get_Qdlin_usrdef()
            if len(ys_charge)!=1000:
                print(f"length of ys_charge is: {len(ys_charge)}")

            plt.plot(xs_charge, ys_charge, color='lightblue', label=f'Fitted Qclin{cycle_num}')
            
            charge_current = charge_data["电流(A)"]

            discharge_data = group[group["工步类型"] == "恒流放电"]

            max_discharge_voltage = discharge_data["电压(V)"].max()
            min_discharge_voltage = discharge_data["电压(V)"].min()
            max_discharge_capacity = discharge_data["放电比容量(mAh/g)"].max()

            
            discharge_current = discharge_data["电流(A)"]  

            
            if filename.startswith("ncm"):
                processor = DataProcessor(discharge_data['电压(V)'], discharge_data['放电比容量(mAh/g)'],cut_off_voltage["ncm"],[4.25,1],charge_or_discharge=False)
            elif filename.startswith("lnmo"):
                processor = DataProcessor(discharge_data['电压(V)'], discharge_data['放电比容量(mAh/g)'],cut_off_voltage["lnmo"],[4.75,1],charge_or_discharge=False)
            elif filename.startswith("lfp"):
                processor = DataProcessor(discharge_data['电压(V)'], discharge_data['放电比容量(mAh/g)'],cut_off_voltage["lfp"],[3.5,1],charge_or_discharge=False)
            else:
                raise ValueError(f"无法从文件名 {filename} 确定电池材料类型 (应为ncm/lnmo/lfp开头)")
                
            try:    
                xs_discharge, ys_discharge = processor.get_Qdlin_usrdef()
            except:
                print(f"error in {file_path}")
                print(f"循环号是:{cycle_num}")
            if len(ys_discharge) != 1000:
                print(f"length of ys is: {len(ys_discharge)}")
            if max(ys_discharge) > 300:
                display(HTML("<font color='red'>放电容量的拟合数值大于300，请仔细检查</font>"))
                print(f"循环号是:{cycle_num}")
                
            plt.plot(
                xs_discharge,
                ys_discharge,
                color="lightblue",
                label=f"Fitted Qdlin{cycle_num}",
            )
            

            
            battery_data_dict[f"b{index}"]["cycledata"][str(cycle_num)] = {}
            battery_data_dict[f"b{index}"]["cycledata"][str(cycle_num)][
                "Qclin"
            ] = ys_charge
            battery_data_dict[f"b{index}"]["cycledata"][str(cycle_num)][
                "Qdlin"
            ] = ys_discharge
            
            battery_data_dict[f"b{index}"]["cycledata"][str(cycle_num)][
                "Voltage"
            ] = xs_charge

            
            battery_data_dict[f"b{index}"]["cycledata"][str(cycle_num)]["raw_qc"]=charge_data['充电比容量(mAh/g)']
            battery_data_dict[f"b{index}"]["cycledata"][str(cycle_num)]["raw_qc_voltage"]=charge_data['电压(V)']

            battery_data_dict[f"b{index}"]["cycledata"][str(cycle_num)][
                "Current_charge"
            ] = charge_current  
            battery_data_dict[f"b{index}"]["cycledata"][str(cycle_num)][
                "Current_discharge"
            ] = discharge_current  
            
            
            battery_data_dict[f"b{index}"]["cycledata"][str(cycle_num)]["raw_qd"] = (
                discharge_data["放电比容量(mAh/g)"]
            )
            battery_data_dict[f"b{index}"]["cycledata"][str(cycle_num)][
                "raw_qd_voltage"
            ] = discharge_data["电压(V)"]

            
            
            

            
            
            
            
            
            
            
        else:
            break
    plt.xlabel("Voltage (V)")
    plt.ylabel("Discharge capacity (mAh/g)")
    
    
    return battery_data_dict





def store_data(battery_data_dict, save_path='media/bms/pkl_file/battery_data.pkl'):
    
    with open(save_path, 'wb') as f:
        pickle.dump(battery_data_dict, f)

































































    























































