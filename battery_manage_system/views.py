from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.http import HttpResponseRedirect
from .forms import BMS_result_form
from django.urls import reverse
import os
import mimetypes
from pathlib import Path
import numpy as np
import pandas as pd
import logging
import urllib
from datetime import datetime
from torch import nn
import torch
import json
from register.decorators import hybrid_login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import FileResponse
from django.conf import settings


import logging

logger = logging.getLogger("django")

from django.middleware.csrf import get_token
from django.utils.decorators import decorator_from_middleware


def index(request):
    
    logger.debug("index page")
    logger.debug("index page")
    logger.info("index page")
    
    return render(request, "bms_home.html")


from .utils.save_pkl.convert import get_LN_data, store_data


def add_data(request):
    if request.method == "POST":
        
        
        BmsResultForm = BMS_result_form(data=request.POST, files=request.FILES)

        
        

        if BmsResultForm.is_valid() == False:
            print(request.POST)
            print(BmsResultForm.errors)
            return JsonResponse(
                {
                    "error": "Form validation failed",
                    "details": str(BmsResultForm.errors),
                },
                status=400,
            )

        if BmsResultForm.is_valid():
            
            new_BmsResultForm = BmsResultForm.save(commit=False)
            current_time = datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            new_BmsResultForm.time_stamp = formatted_time

            if "bms_rawfile" in request.FILES:
                
                uploaded_file = request.FILES["bms_rawfile"]
                temp_dir = os.path.join(settings.MEDIA_ROOT, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, uploaded_file.name)

                with open(temp_path, "wb+") as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                logging.info(f"Saved uploaded file to: {temp_path}")
                new_BmsResultForm.bms_rawfile = uploaded_file.name

                try:
                    battery_data_dict = get_LN_data(1, temp_path)
                    store_data(battery_data_dict)
                except Exception as e:
                    logging.error(f"Error processing file: {str(e)}")
                    return JsonResponse(
                        {"error": f"File processing failed: {str(e)}"}, status=500
                    )
            new_BmsResultForm.save()
            print("sucessfully save data")
        return HttpResponseRedirect(reverse("bms:add_data"))
    
    cathode_options = ["LFP", "LCO", "NMC", "OTHER"]
    cathode_active_material_options = ["11", "15"]
    anode_options = ["Li", "C", "Si", "Other"]
    li_metal_thickness_options = [
        50,
        180,
    ]  
    charge_rate_options = ["0.5C", "1C", "2C", "3C", "rate"]
    polymer_options = ["PBDT", "Other"]
    polymer_percentage_options = ["5", "8", "10", "15", "20"]
    intristic_viscosity_options = ["15", "30"]
    ionic_liquid_options = ["C2mim-TfO"]
    ILE_options = ["C2mimFSI-LiFSI", "C3mpyrFSI-LiFSI"]
    li_conc_options = ["1.6", "3.2", "3.4", "4.8"]
    temperature_options = ["25", "28", "50", "80"]
    pressure_options = ["0.5", "0.6", "0.7", "0.8"]
    thickness_options = [
        "0",
        "61",
        "75",
        "80",
        "95",
        "100",
        "110",
        "120",
        "125",
        "135",
        "150",
    ]  
    magnetic_field_direction_options = ["No", "horizontal", "vertical"]
    csrf_token = get_token(request)
    template_dict = {
        "cathode_options": cathode_options,
        "cathode_active_material_options": cathode_active_material_options,
        "anode_options": anode_options,
        "li_metal_thickness_options": li_metal_thickness_options,
        "charge_rate_options": charge_rate_options,
        "polymer_options": polymer_options,
        "polymer_percentage_options": polymer_percentage_options,
        "intristic_viscosity_options": intristic_viscosity_options,
        "ionic_liquid_options": ionic_liquid_options,
        "ILE_options": ILE_options,
        "li_conc_options": li_conc_options,
        "temperature_options": temperature_options,
        "pressure_options": pressure_options,
        "thickness_options": thickness_options,
        "thickness_options": thickness_options,
        "magnetic_field_direction_options": magnetic_field_direction_options,
        "csrf_token": csrf_token,
    }
    return render(request, "add_data.html", {"template_dict": template_dict})



