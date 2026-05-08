from django.shortcuts import render
import torch

from crystals.moco_builder import MoCo
from crystals.gatmodel_ssl import GATModel 
from crystals.gatmodel_ssl_MultiHeads import GATMultiHeadModel 
from crystals.gcnmodel_ssl import GCNModel 
from crystals.GNNWithRegression import GNNWithRegression_singleMLP 

from crystals.utils import cif_to_structure, gaussian_expansion, structure_to_graph


from django.http import HttpResponse
from django.shortcuts import render
from .forms import CrystalForm
from .models import Crystal_properties, Crystal_smiles_psi4, Crystal_smiles_rdkit,Crystal
import pandas as pd
from django.shortcuts import render


from django.http import JsonResponse, HttpResponse
from django.http import Http404 
import os
from django.conf import settings 

from autocompute.models import ComputationTask 

from django.shortcuts import HttpResponse
import uuid  
from django.utils import timezone 
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt  
from io import BytesIO
import pandas as pd
import subprocess
import shutil
import traceback
import time
from django.core.cache import cache
from rdkit import Chem
from datetime import datetime 
import zipfile 
from django.contrib.auth.decorators import login_required
from threading import Thread
from cryptography.fernet import Fernet  
import json
from autocompute.models import ComputeTask  
from django.core.paginator import Paginator


import re
import mimetypes
from urllib.parse import unquote_plus  
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import io
import logging


from register.decorators import auto_compute_permission_required, premium_permission_required, premium_permission_required, ml_prediction_permission_required

logger = logging.getLogger('django')  


@premium_permission_required
def crystal_search(request):
    if request.method == "POST":
        polymer_name = request.POST.get('polymer_name', None)
        model = polymer_name
        field_names = list(model._meta.get_fields())
        print(field_names)
        titles = [f.verbose_name for f in field_names]
        field_Names = [f.name for f in field_names]
        data = [[getattr(ins, name) for name in field_Names]
                for ins in model.objects.filter(label=polymer_name)]
        print(titles)
        print(data)
    else:
        model = polymer_name
        field_names = list(model._meta.get_fields())
        print(field_names)
        titles = [f.verbose_name for f in field_names]
        field_Names = [f.name for f in field_names]
        data = [[getattr(ins, name) for name in field_Names] for ins in model.objects.all()]
        print(data[0])

    return render(request, 'crystal.html', {'field_names': titles, 'data': data})



def crystal_display(request):
    crystal_list = Crystal.objects.values('crystal').distinct()
    return render(request, "crystal_display.html", {'crystal_list': crystal_list})

def crystal_selected(request):
    crystal_list = Crystal.objects.values('crystal').distinct() 
    selected_crystal = request.GET.get('crystal','Al') 
    excluded_fields=['id','author','Author'] 
    
    field_names = Crystal._meta.get_fields()
    
    field_names_verbose = [f.name for f in field_names if not (f.name in excluded_fields or isinstance(f, Crystal))]
    
    crystals_selected = Crystal.objects.filter(crystal=selected_crystal)  
    
    
    data = [[getattr(instance, name) for name in field_names_verbose] for instance in crystals_selected]

    
    dict = {
        'crystal_list': crystal_list, 
        'selected_crystal': selected_crystal, 
        'field_names':field_names_verbose,
        'data':data, 
        'image_extensions': ['jpg', 'jpeg', 'png', 'gif'],
        'file_extensions': ['txt', 'csv','CSV', 'pdf'],
        
        
    }

    return render(request,"crystal_selected.html", dict)

def crystal_visualize(request):
    return render(request,"crystal_visualization.html")

@ml_prediction_permission_required
def crystal_property_prediction_page(request):
    return render(request,"crystal_property_prediction.html")

