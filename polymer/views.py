from django.shortcuts import render


from .forms import PolymerForm
from .models import (polymer_properties,
                     polymer_smiles_psi4,
                     polymer_smiles_rdkit,
                     polyelectrolyte,
                     experiment_polymer_data,
                     calculated_monomer_data,
                     calculated_polymer_data,
                     )

from django.http import JsonResponse, HttpResponse
from django.http import Http404 
import os
from django.conf import settings 

from ionic_liquid.models import metal_anion_energy,Example 
from ionic_liquid.models import IL,Cation,Anion
from ionic_liquid.models import Li_electrolyte,electrolyte
from autocompute.models import ComputationTask 

from django.shortcuts import HttpResponse
import uuid  
from django.utils import timezone 
from django.views.decorators.csrf import csrf_exempt  
import pandas as pd
import subprocess
import shutil
import traceback
import time
import subprocess, sys
import posixpath
from django.core.cache import cache
from rdkit import Chem
from datetime import datetime 
import zipfile 
from django.contrib.auth.decorators import login_required
from threading import Thread
from cryptography.fernet import Fernet  
import json
from autocompute.models import ComputeTask  
from autocompute.remote_utils import persist_remote_dispatch_request
from django.core.paginator import Paginator


from rest_framework import generics
from autocompute.serializers import ElectrolyteSerializer, Metal_Anion_EnergySerializer, ILSerializer, CationSerializer, Li_ElectrolyteSerializer, AnionSerializer
from rest_framework.permissions import IsAuthenticated 
import re


TEST_BOX_PATH = os.path.join(os.path.dirname(__file__), 'test_box')
if TEST_BOX_PATH not in sys.path:
    sys.path.append(TEST_BOX_PATH)


from smipoly.smip import monc, polg


MOLFORMULA_PATTERN = re.compile(r'^[A-Z][A-Za-z0-9]*$')
from autocompute.utils import validate_HTQC_single_point_energy_df, validate_HTQC_binding_energy_df, validate_HTQC_pka_pkb_df, validate_MD_system_df
from autocompute.utils import from_smiles_get_iupac_name, get_safe_name
import mimetypes
from urllib.parse import unquote_plus  
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import logging
from polymer.utils import (
    generate_polymer_run_notebook_tasks,
)

from register.decorators import auto_compute_permission_required, premium_permission_required, ml_prediction_permission_required, hybrid_login_required
logger = logging.getLogger('django')  
REMOTE_POLYMER_GENERATE_TARGET = posixpath.join("Polymer", "GeneratePolymer")


def _prepare_task_for_remote_dispatch(task: ComputeTask) -> None:

    task.remote_type = "remote"
    task.status = "queuing"
    task.server_name = None
    task.pid = None
    task.save(update_fields=["remote_type", "status", "server_name", "pid"])


def _enqueue_polymer_remote_task_for_scheduler(
    task: ComputeTask,
    source_dir: str,
    download_dir: str,
    remote_target_subpath: str,
) -> None:

    _prepare_task_for_remote_dispatch(task)
    persist_remote_dispatch_request(
        task=task,
        source_dir=source_dir,
        download_dir=download_dir,
        func_path="polymer.remote_utils.generate_polymer_run_notebook_tasks_remote",
        remote_target_subpath=remote_target_subpath,
    )



cipher_suite = Fernet(settings.FERNET_SECRET_KEY)


def encrypt_download_url_list(download_url_list):
    
    url_list_str = json.dumps(download_url_list)

    
    encrypted = cipher_suite.encrypt(url_list_str.encode('utf-8'))

    
    return encrypted.decode('utf-8')


def decrypt_download_url_list(encrypted_id):
    try:
        
        decrypted = cipher_suite.decrypt(encrypted_id.encode('utf-8'))

        
        download_url_list = json.loads(decrypted.decode('utf-8'))

        return download_url_list
    except Exception as e:
        
        print(f"解密失败: {str(e)}")
        return None

def display(request):
    return render(request, 'polymer_display.html')

@login_required
def generate_polymer_display(request):
    return render(request, 'generate_polymer.html')


def visualization_structure(request):
    return render(request, 'visualization_structure.html')


def polymer_database_card_display_view(request):
    return render(request, 'database/polymer_database_card_display_base.html')



@login_required
@ml_prediction_permission_required
def polymer_predict_page_view(request):
    return render(request,"polymer_predict.html")


@login_required
def polyelectrolyte_view(request):
    fields = polyelectrolyte._meta.get_fields()  
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [[getattr(instance, name) for name in field_names_verbose] for instance in polyelectrolyte.objects.all()]

    dict = {
        'field_names': field_names_verbose,
        'data': data,  
        'image_extensions': ['jpg', 'jpeg', 'png', 'gif'],
        'file_extensions': ['txt', 'csv', 'CSV', 'pdf'],
    }

    return render(request, "database/database_page.html", dict)