from pprint import pprint
from django.shortcuts import render
from .forms import BatteryQueryForm
from .utils.mongo.q_figure_combined import (
    interactive_query_and_plot,
    query_file_name_by_bat_key,
    filter_batcycle,
)
from .utils.mongo.figure_overall import (
    interactive_query_and_plot_overall,
    query_battery_info,
)



def parse_keys(input_str):
    
    s = input_str.replace("：", ":").replace("，", ",")
    parts = s.split(",")
    result = []

    for part in parts:
        part = part.strip()
        if ":" in part:
            
            try:
                start_str, end_str = part.split(":", 1)
                start = int(start_str)
                end = int(end_str)
                
                for num in range(start, end):
                    if num <= 109:
                        result.append(num)
            except ValueError:
                
                continue
        else:
            
            try:
                num = int(part)
                if num <= 109:
                    result.append(num)
            except ValueError:
                
                continue
    
    result = sorted(list(set(result)))  
    return result



print(parse_keys("1,3,5:10"))  
print(parse_keys("5:10,3,1"))  





@hybrid_login_required  
def visualize_battery_data(request):
    context = {}
    
    if request.method == "POST":
        form_id = request.POST.get("form_id")
        print(request.POST)
        print("form_id", form_id)
        if form_id == "concrete_display":
            bat_keys = str(request.POST["bat_keys"])  
            visualtype = request.POST.get("visualtype")  
            subplots = request.POST.get(
                "subplots"
            )  
            print(bat_keys, visualtype, subplots)
            
            print(parse_keys(bat_keys))
            bat_keys = parse_keys(bat_keys)
            bat_keys = ["b" + str(bat_key) for bat_key in bat_keys]
            image_base64 = interactive_query_and_plot(
                bat_keys=bat_keys, property=visualtype
            )
            
            return JsonResponse(
                {"concrete_display": f"data:image/png;base64,{image_base64}"}
            )
        elif form_id == "overall_display":
            bat_keys = str(request.POST["bat_keys"])  
            visualtype = request.POST.get("visualtype")  
            subplots = request.POST.get(
                "subplots"
            )  
            print(bat_keys, visualtype, subplots)
            
            print(parse_keys(bat_keys))
            bat_keys = parse_keys(bat_keys)
            bat_keys = ["b" + str(bat_key) for bat_key in bat_keys]
            image_base64 = interactive_query_and_plot_overall(
                bat_keys=bat_keys, property=visualtype
            )
            return JsonResponse(
                {"overall_display": f"data:image/png;base64,{image_base64}"}
            )
        elif form_id == "filter_batdata":
            lowest_value = str(request.POST["lowestValue"])  
            filter_visual_type = str(request.POST["filterVisualType"])  
            print(lowest_value, filter_visual_type)

            return_dict = filter_batcycle(filter_visual_type, lowest_value)
            print("return_dict", return_dict)

            return JsonResponse({"filter_batdata": return_dict})

        elif form_id == "search_batkey":
            form = BatteryQueryForm(request.POST)
            if form.is_valid():
                print("form.cleaned_data:", form.cleaned_data)  
                
                query_params = {}
                if form.cleaned_data.get("material") is not None:
                    query_params["material"] = form.cleaned_data.get("material")
                if (
                    form.cleaned_data.get("temperature") is not None
                ):  
                    query_params["temperature"] = form.cleaned_data.get("temperature")
                if form.cleaned_data.get("percent") is not None:
                    query_params["percent"] = form.cleaned_data.get("percent")
                if form.cleaned_data.get("size") is not None:
                    query_params["size"] = form.cleaned_data.get("size")
                
                specific_capacity = request.POST.get("specificCapacity")
                if specific_capacity and specific_capacity != "":
                    query_params["specific_capacity"] = float(specific_capacity)
                try:
                    
                    results = query_battery_info(query_params)
                    context["results_batkey"] = results
                    form = BatteryQueryForm()  
                    
                    
                    context["form"] = form
                    print("results:", results)
                    non_result = [{"file_name": "Not Found", "bat_key": "Not Found"}]
                    if not results:
                        return JsonResponse({"bat_key": non_result})
                    return JsonResponse({"bat_key": results})
                except ValueError as e:
                    context["error"] = str(e)

        elif form_id == "search_filename":
            print("search_filename")
            batkey = request.POST.get("bat_key", None)
            
            
            batkey = "b" + str(batkey)
            print("batkey:", batkey)
            result = query_file_name_by_bat_key(batkey)

            if result:
                return JsonResponse(result)
            else:
                return JsonResponse({"error": "Battery not found"}, status=404)
        else:
            
            context["error"] = "请输入有效的查询参数"
    elif request.method == "GET":
        
        default_query = {"material": "LFP", "temperature": 28, "percent": 10}
        context["results_batkey"] = query_battery_info(default_query)
        form = BatteryQueryForm()  
        
        context["form"] = form
        return render(request, "visual.html", context)
    else:
        return HttpResponse("Disallowed request method!")



