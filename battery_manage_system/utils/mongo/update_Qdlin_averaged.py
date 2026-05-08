import pickle
import numpy as np
import pandas as pd  
from pymongo import MongoClient
import matplotlib.pyplot as plt 


client = MongoClient("mongodb://localhost:27017/")
db = client["battery_db"]
cycles_col = db["battery_cycles"]
metadata_col = db["battery_metadata"]

def process_battery(bat_num):
    bat_key = f"b{bat_num}"
    
    
    
    
    
    
    
    query = {"bat_key": bat_key}
    docs = list(cycles_col.find(query))
    print(f"处理电池 {bat_key}, 总共有 {len(docs)} 个循环数据")

    
    max_qdlin_dict = {}
    for doc in docs:
        cycle_num = doc["cycle_num"]
        qdlin = doc.get("Qdlin", [])
        if qdlin:
            max_val = max(qdlin)
        else:
            max_val = 1  
        max_qdlin_dict[cycle_num] = max_val

    
    for doc in docs:
        cycle_num = doc["cycle_num"]
        qdlin = doc["Qdlin"]
        max_val = max_qdlin_dict.get(cycle_num, 1)  
        if max_val <1:
            max_val=1
        if max_val==0:
            print(f"find value zero for {cycle_num}")
            qdlin = list(cycles_col.find({"bat_key": bat_key,"cycle_num":cycle_num}, []))[0]["Qdlin"]
            print(qdlin)
            
            fig = plt.figure(figsize=(8, 4))
            plt.style.use('/home/jju/custom.mplstyle')
            plt.plot(qdlin)
            
            plt.savefig("fail.png", dpi=400)
            plt.show()
            print("失败")
            break
        qdlin_averaged = [x / max_val for x in qdlin]
        
        
        cycles_col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"Qdlin_averaged": qdlin_averaged}}
        )
    
    print(f"成功为 {bat_key} 的所有循环添加 Qdlin_averaged 字段！")


for bat_num in range(13, 14):  
    process_battery(bat_num)