@login_required
@premium_permission_required
def database_experiment_polymer_data_view(request):
    
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        
        try:
            
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            search = request.GET.get('search', '').strip()
            sort_field = request.GET.get('sort_field', 'id')
            sort_order = request.GET.get('sort_order', 'asc')

            
            queryset = experiment_polymer_data.objects.all()

            
            if search:
                queryset = queryset.filter(
                    Q(Name__icontains=search) |
                    Q(PSMILES__icontains=search) |
                    Q(Reference__icontains=search)
                )

            
            if sort_order == 'desc':
                sort_field = f'-{sort_field}'

            valid_fields = [f.name for f in experiment_polymer_data._meta.get_fields()]
            if sort_field.lstrip('-') in valid_fields:
                queryset = queryset.order_by(sort_field)

            
            total_count = queryset.count()

            
            from django.core.paginator import Paginator
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)

            
            fields = experiment_polymer_data._meta.get_fields()
            field_names = [f.name for f in fields]

            
            data = []
            for obj in page_obj:
                item = {}
                for field_name in field_names:
                    value = getattr(obj, field_name)
                    item[field_name] = value if value is not None else ''
                data.append(item)

            response_data = {
                'success': True,
                'data': data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                },
                'meta': {
                    'field_names': field_names,
                }
            }

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    
    fields = experiment_polymer_data._meta.get_fields()  
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [[getattr(instance, name) for name in field_names_verbose] for instance in experiment_polymer_data.objects.all()]

    dict = {
        'field_names': field_names_verbose,
        'data': data,  
        'image_extensions': ['jpg', 'jpeg', 'png', 'gif'],
        'file_extensions': ['txt', 'csv', 'CSV', 'pdf'],
    }

    return render(request, "database/database_page.html", dict)


@login_required
@premium_permission_required
def database_calculated_monomer_data_view(request):
    fields = calculated_monomer_data._meta.get_fields()  
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [[getattr(instance, name) for name in field_names_verbose] for instance in calculated_monomer_data.objects.all()]

    dict = {
        'field_names': field_names_verbose,
        'data': data,  
        'image_extensions': ['jpg', 'jpeg', 'png', 'gif'],
        'file_extensions': ['txt', 'csv', 'CSV', 'pdf'],
    }

    return render(request, "database/database_page.html", dict)


@login_required
@premium_permission_required
def database_calculated_polymer_data_view(request):
    fields = calculated_polymer_data._meta.get_fields()  
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [[getattr(instance, name) for name in field_names_verbose] for instance in calculated_polymer_data.objects.all()]

    dict = {
        'field_names': field_names_verbose,
        'data': data,  
        'image_extensions': ['jpg', 'jpeg', 'png', 'gif'],
        'file_extensions': ['txt', 'csv', 'CSV', 'pdf'],
        
        
    }

    return render(request, "database/database_page.html", dict)