from django.conf import settings
import os

from django.shortcuts import render
from .prediction_utils import make_predictions
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import torch


import matplotlib.font_manager as fm

fm.fontManager.addfont("/usr/share/fonts/truetype/times.ttf")  
fm.fontManager.addfont("/usr/share/fonts/truetype/simsun.ttc")





@csrf_exempt
def bms_short_prediction(request):
    context = {}

    if request.method == "POST":
        
        print(request.POST)  
        params = {
            "material": request.POST.get("material", "LFP"),
            "size": request.POST.get("size", "100um"),
            "specific_capacity": float(request.POST.get("specific_capacity", 150)),
            "temperature": float(request.POST.get("temperature", 28)),
            "percent": float(request.POST.get("percent", 15)),
            "cathode_area": float(request.POST.get("cathode_area", 0.1256)),
            "area_living_material": float(
                request.POST.get("area_living_material", 5.830149)
            ),
        }
        print(params)

        voltage_group = np.linspace(2.5, 4.25, 1000)
        
        predictions, voltage_group = make_predictions(params)  
        
        predictions_reshaped = np.array(predictions).reshape(25, 1000)
        prediction_data = [
            
            [{"x": x, "y": y} for x, y in zip(cycle_predictions, voltage_group)]
            for cycle_predictions in predictions_reshaped.tolist()
        ]
        
        

        print(params)
        print(predictions[:10])
        try:
            filename = "/path/to/example/battery_manage_system/predictions.npy"
            np.save(filename, prediction_data)
        except Exception as e:
            print(e)
        context["params"] = params
        context["data"] = prediction_data
        try:
            json.dumps(context)  
            return JsonResponse(context)
        except TypeError as e:
            print("JSON 序列化错误:", e)
            return JsonResponse({"error": "数据格式错误"}, status=500)

    cathode_active_material_options = ["LFP", "NCM", "LNMO"]
    csrf_token = get_token(request)
    template_dict = {
        "cathode_active_material_options": cathode_active_material_options,
        "csrf_token": csrf_token,
    }

    return render(request, "rate_prediction.html", {"template_dict": template_dict})


import os
import pickle
import base64
import matplotlib.pyplot as plt
from django.http import JsonResponse
from io import BytesIO
import gc


def get_pkl_files():
    pkl_dir = os.path.join(settings.MEDIA_ROOT, "bms", "pkl_file")
    return [f for f in os.listdir(pkl_dir) if f.endswith(".pkl")]


def load_pkl_file(filename):
    print(filename)
    pkl_path = os.path.join(settings.MEDIA_ROOT, "bms", "pkl_file", filename)
    pkl_path = "/path/to/example/media/bms/pkl_file/battery_data_full_0225_modified_sort_by_cathode_copy.pkl"
    with open(pkl_path, "rb") as f:
        pkl = pickle.load(f)
        return pkl