def upload_data(request):
    Crystal.objects.all().delete()
    list=['Al','Ba','Ca','K','Li','Mg','Na','Zn']
    for item in list:
        df = pd.read_excel('./crystals/crystal_database/'+item+'_cleaned.xlsx')
        for _, row in df.iterrows():
            Crystal.objects.create(
                crystal=row['Crystal'],
                label = row['label'],
                band_gap=row['band_gap'],
                chemsys=row['chemsys'],
                density = row['density'],
                density_atomic = row['density_atomic'],
                deprecated = row['deprecated'],
                efermi = row['efermi'],
                energy_above_hull=row['energy_above_hull'],
                energy_per_atom = row['energy_per_atom'],
                formation_energy_per_atom=row['formation_energy_per_atom'],
                formula_anonymous = row['formula_anonymous'],
                formula_pretty=row['formula_pretty'],
                is_gap_direct = row['is_gap_direct'],
                is_magnetic = row['is_magnetic'],
                is_metal = row['is_metal'],
                is_stable = row['is_stable'],
                nelements = row['nelements'],
                nsites = row['nsites'],
                num_magnetic_sites = row['num_magnetic_sites'],
                num_unique_magnetic_sites = row['num_unique_magnetic_sites'],
                ordering = row['ordering'],
                theoretical = row['theoretical'],
                total_magnetization = row['total_magnetization'],
                volume = row['volume'],
            )
    return HttpResponse("Done!")

def calculate(request):
    return HttpResponse("Calculation!")
def prediction(request):
    return HttpResponse("Prediction!")

def crystal_structure_visualization_upload(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            
            error_message = "No file uploaded."
            return render(request, 'crystal_visualization.html', {'error_message': error_message})

        else:
            
            
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            unique_folder = f"{current_time}_{str(uuid.uuid4())}"

            
            upload_folder = os.path.join(settings.MEDIA_ROOT, 'Crystal/visualization_crystal_structure', unique_folder)
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            fs = FileSystemStorage(location=upload_folder)

            
            filename = fs.save(uploaded_file.name, uploaded_file)

            
            file_path = os.path.join(upload_folder, filename)

            
            file_url = fs.url(os.path.join('Crystal/visualization_crystal_structure', unique_folder, filename))

            success_message = "File uploaded successfully."

            
            context = {
                'success_message': success_message,
                'file_url': file_url,
            }

            logger.info(f"crystal_structure_visualization_upload : {context}")

            return render(request, 'crystal_visualization.html', context)

    else:
        return render(request, 'crystal_visualization.html')
    


@csrf_exempt
def upload_prediction(request):
    if request.method == 'POST':
        
        model_type = request.POST.get('modelSelect', None)
        
        
        logger.info(f"{model_type} completed.")

        
        uploaded_file = request.FILES.get('cifFile', None)
        
        
        if not model_type or not uploaded_file:
            return JsonResponse({'error': 'Missing model selection or file.'}, status=400)
        
        
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"
        
        upload_folder = os.path.join(settings.MEDIA_ROOT, 'Crystal', 'prediction', unique_folder)
        
        
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        
        fs = FileSystemStorage(location=upload_folder)
        filename = fs.save(uploaded_file.name, uploaded_file)
        
        file_path = os.path.join(upload_folder, filename)
        
        
        logger.info(f"upload {file_path} completed.")

        
        structure = cif_to_structure(file_path)
        
        
        logger.info(f"structure generate completed.")

        if structure is None:
            return JsonResponse({'error': 'Failed to parse CIF file.'}, status=400)
        
        
        graph_data = structure_to_graph(structure)
        
        
        logger.info(f"graph_data generate completed.")

        
        device = torch.device("cpu")
        
        
        model_dir = os.path.join(settings.BASE_DIR, 'crystals', 'static', 'prediction_model')

        
        if model_type == "MOCO+GAT":
            average_voltage_model_save_path = os.path.join(model_dir, 'average_voltage_MOCO+GAT.pth')
            capacity_grav_model_save_path = os.path.join(model_dir, 'capacity_grav_MOCO+GAT.pth')
            energy_grav_model_save_path = os.path.join(model_dir, 'energy_grav_MOCO+GAT.pth')
            
            average_voltage_base_encoder = GATModel(num_layers=10, dropout=0.1).to(device)
            capacity_grav_base_encoder = GATModel(num_layers=10, dropout=0.1).to(device)
            energy_grav_base_encoder = GATModel(num_layers=10, dropout=0.1).to(device)
        elif model_type == "GAT":
            average_voltage_model_save_path = os.path.join(model_dir, 'average_voltage_GAT.pth')
            capacity_grav_model_save_path = os.path.join(model_dir, 'capacity_grav_GAT.pth')
            energy_grav_model_save_path = os.path.join(model_dir, 'energy_grav_GAT.pth')
            
            average_voltage_base_encoder = GATModel(num_layers=10, dropout=0.1).to(device)
            capacity_grav_base_encoder = GATModel(num_layers=10, dropout=0.1).to(device)
            energy_grav_base_encoder = GATModel(num_layers=10, dropout=0.1).to(device)
        elif model_type == "GCN":
            average_voltage_model_save_path = os.path.join(model_dir, 'average_voltage_GCN.pth')
            capacity_grav_model_save_path = os.path.join(model_dir, 'capacity_grav_GCN.pth')
            energy_grav_model_save_path = os.path.join(model_dir, 'energy_grav_GCN.pth')
            
            average_voltage_base_encoder = GCNModel(num_layers=10, dropout=0.1).to(device)
            capacity_grav_base_encoder = GCNModel(num_layers=10, dropout=0.1).to(device)
            energy_grav_base_encoder = GCNModel(num_layers=10, dropout=0.1).to(device)
        
        
        logger.info(f"initialize model-part1 completed.")

        
        average_voltage_model = GNNWithRegression_singleMLP(average_voltage_base_encoder, regression_dim=1).to(device)
        capacity_grav_model = GNNWithRegression_singleMLP(capacity_grav_base_encoder, regression_dim=1).to(device)
        energy_grav_model = GNNWithRegression_singleMLP(energy_grav_base_encoder, regression_dim=1).to(device)
        
        
        logger.info(f"initialize model-part2 completed.")

        
        average_voltage_model.load_state_dict(torch.load(average_voltage_model_save_path))
        capacity_grav_model.load_state_dict(torch.load(capacity_grav_model_save_path))
        energy_grav_model.load_state_dict(torch.load(energy_grav_model_save_path))
        
        
        logger.info(f"load_state_dict completed.")

        
        average_voltage_model.eval()
        capacity_grav_model.eval()
        energy_grav_model.eval()
        
        
        graph_data = graph_data.to(device)
        
        
        average_voltage_output, _ = average_voltage_model(graph_data)
        capacity_grav_output, _ = capacity_grav_model(graph_data)
        energy_grav_output, _ = energy_grav_model(graph_data)
        
        
        average_voltage_result = average_voltage_output.cpu().detach().numpy().tolist()
        capacity_grav_result = capacity_grav_output.cpu().detach().numpy().tolist()
        energy_grav_result = energy_grav_output.cpu().detach().numpy().tolist()
        
        
        context = {
            'average_voltage': average_voltage_result,
            'capacity_grav': capacity_grav_result,
            'energy_grav': energy_grav_result
        }
        
        
        logger.info(f"{context}")

        
        return JsonResponse(context)
    
    
    return render(request, 'crystal_property_prediction.html')





from pathlib import Path
from django.http import FileResponse

SPA_DIST_DIR = Path(settings.BASE_DIR) / 'crystals' / 'dist'
SPA_ASSETS_DIR = SPA_DIST_DIR / 'assets'


def spa_index(request):
    """Serve Vue SPA index.html for all /crystals/app/* routes"""
    index_path = SPA_DIST_DIR / 'index.html'
    if not index_path.exists():
        return HttpResponse("Vue SPA build not found. Run `npm run build` in crystals/frontend/.", status=404)
    return FileResponse(open(index_path, 'rb'), content_type='text/html; charset=utf-8')


def spa_assets(request, path):
    """Serve Vue build assets (JS/CSS) with proper MIME types"""
    file_path = (SPA_ASSETS_DIR / path).resolve()
    if not str(file_path).startswith(str(SPA_ASSETS_DIR.resolve())):
        raise Http404
    if not file_path.is_file():
        raise Http404
    ctype, _ = mimetypes.guess_type(str(file_path))
    resp = FileResponse(open(file_path, 'rb'), content_type=ctype or 'application/octet-stream')
    resp['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resp