@hybrid_login_required  
@csrf_exempt  
def copolymer_property_predict(request):
    logger.info("pass_1")

    if request.method == 'POST':
        
        logger.info("Request body: %s", request.body.decode('utf-8'))

        
        try:
            data = json.loads(request.body)
            logger.info("Parsed data: %s", data)
        except json.JSONDecodeError as e:
            logger.error("JSONDecodeError: %s", e)
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        
        polymerization_method = data.get('polymerization_method')

        if not polymerization_method:
            return JsonResponse({'error': 'Polymerization method is required'}, status=400)

        
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())[:6]}"

        
        download_dir = os.path.join(settings.MEDIA_ROOT, 'Polymer', 'polymer_predict', 'Downloads', unique_folder)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        response_data = {
            'polymerization_method': polymerization_method,
            'table_data': [],
            'polymer_name': '',
            'number_of_blocks': ''
        }

        
        if polymerization_method == 'homopolymer':
            
            
            table_data = data.get('table_data', [])
            if not table_data:
                return JsonResponse({'error': 'No data provided for homopolymer'}, status=400)

            
            for item in table_data:
                response_data['table_data'].append({
                    'Name': item.get('name'),
                    'SMILES': item.get('smiles'),
                    'repeating unit': item.get('repeating_unit_number')
                })

            
            df = pd.DataFrame(response_data['table_data'])
            
            excel_filename = 'copolymer_system.xlsx'
            
            excel_path = os.path.join(download_dir, excel_filename)
            
            df.to_excel(excel_path, index=False)
        
        elif polymerization_method == 'random-copolymer':
            
            
            polymer_name = data.get('polymer_name')
            response_data['polymer_name'] = polymer_name

            
            table_data = data.get('table_data', [])
            if not table_data:
                return JsonResponse({'error': 'No data provided for random copolymer'}, status=400)

            
            for item in table_data:
                response_data['table_data'].append({
                    'Name': item.get('name'),
                    'SMILES': item.get('smiles'),
                    'repeating unit': item.get('repeating_unit_number')
                })

            
            df = pd.DataFrame(response_data['table_data'])
            
            df['copolymer_name'] = polymer_name
            df['is polymer'] = True
            
            excel_filename = 'copolymer_system.xlsx'
            
            excel_path = os.path.join(download_dir, excel_filename)
            
            df.to_excel(excel_path, index=False)

        elif polymerization_method == 'block-copolymer':
            
            
            polymer_name = data.get('polymer_name')
            number_of_blocks = data.get('number_of_blocks')
            response_data['polymer_name'] = polymer_name
            response_data['number_of_blocks'] = number_of_blocks

            
            table_data = data.get('table_data', [])
            if not table_data:
                return JsonResponse({'error': 'No data provided for block copolymer'}, status=400)

            
            for item in table_data:
                response_data['table_data'].append({
                    'Name': item.get('name'),
                    'SMILES': item.get('smiles'),
                    'repeating unit': item.get('repeating_unit_number')
                })

            
            df = pd.DataFrame(response_data['table_data'])
            
            df['copolymer_name'] = polymer_name
            df['Number of blocks'] = number_of_blocks
            df['is polymer'] = True
            
            excel_filename = 'copolymer_system.xlsx'
            
            excel_path = os.path.join(download_dir, excel_filename)
            
            df.to_excel(excel_path, index=False)

        else:
            
            return JsonResponse({'error': 'Invalid polymerization method'}, status=400)

        
        source_dir = os.path.join(settings.BASE_DIR, 'polymer', 'static', 'programe', 'predict_copolymer_property')
        for filename in os.listdir(source_dir):
            source_file = os.path.join(source_dir, filename)
            if os.path.isfile(source_file):
                shutil.copy(source_file, download_dir)
            elif os.path.isdir(source_file):
                shutil.copytree(source_file, os.path.join(download_dir, filename))

        
        notebooks_to_run = [
            '1_predict_copolymer_property.ipynb',
            ]

        
        for notebook_name in notebooks_to_run:
            notebook_path = os.path.join(download_dir, notebook_name)
            try:
                subprocess.run(
                    ["jupyter", "nbconvert", "--to", "notebook", "--execute",
                    "--output", notebook_path, notebook_path],
                    check=True, timeout=None, capture_output=True, text=True
                )

            except subprocess.CalledProcessError as e:
                
                error_message = f'Failed to run notebook: {str(e)}'
                stdout_output = e.stdout 
                stderr_output = e.stderr 
                traceback_str = traceback.format_exc()  
                return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
            
            except Exception as e:
                
                error_message = f'An error occurred: {str(e)}'
                traceback_str = traceback.format_exc()  
                return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)

        
        download_url = settings.MEDIA_URL + '/Polymer/polymer_predict/Downloads/' + unique_folder + '/copolymer_property_list.xlsx'

        
        return JsonResponse({'download_url': download_url})

    else:
        
        return HttpResponse("Invalid request method.")

@hybrid_login_required  
@csrf_exempt  
def generate_polymer(request):
    
    pid = os.getpid()

    if request.method == 'POST':
        
        try:
            data = json.loads(request.body)
            
        except json.JSONDecodeError as e:
            
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        
        polymerization_method = data.get('polymerization_method')

        
        polymer_topology = data.get('polymer_topology')

        if not polymerization_method:
            return JsonResponse({'error': 'Polymerization method is required'}, status=400)

        
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())[:6]}"

        
        download_dir = os.path.join(settings.MEDIA_ROOT, 'Polymer', 'GeneratePolymer', unique_folder)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        response_data = {
            'polymerization_method': polymerization_method,
            'table_data': [],
            'polymer_name': '',
            'number_of_blocks': ''
        }

        
        remote_target = REMOTE_POLYMER_GENERATE_TARGET

        
        if polymerization_method == 'homopolymer':
            
            
            table_data = data.get('table_data', [])
            if not table_data:
                return JsonResponse({'error': 'No data provided for homopolymer'}, status=400)

            
            for item in table_data:
                response_data['table_data'].append({
                    'Name': item.get('name'),
                    'SMILES': item.get('smiles'),
                    'repeating unit': item.get('repeating_unit_number')
                })

            
            df = pd.DataFrame(response_data['table_data'])
            
            excel_filename = 'System_homopolymer.xlsx'
            
            excel_path = os.path.join(download_dir, excel_filename)
            
            df.to_excel(excel_path, index=False)

            
            zip_download_url = os.path.join(settings.MEDIA_URL, 'Polymer/GeneratePolymer', unique_folder, 'all_results.zip')

            
            download_url = os.path.join(settings.MEDIA_URL, 'Polymer/GeneratePolymer', unique_folder, 'System_homopolymer.xlsx')

            
            download_url_list = [download_dir, zip_download_url, download_url]

            
            encrypted_id = encrypt_download_url_list(download_url_list)

            
            task = ComputeTask.objects.create(
                user=request.user,  
                task_type='Generate_homopolymer', 
                task_id=encrypted_id,  
                folder_path=download_dir,  
                status='pending',  
                pid=pid,  
            )

            
            if polymer_topology == "linear":
                source_dir = os.path.join(settings.BASE_DIR, 'polymer', 'static', 'programe', 'generate_homopolymer')
            elif polymer_topology == "cyclic":
                source_dir = os.path.join(settings.BASE_DIR, 'polymer', 'static', 'programe', 'generate_cyclic_homopolymer')

            
            response_data = {
                'encrypted_id': encrypted_id,
            }
            _enqueue_polymer_remote_task_for_scheduler(
                task=task,
                source_dir=source_dir,
                download_dir=download_dir,
                remote_target_subpath=remote_target,
            )

            
            return JsonResponse(response_data)
        
        elif polymerization_method == 'random-copolymer':
            
            
            polymer_name = data.get('polymer_name')
            response_data['polymer_name'] = polymer_name

            
            table_data = data.get('table_data', [])
            if not table_data:
                return JsonResponse({'error': 'No data provided for random copolymer'}, status=400)

            
            for item in table_data:
                response_data['table_data'].append({
                    'Name': item.get('name'),
                    'SMILES': item.get('smiles'),
                    'repeating unit': item.get('repeating_unit_number')
                })

            
            df = pd.DataFrame(response_data['table_data'])
            
            df['copolymer_name'] = polymer_name
            df['is polymer'] = True
            
            excel_filename = 'System_random_copolymer.xlsx'
            
            excel_path = os.path.join(download_dir, excel_filename)
            
            df.to_excel(excel_path, index=False)

            
            zip_download_url = os.path.join(settings.MEDIA_URL, 'Polymer/GeneratePolymer', unique_folder, 'all_results.zip')

            
            download_url = os.path.join(settings.MEDIA_URL, 'Polymer/GeneratePolymer', unique_folder, 'System_random_copolymer.xlsx')

            
            download_url_list = [download_dir, zip_download_url, download_url]

            
            encrypted_id = encrypt_download_url_list(download_url_list)

            
            task = ComputeTask.objects.create(
                user=request.user,  
                task_type='Generate_random_copolymer', 
                task_id=encrypted_id,  
                folder_path=download_dir,  
                status='pending',  
                pid=pid,  
            )

            
            if polymer_topology == "linear":
                source_dir = os.path.join(settings.BASE_DIR, 'polymer', 'static', 'programe', 'generate_random_copolymer')
            elif polymer_topology == "cyclic":
                source_dir = os.path.join(settings.BASE_DIR, 'polymer', 'static', 'programe', 'generate_cyclic_random_copolymer')
            
            
            response_data = {
                'encrypted_id': encrypted_id,
            }

            _enqueue_polymer_remote_task_for_scheduler(
                task=task,
                source_dir=source_dir,
                download_dir=download_dir,
                remote_target_subpath=remote_target,
            )

            
            return JsonResponse(response_data)

        elif polymerization_method == 'block-copolymer':
            
            
            polymer_name = data.get('polymer_name')
            number_of_blocks = data.get('number_of_blocks')
            response_data['polymer_name'] = polymer_name
            response_data['number_of_blocks'] = number_of_blocks

            
            table_data = data.get('table_data', [])
            if not table_data:
                return JsonResponse({'error': 'No data provided for block copolymer'}, status=400)

            
            for item in table_data:
                response_data['table_data'].append({
                    'Name': item.get('name'),
                    'SMILES': item.get('smiles'),
                    'repeating unit': item.get('repeating_unit_number')
                })

            
            df = pd.DataFrame(response_data['table_data'])
            
            df['copolymer_name'] = polymer_name
            df['Number of blocks'] = number_of_blocks
            df['is polymer'] = True
            
            excel_filename = 'System_block_copolymer.xlsx'
            
            excel_path = os.path.join(download_dir, excel_filename)
            
            df.to_excel(excel_path, index=False)

            
            zip_download_url = os.path.join(settings.MEDIA_URL, 'Polymer/GeneratePolymer', unique_folder, 'all_results.zip')

            
            download_url = os.path.join(settings.MEDIA_URL, 'Polymer/GeneratePolymer', unique_folder, 'System_block_copolymer.xlsx')

            
            download_url_list = [download_dir, zip_download_url, download_url]

            
            encrypted_id = encrypt_download_url_list(download_url_list)

            
            task = ComputeTask.objects.create(
                user=request.user,  
                task_type='Generate_block_copolymer', 
                task_id=encrypted_id,  
                folder_path=download_dir,  
                status='pending',  
                pid=pid,  
            )

            
            if polymer_topology == "linear":
                source_dir = os.path.join(settings.BASE_DIR, 'polymer', 'static', 'programe', 'generate_block_copolymer')
            elif polymer_topology == "cyclic":
                source_dir = os.path.join(settings.BASE_DIR, 'polymer', 'static', 'programe', 'generate_cyclic_block_copolymer')
            
            
            response_data = {
                'encrypted_id': encrypted_id,
            }

            _enqueue_polymer_remote_task_for_scheduler(
                task=task,
                source_dir=source_dir,
                download_dir=download_dir,
                remote_target_subpath=remote_target,
            )

            
            return JsonResponse(response_data)
        else:
            
            return JsonResponse({'error': 'Invalid polymerization method'}, status=400)

    else:
        
        return HttpResponse("Invalid request method.")


def polymer_structure_visualization_upload(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')

        if not uploaded_file:
            
            error_message = "No file uploaded."
            return render(request, 'visualization_structure.html', {'error_message': error_message})

        else:
            
            
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            unique_folder = f"{current_time}_{str(uuid.uuid4())}"

            
            upload_folder = os.path.join(settings.MEDIA_ROOT, 'Polymer/visualization_polymer_structure', unique_folder)
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            fs = FileSystemStorage(location=upload_folder)

            
            filename = fs.save(uploaded_file.name, uploaded_file)

            
            file_path = os.path.join(upload_folder, filename)

            
            file_url = fs.url(os.path.join('Polymer/visualization_polymer_structure', unique_folder, filename))

            success_message = "File uploaded successfully."

            
            context = {
                'success_message': success_message,
                'file_url': file_url,
            }

            logger.info(f"polymer_structure_visualization_upload : {context}")

            return render(request, 'visualization_structure.html', context)

    else:
        return render(request, 'visualization_structure.html')

@csrf_exempt  
def upload_excel_polymer_predict_file_view(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']  

            
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')

            
            unique_folder = f"{current_time}_{str(uuid.uuid4())}"
            
            
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'Polymer/polymer_predict/Uploads', unique_folder)
            
            
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            
            file_path = os.path.join(upload_dir, 'polymer_list.xlsx')
            
            
            with open(file_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)
            
            
            return JsonResponse({
                'file_path': os.path.join(settings.MEDIA_URL, 'Polymer/polymer_predict/Uploads', unique_folder, 'polymer_list.xlsx')
            })
        else:
            return JsonResponse({'error': 'No file provided'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def process_polymer_predict_view(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        
        excel_file = request.FILES['excel_file']
        
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            error_message = f"Failed to read Excel file: {str(e)}"
            traceback_str = traceback.format_exc()
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)

        
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(settings.MEDIA_ROOT, 'Polymer/polymer_predict/Downloads', unique_folder)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, 'polymer_list.xlsx')
        try:
            df.to_excel(processed_excel_path, index=False)
        except Exception as e:
            error_message = f"Failed to save Excel file: {str(e)}"
            traceback_str = traceback.format_exc()
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)

        
        source_dir = os.path.join(settings.BASE_DIR, 'polymer', 'static', 'programe', 'predict_polymer_properties')
        for filename in os.listdir(source_dir):
            source_file = os.path.join(source_dir, filename)
            if os.path.isfile(source_file):
                shutil.copy(source_file, download_dir)
            elif os.path.isdir(source_file):
                shutil.copytree(source_file, os.path.join(download_dir, filename))

        
        notebooks_to_run = [
            'predict_polymer_property.ipynb',
            ]

        
        for notebook_name in notebooks_to_run:
            notebook_path = os.path.join(download_dir, notebook_name)
            try:
                subprocess.run(
                    ["jupyter", "nbconvert", "--to", "notebook", "--execute",
                    "--output", notebook_path, notebook_path],
                    check=True, timeout=None, capture_output=True, text=True
                )

            except subprocess.CalledProcessError as e:
                
                error_message = f'Failed to run notebook: {str(e)}'
                stdout_output = e.stdout 
                stderr_output = e.stderr 
                traceback_str = traceback.format_exc()  
                return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
            
            except Exception as e:
                
                error_message = f'An error occurred: {str(e)}'
                traceback_str = traceback.format_exc()  
                return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)

        
        download_url = settings.MEDIA_URL + '/Polymer/polymer_predict/Downloads/' + unique_folder + '/polymer_list.xlsx'

        
        return JsonResponse({'download_url': download_url}) 
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def polymer_frontend_spa(request):
    from django.http import FileResponse
    import os
    
    index_path = os.path.join(settings.BASE_DIR, 'polymer', 'dist', 'index.html')
    
    if not os.path.exists(index_path):
        raise Http404("前端build文件未找到，请先运行 npm run build")
    
    return FileResponse(
        open(index_path, 'rb'),
        content_type='text/html; charset=utf-8'
    )