def bms_long_prediction(request):
    context = {}
    if request.method == "POST":
        
        print(request.POST)  
        params = {
            "material": request.POST.get("material", "LFP"),
            "size": request.POST.get("size", "100um"),
            "specific_capacity": float(request.POST.get("specific_capacity", 150)),
            "temperature": float(request.POST.get("temperature", 28)),
            "percent": float(request.POST.get("percent", 15)),
            "cathode_area": float(request.POST.get("cathode_area", 0.1256)),
            "area_living_material": float(
                request.POST.get("area_living_material", 5.830149)
            ),
        }
        print(params)
        form = BatteryQueryForm(request.POST)
        if form.is_valid():
            print("form.cleaned_data:", form.cleaned_data)  
            
            query_params = {}
            if form.cleaned_data.get("material") is not None:
                query_params["material"] = form.cleaned_data.get("material")
            if form.cleaned_data.get("temperature") is not None:  
                query_params["temperature"] = form.cleaned_data.get("temperature")
            if form.cleaned_data.get("percent") is not None:
                query_params["percent"] = form.cleaned_data.get("percent")
            if form.cleaned_data.get("size") is not None:
                query_params["size"] = form.cleaned_data.get("size")
            
            specific_capacity = request.POST.get("specificCapacity")
            if specific_capacity and specific_capacity != "":
                query_params["specific_capacity"] = float(specific_capacity)
            try:
                
                results = query_battery_info(query_params)
                context["results_batkey"] = results
                form = BatteryQueryForm()  
                
                
                context["form"] = form
                print("results:", results)
            except:
                non_result = [{"file_name": "Not Found", "bat_key": "Not Found"}]

        voltage_group = np.linspace(2.5, 4.25, 1000)
        
        predictions, voltage_group = make_predictions(params)  
        
        predictions_reshaped = np.array(predictions).reshape(25, 1000)
        prediction_data = [
            [{"x": x, "y": y} for x, y in zip(voltage_group, cycle_predictions)]
            for cycle_predictions in predictions_reshaped.tolist()
        ]
        
        

        print(params)
        print(predictions[:10])
        context["params"] = params
        context["data"] = prediction_data
        try:
            json.dumps(context)  
            return JsonResponse(context)
        except TypeError as e:
            print("JSON 序列化错误:", e)
            return JsonResponse({"error": "数据格式错误"}, status=500)

    cathode_active_material_options = ["LFP", "NCM", "LNMO"]
    csrf_token = get_token(request)
    template_dict = {
        "cathode_active_material_options": cathode_active_material_options,
        "csrf_token": csrf_token,
    }

    return render(
        request, "long_cycle_prediction.html", {"template_dict": template_dict}
    )


def view_opendata(request):
    return render(request, "opendata.html")


from django.http import FileResponse
import os
from django.http import HttpResponseNotFound


def pattern_recognition(request):
    return render(request, "pattern_recognition.html")



def download_file(request, filename):
    
    file_path = os.path.join(settings.MEDIA_ROOT, filename)

    
    if os.path.exists(file_path):
        
        response = FileResponse(open(file_path, "rb"))
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    else:
        
        return HttpResponseNotFound("File not found")






DIST_DIR = Path(settings.BASE_DIR) / "battery_manage_system" / "dist"
ASSETS_DIR = DIST_DIR / "assets"


def spa_index(request):
    index_path = DIST_DIR / "index.html"
    if not index_path.exists():
        return HttpResponse("Build not found. Run `npm run build`.", status=404)
    return FileResponse(open(index_path, "rb"), content_type="text/html; charset=utf-8")


def spa_assets(request, path: str):
    file_path = (ASSETS_DIR / path).resolve()
    if not str(file_path).startswith(str(ASSETS_DIR.resolve())):
        raise Http404
    if not file_path.is_file():
        raise Http404

    ctype, _ = mimetypes.guess_type(str(file_path))
    resp = FileResponse(
        open(file_path, "rb"), content_type=ctype or "application/octet-stream"
    )
    
    resp["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp
