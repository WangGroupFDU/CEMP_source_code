import pickle
import numpy as np
import pandas as pd  
from pymongo import MongoClient
import matplotlib.pyplot as plt 


client = MongoClient("mongodb://localhost:27017/")
db = client["battery_db"]
cycles_col = db["battery_cycles"]
metadata_col = db["battery_metadata"]

from pymongo import MongoClient

def get_unique_properties(bat_keys=None):
    """Get unique values for specified properties across all battery records.
    
    Args:
        bat_keys: List of bat_keys to query (defaults to b0-b109 if None)
    
    Returns:
        dict: Dictionary containing sets of unique values for each property
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client['battery_db']
    metadata_col = db['battery_metadata']
    
    
    if bat_keys is None:
        bat_keys = [f"b{i}" for i in range(110)]  
    
    
    properties = ["material", "temperature", "percent", "size", "specific_capacity"]
    unique_values = {prop: set() for prop in properties}
    
    
    for bat_key in bat_keys:
        result = metadata_col.find_one({"bat_key": bat_key})
        if result and 'info' in result:
            for prop in properties:
                if prop in result['info']:
                    unique_values[prop].add(result['info'][prop])
    
    return unique_values

def print_unique_properties(unique_values):
    """Print the collected unique values in a readable format."""
    for prop, values in unique_values.items():
        print(f"Unique {prop} values ({len(values)}):")
        for value in sorted(values):
            print(f"  - {value}")

if __name__ == "__main__":
    unique_values = get_unique_properties()
    print_unique_properties(unique_values)


























































    





        
















    





    

