from django.http import JsonResponse
import json
@csrf_exempt
def api_similarity_search(request):
    """API endpoint for molecular similarity search"""
    if request.method == 'OPTIONS':
        return HttpResponse()
    print(request.method)
    if request.method == 'POST':
        try:
            import sys
            import os
            
            
            test_box_path = os.path.join(os.path.dirname(__file__), 'test_box')
            sys.path.append(test_box_path)
            
            
            from polymer.test_box.query_similar_monomer.query_utils import topk_similar_smiles, load_morgan_fp_data_list
            
            data = json.loads(request.body)
            query_smiles = data.get('smiles', '')
            topk = int(data.get('topk', 10))
            method = data.get('method', 'tanimoto')
            radius = int(data.get('radius', 2))
            n_bits = int(data.get('n_bits', 2048))
            
            
            fp_data_path = os.path.join(test_box_path, 'query_similar_monomer', 'smiles_morgan_fp_r2_n2048.json.gz')
            print("fp_data_path loaded!")
            if os.path.exists(fp_data_path):
                data_list = load_morgan_fp_data_list(fp_data_path)
                results = topk_similar_smiles(
                    query_smiles=query_smiles,
                    data_list=data_list,
                    topk=topk,
                    method=method,
                    radius=radius,
                    n_bits=n_bits
                )
                print(results)
                response = JsonResponse({'results': results, 'status': 'success'})
                response['Access-Control-Allow-Origin'] = '*'
                return response
            else:
                return JsonResponse({'error': 'Fingerprint database not found'}, status=404)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

from django.views.decorators.http import require_http_methods
def validate_smiles(smiles_str):
    """Return True if RDKit can parse the SMILES string."""
    return Chem.MolFromSmiles(smiles_str) is not None

def is_molecular_formula(smiles_str):
    """Return True if string matches a molecular formula pattern."""
    return bool(MOLFORMULA_PATTERN.fullmatch(smiles_str.strip()))

@csrf_exempt
@require_http_methods(["POST"])
def polymerization_prediction(request):
    """
    API endpoint for polymer prediction
    input : monomers list
    """
    print("polymerization function called")
    try:
        data = json.loads(request.body or '{}')
        monomers = data.get('monomers', []) 

        if len(monomers) < 2:
            return JsonResponse({'error': 'At least 2 monomers required'}, status=400)

        valid_monomers = []
        invalid_entries = []

        for i, monomer in enumerate(monomers):
            
            
            smiles = (monomer.get('SMILES') or monomer.get('smiles') or '').strip()
            name = monomer.get('Name') or monomer.get('name') or f'Monomer {len(valid_monomers)+1}'
            valid_monomers.append({
                'SMILES': smiles,
                'Name': name
            })
        
        if invalid_entries:
            return JsonResponse({
                'error': 'Invalid SMILES detected',
                'details': invalid_entries,
                'hint': 'SMILES format examples: "c1ccc(N)cc1" (aniline), "O=C(O)CCO" (3-hydroxypropionic acid)'
            }, status=400)

        if len(valid_monomers) < 2:
            return JsonResponse({'error': 'At least 2 valid monomers required after validation'}, status=400)
        
        df = pd.DataFrame(valid_monomers)

        try:
            
            classified_df = monc.moncls(df, smiColn="SMILES")
        except Exception as e:
            return JsonResponse({
                'error': 'Failed to classify monomers',
                'details': str(e),
                'hint': 'Please check if the SMILES are valid organic molecules suitable for polymerization'
            }, status=400)

        classified_df = classified_df.iloc[:-2]

        
        try:
            polymer_df = polg.biplym(classified_df)
        except Exception as e:
            return JsonResponse({
                'error': 'Failed to generate polymers',
                'details': str(e),
                'hint': 'The classified monomers might not be suitable for the supported polymerization reactions'
            }, status=400)

        results = []
        for _, row in polymer_df.iterrows():
            result = {
                'monomer1': row.get('monomer1_smiles', ''),
                'monomer2': row.get('monomer2_smiles', ''),
                'polymer_smiles': row.get('polymer_smiles', ''),
                'reaction_type': row.get('reaction_type', 'Unknown')
            }
            
            for col in polymer_df.columns:
                if col not in ['monomer1_smiles', 'monomer2_smiles', 'polymer_smiles', 'reaction_type']:
                    result[col] = row.get(col, '')
                    
            results.append(result)
        print(results)
        return JsonResponse({
            'results': results,
            'total_polymers': len(results),
            'classified_monomers': len(classified_df),
            'input_monomers': len(valid_monomers)
        }, status=200)
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

from pathlib import Path
import mimetypes
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse

DIST_DIR = Path(settings.BASE_DIR) / 'polymer' / 'dist'
ASSETS_DIR = DIST_DIR / 'assets'

def analysis_index(request):
    index_path = DIST_DIR / 'index.html'
    if not index_path.exists():
        return HttpResponse("Build not found. Run `npm run build`.", status=404)
    return FileResponse(open(index_path, 'rb'), content_type='text/html; charset=utf-8')

