import matplotlib.pyplot as plt
import numpy as np
from math import sqrt, ceil

def plot_voltage_vs_qdlin(battery_cycles_dict):
    if not battery_cycles_dict:
        print("没有可用的电池数据。")
        return
    
    num_batteries = len(battery_cycles_dict)
    bat_keys = list(battery_cycles_dict.keys())
    
    
    cols = ceil(sqrt(num_batteries))
    rows = ceil(num_batteries / cols)
    
    
    fig, axes = plt.subplots(rows, cols, figsize=(cols*5, rows*4))
    fig.subplots_adjust(hspace=0.4, wspace=0.3)
    
    
    if num_batteries == 1:
        axes = np.array([[axes]])
    elif rows == 1 or cols == 1:
        axes = axes.reshape(-1, 1)
    
    
    for idx, bat_key in enumerate(bat_keys):
        cycles = battery_cycles_dict[bat_key]
        row = idx // cols
        col = idx % cols
        ax = axes[row, col]
        
        if not cycles:
            ax.text(0.5, 0.5, f"No data for {bat_key}", 
                   ha='center', va='center')
            ax.set_title(bat_key)
            continue
            
        
        cmap = plt.cm.viridis
        max_cycle = max([cycle["cycle_num"] for cycle in cycles])
        
        
        for cycle_data in cycles:
            cycle_num = cycle_data["cycle_num"]
            qdlin = cycle_data.get("Qdlin", [])
            voltage = cycle_data.get("Voltage", [])
            
            if len(qdlin) > 0 and len(voltage) > 0:
                color = cmap(cycle_num / max_cycle)
                ax.plot(qdlin, voltage, 
                        color=color, 
                        alpha=0.7, 
                        linewidth=1,
                        label=f"Cycle {cycle_num}" if cycle_num % 50 == 0 else "")
        
        
        norm = plt.Normalize(1, max_cycle)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax)
        cbar.set_label("Cycle Number")
        
        
        ax.set_title(f"Battery {bat_key}")
        ax.set_xlabel("Qdlin (Discharge Capacity)")
        ax.set_ylabel("Voltage (V)")
        ax.grid(True)
    
    
    for idx in range(num_batteries, rows*cols):
        row = idx // cols
        col = idx % cols
        axes[row, col].axis('off')
    
    
    plt.tight_layout()
    plt.savefig("multi_battery_voltage_vs_qdlin.png", dpi=300, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    
    from random import random
    mock_data = {
        "b1": [{
            "cycle_num": i,
            "Qdlin": [random()*10 for _ in range(100)],
            "Voltage": [3.0 + random()*1.5 for _ in range(100)]
        } for i in range(1, 101)],
        "b2": [{
            "cycle_num": i,
            "Qdlin": [random()*8 for _ in range(100)],
            "Voltage": [3.2 + random()*1.3 for _ in range(100)]
        } for i in range(1, 51)],
        "b3": [{
            "cycle_num": i,
            "Qdlin": [random()*12 for _ in range(100)],
            "Voltage": [2.8 + random()*1.7 for _ in range(100)]
        } for i in range(1, 151)]
    }
    
    plot_voltage_vs_qdlin(mock_data)