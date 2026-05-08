
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["battery_db"]
cycles_col = db["battery_cycles"]


sample = cycles_col.find_one(
    {"bat_key": "b1", "cycle_num": 1},
    {"Qclin": 1, "Qdlin": 1, "cycle_num": 1, "_id": 0},
)
print("=== b1 cycle 1 样本 ===")
if sample:
    qdlin = sample.get("Qdlin", [])
    qclin = sample.get("Qclin", [])
    print(f"  Qdlin: len={len(qdlin)}, max={max(qdlin) if qdlin else 'empty'}")
    print(f"  Qclin: len={len(qclin)}, max={max(qclin) if qclin else 'empty'}")
else:
    print("  b1 cycle 1 不存在")


total = cycles_col.count_documents({})
has_qclin = cycles_col.count_documents({"Qclin": {"$exists": True, "$ne": []}})
print(f"\n=== 全库统计 ===")
print(f"  总文档数: {total}")
print(f"  Qclin 非空: {has_qclin}")
print(f"  覆盖率: {has_qclin / total * 100:.1f}%" if total else "  无数据")


lowest_value = 15
test_keys = ["b1", "b2", "b3"]
print(f"\n=== filter_batcycle 用 Qclin, lowest_value={lowest_value} ===")
for bat_key in test_keys:
    query = {
        "bat_key": bat_key,
        "cycle_num": {"$lte": 25},
        "$expr": {"$lt": [{"$max": "$Qclin"}, float(lowest_value)]},
    }
    cycles = list(
        cycles_col.find(query, {"Qclin": 1, "cycle_num": 1, "_id": 0}).sort("cycle_num")
    )

    if cycles:
        cycle_data = []
        for c in cycles:
            vals = c.get("Qclin", [])
            mx = round(max(vals), 3) if vals else 0
            cycle_data.append(f"{c['cycle_num']}_{mx}")
        print(f"  {bat_key}: {cycle_data}")
    else:
        print(f"  {bat_key}: 无匹配循环")

import time


print("\n=== 优化前：110次串行查询（原逻辑） ===")
start = time.time()
bat_keys_full = [f"b{i}" for i in range(110)]
filtered_data_original = []
for bat_key in bat_keys_full:
    query = {
        "bat_key": bat_key,
        "cycle_num": {"$lte": 25},
        "$expr": {"$lt": [{"$max": "$Qdlin"}, float(lowest_value)]},
    }
    cycles = list(cycles_col.find(query, {"Qdlin": 1, "cycle_num": 1, "_id": 0}).sort("cycle_num"))
    if cycles:
        cycle_data = []
        for c in cycles:
            vals = c.get("Qdlin", [])
            mx = round(max(vals), 3) if vals else 0
            cycle_data.append(f"{c['cycle_num']}_{mx}")
        filtered_data_original.append({"bat_key": bat_key, "cycle_data": cycle_data})
duration_original = time.time() - start
print(f"  耗时: {duration_original:.2f}s")
print(f"  匹配电池数: {len(filtered_data_original)}")


print("\n=== 优化后：单条 Aggregation Pipeline ===")
start = time.time()
pipeline = [
    
    {"$match": {
        "bat_key": {"$in": bat_keys_full},
        "cycle_num": {"$lte": 25}
    }},
    
    {"$addFields": {
        "q_max": {"$max": "$Qdlin"}  
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

filtered_data_optimized = []
for doc in agg_result:
    bat_key = doc["_id"]
    
    sorted_cycles = sorted(doc["cycles"], key=lambda x: x["cycle_num"])
    cycle_data = [f"{c['cycle_num']}_{round(c['q_max'], 3)}" for c in sorted_cycles]
    filtered_data_optimized.append({"bat_key": bat_key, "cycle_data": cycle_data})
duration_optimized = time.time() - start
print(f"  耗时: {duration_optimized:.2f}s")
print(f"  匹配电池数: {len(filtered_data_optimized)}")
print(f"\n  加速比: {duration_original / duration_optimized:.1f}x")

client.close()