def analysis_assets(request, path: str):
    file_path = (ASSETS_DIR / path).resolve()
    if not str(file_path).startswith(str(ASSETS_DIR.resolve())):
        raise Http404
    if not file_path.is_file():
        raise Http404

    ctype, _ = mimetypes.guess_type(str(file_path))
    resp = FileResponse(open(file_path, 'rb'), content_type=ctype or 'application/octet-stream')
    
    resp['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resp

def analysis_static(request, filename: str):
    
    allowed_files = {
        'RDKit_minimal.js',
        'RDKit_minimal.wasm',
        'monomer_template.csv',
        'polymerization_prediction_template.csv',
        'polymer_prediction_template.xlsx',
        'property_prediction_template.xlsx'
    }

    if filename not in allowed_files:
        raise Http404(f"File '{filename}' not allowed")

    file_path = (DIST_DIR / filename).resolve()

    
    if not str(file_path).startswith(str(DIST_DIR.resolve())):
        raise Http404("Invalid path")

    if not file_path.is_file():
        raise Http404(f"File '{filename}' not found")

    
    ctype, _ = mimetypes.guess_type(str(file_path))
    if filename.endswith('.wasm'):
        ctype = 'application/wasm'

    resp = FileResponse(
        open(file_path, 'rb'),
        content_type=ctype or 'application/octet-stream'
    )

    
    if filename.endswith(('.js', '.wasm')):
        resp['Cache-Control'] = 'public, max-age=31536000, immutable'
    else:
        
        resp['Cache-Control'] = 'no-cache'

    return resp


from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

@login_required
@premium_permission_required
def api_experiment_polymer_data(request):
    """
    REST API for Experiment Polymer Database with pagination, search, and sorting
    """
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    if request.method == 'GET':
        try:
            
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            search = request.GET.get('search', '').strip()
            sort_field = request.GET.get('sort_field', 'id')
            sort_order = request.GET.get('sort_order', 'asc')

            
            queryset = experiment_polymer_data.objects.all()

            
            if search:
                
                queryset = queryset.filter(
                    Q(Name__icontains=search) |
                    Q(PSMILES__icontains=search) |
                    Q(Reference__icontains=search)
                )

            
            if sort_order == 'desc':
                sort_field = f'-{sort_field}'

            
            valid_fields = [f.name for f in experiment_polymer_data._meta.get_fields()]
            if sort_field.lstrip('-') in valid_fields:
                queryset = queryset.order_by(sort_field)

            
            total_count = queryset.count()

            
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)

            
            fields = experiment_polymer_data._meta.get_fields()
            field_names = [f.name for f in fields]
            field_verbose_names = {}
            field_types = {}

            for field in fields:
                field_verbose_names[field.name] = getattr(field, 'verbose_name', field.name)
                field_types[field.name] = field.get_internal_type()

            
            data = []
            for obj in page_obj:
                item = {}
                for field_name in field_names:
                    value = getattr(obj, field_name)
                    
                    item[field_name] = value if value is not None else ''
                data.append(item)

            response_data = {
                'success': True,
                'data': data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                },
                'meta': {
                    'field_names': field_names,
                    'field_verbose_names': field_verbose_names,
                    'field_types': field_types,
                    'searchable_fields': ['Name', 'PSMILES', 'Reference'],
                    'sortable_fields': field_names,
                }
            }

            response = JsonResponse(response_data)
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as e:
            response = JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
            response['Access-Control-Allow-Origin'] = '*'
            return response

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_public_experiment_polymer_data(request):
    """
    Public REST API for Experiment Polymer Database
    No authentication required for read-only access
    """
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    if request.method == 'GET':
        try:
            
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            search = request.GET.get('search', '').strip()
            sort_field = request.GET.get('sort_field', 'id')
            sort_order = request.GET.get('sort_order', 'asc')

            
            queryset = experiment_polymer_data.objects.all()

            
            if search:
                queryset = queryset.filter(
                    Q(Name__icontains=search) |
                    Q(PSMILES__icontains=search) |
                    Q(Reference__icontains=search)
                )

            
            if sort_order == 'desc':
                sort_field = f'-{sort_field}'

            
            valid_fields = [f.name for f in experiment_polymer_data._meta.get_fields()]
            if sort_field.lstrip('-') in valid_fields:
                queryset = queryset.order_by(sort_field)

            
            total_count = queryset.count()

            
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)

            
            fields = experiment_polymer_data._meta.get_fields()
            field_names = [f.name for f in fields]

            
            data = []
            for obj in page_obj:
                item = {}
                for field_name in field_names:
                    value = getattr(obj, field_name)
                    
                    item[field_name] = value if value is not None else ''
                data.append(item)

            response_data = {
                'success': True,
                'data': data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                },
                'meta': {
                    'field_names': field_names,
                    'searchable_fields': ['Name', 'PSMILES', 'Reference'],
                    'sortable_fields': field_names,
                }
            }

            response = JsonResponse(response_data)
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as e:
            response = JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
            response['Access-Control-Allow-Origin'] = '*'
            return response

    response = JsonResponse({'error': 'Method not allowed'}, status=405)
    response['Access-Control-Allow-Origin'] = '*'
    return response


