from locust import HttpUser, task, between
from pymongo import MongoClient
import matplotlib.pyplot as plt
import random
import os
import time


client = MongoClient("mongodb://localhost:27017/")
db = client["battery_db"]
cycles_col = db["battery_cycles"]

class MongoLoadUser(HttpUser):
    host = "http://localhost"  
    wait_time = between(0.5, 2.0)

    @task
    def query_and_plot(self):
        start_time = time.time()
        try:
            cycle_data = cycles_col.find_one({"bat_key": "b0", "cycle_num": 100})
            if cycle_data:
                qdlin = cycle_data.get("Qdlin", [])
                voltage = cycle_data.get("Voltage", [])
                
                user_id = random.randint(1, 10000)
                plt.figure(figsize=(10, 6))
                plt.plot(qdlin, voltage, 'b-', linewidth=2)
                plt.title(f"Locust User: Voltage vs. Qdlin (Cycle 100)")
                plt.xlabel("Qdlin (Discharge Capacity)")
                plt.ylabel("Voltage (V)")
                plt.grid(True)
                os.makedirs("locust_plots", exist_ok=True)
                
                plt.show()
                plt.close()
                
                
                response_time = int((time.time() - start_time) * 1000)  
                self.environment.events.request.fire(
                    request_type="MongoDB",
                    name="query_and_plot",
                    response_time=response_time,  
                    response_length=0,
                )
        except Exception as e:
            self.environment.events.request.fire(..., exception=e)