@csrf_exempt
def api_public_calculated_polymer_data(request):
    """
    Public REST API for Calculated Polymer Database
    No authentication required for read-only access
    """
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    if request.method == 'GET':
        try:
            
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            search = request.GET.get('search', '').strip()
            sort_field = request.GET.get('sort_field', 'id')
            sort_order = request.GET.get('sort_order', 'asc')

            
            queryset = calculated_polymer_data.objects.all()

            
            if search:
                queryset = queryset.filter(
                    Q(Name__icontains=search) |
                    Q(psmiles__icontains=search) |
                    Q(SMILES__icontains=search) |
                    Q(reactant_1__icontains=search) |
                    Q(reactant_2__icontains=search) |
                    Q(reaction_type__icontains=search)
                )

            
            if sort_order == 'desc':
                sort_field = f'-{sort_field}'

            
            valid_fields = [f.name for f in calculated_polymer_data._meta.get_fields()]
            if sort_field.lstrip('-') in valid_fields:
                queryset = queryset.order_by(sort_field)

            
            total_count = queryset.count()

            
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)

            
            fields = calculated_polymer_data._meta.get_fields()
            field_names = [f.name for f in fields]

            
            data = []
            for obj in page_obj:
                item = {}
                for field_name in field_names:
                    value = getattr(obj, field_name)
                    
                    item[field_name] = value if value is not None else ''
                data.append(item)

            response_data = {
                'success': True,
                'data': data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                },
                'meta': {
                    'field_names': field_names,
                    'searchable_fields': ['Name', 'psmiles', 'SMILES', 'reactant_1', 'reactant_2', 'reaction_type'],
                    'sortable_fields': field_names,
                }
            }

            response = JsonResponse(response_data)
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as e:
            response = JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
            response['Access-Control-Allow-Origin'] = '*'
            return response

    response = JsonResponse({'error': 'Method not allowed'}, status=405)
    response['Access-Control-Allow-Origin'] = '*'
    return response


@csrf_exempt
def api_public_calculated_monomer_data(request):
    """
    Public REST API for Calculated Monomer Database
    No authentication required for read-only access
    """
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    if request.method == 'GET':
        try:
            
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            search = request.GET.get('search', '').strip()
            sort_field = request.GET.get('sort_field', 'id')
            sort_order = request.GET.get('sort_order', 'asc')

            
            queryset = calculated_monomer_data.objects.all()

            
            if search:
                queryset = queryset.filter(
                    Q(Name__icontains=search) |
                    Q(SMILES__icontains=search) |
                    Q(Monomer_Type__icontains=search) |
                    Q(Software__icontains=search)
                )

            
            if sort_order == 'desc':
                sort_field = f'-{sort_field}'

            
            valid_fields = [f.name for f in calculated_monomer_data._meta.get_fields()]
            if sort_field.lstrip('-') in valid_fields:
                queryset = queryset.order_by(sort_field)

            
            total_count = queryset.count()

            
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)

            
            fields = calculated_monomer_data._meta.get_fields()
            field_names = [f.name for f in fields]

            
            data = []
            for obj in page_obj:
                item = {}
                for field_name in field_names:
                    value = getattr(obj, field_name)
                    
                    item[field_name] = value if value is not None else ''
                data.append(item)

            response_data = {
                'success': True,
                'data': data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': paginator.num_pages,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                },
                'meta': {
                    'field_names': field_names,
                    'searchable_fields': ['Name', 'SMILES', 'Monomer_Type', 'Software'],
                    'sortable_fields': field_names,
                }
            }

            response = JsonResponse(response_data)
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as e:
            response = JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
            response['Access-Control-Allow-Origin'] = '*'
            return response

    response = JsonResponse({'error': 'Method not allowed'}, status=405)
    response['Access-Control-Allow-Origin'] = '*'
    return response

DATABASE_EXPORT_FILES = {
    'experiment_polymer_data': 'experiment_polymer_data.xlsx',
    'calculated_monomer_data': 'calculated_monomer_data.xlsx',
    'calculated_polymer_data': 'calculated_polymer_data.xlsx',
}


def _build_export_file_response(filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'Polymer', 'Database_full', filename)
    if not os.path.exists(file_path):
        return None

    response = FileResponse(
        open(file_path, 'rb'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response



@csrf_exempt
def download_database_export(request, database_name):
    filename = DATABASE_EXPORT_FILES.get(database_name)
    if not filename:
        return JsonResponse({'error': 'Invalid database name'}, status=400)

    response = _build_export_file_response(filename)
    if response is None:
        return JsonResponse({
            'error': 'Export file not found. Please run update_database_exports.py first'
        }, status=404)

    return response


@csrf_exempt
def download_database_export_file(request, filename):
    if filename not in DATABASE_EXPORT_FILES.values():
        raise Http404("File not allowed")

    response = _build_export_file_response(filename)
    if response is None:
        raise Http404("Export file not found. Please run update_database_exports.py first")

    return response
