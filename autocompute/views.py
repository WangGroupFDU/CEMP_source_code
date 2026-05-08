from django.shortcuts import render
from django.http import JsonResponse, Http404  
import os
from django.conf import settings  

from ionic_liquid.models import metal_anion_energy, Example
from ionic_liquid.models import IL, Cation, Anion
from ionic_liquid.models import Li_electrolyte, electrolyte
from autocompute.models import (
    ComputationTask,
)  

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


from register.decorators import hybrid_login_required
from threading import Thread
from cryptography.fernet import Fernet  
import json
from autocompute.models import ComputeTask  
from django.core.paginator import Paginator
import subprocess, sys
import shlex  
import posixpath  
import traceback  


from rest_framework import generics
from autocompute.serializers import (
    ElectrolyteSerializer,
    Metal_Anion_EnergySerializer,
    ILSerializer,
    CationSerializer,
    Li_ElectrolyteSerializer,
    AnionSerializer,
)
from rest_framework.permissions import (
    IsAuthenticated,
)  
import re
from autocompute.utils import (
    validate_HTQC_single_point_energy_df,
    validate_HTQC_binding_energy_df,
    validate_HTQC_pka_pkb_df,
    validate_MD_system_df,
)
from autocompute.utils import from_smiles_get_iupac_name, get_safe_name
from autocompute.remote_utils import persist_remote_dispatch_request
import mimetypes
from urllib.parse import unquote_plus  
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import io
import re, subprocess, textwrap


from django.utils.text import get_valid_filename  
from register.decorators import hybrid_login_required



from autocompute.utils import (
    extract_energy_from_out,
    extract_dipole_moment,
    extract_homo_lumo,
    extract_entropy,
    extract_enthalpy_correction,
    extract_gibbs_correction,
    get_conjugate_acid_base,
    convert_chk_to_fchk,
    convert_gbw_to_molden,
    can_submit_today,
)

from autocompute.utils import (
    create_result_excel,
    extract_coordinates,
    create_ORCA_opt_inputfile,
    create_ORCA_energy_inputfile,
    get_authenticated_user,
)  
from autocompute.utils import (
    batch_generate_esp_cub,
    generate_esp_vmd,
    render_esp_with_vmd,
)  
from autocompute.run_MD_QC_utils import (
    run_Gaussian_single_point_energy_notebook_tasks,
    run_ORCA_single_point_energy_notebook_tasks,
    run_Gaussian_binding_energy_notebook_tasks,
    run_ORCA_binding_energy_notebook_tasks,
    run_Gaussian_pka_pkb_notebook_tasks,
    run_Gaussian_ox_red_notebook_tasks,
    run_ORCA_ox_red_notebook_tasks,
    run_Gaussian_reaction_thermo_notebook_tasks,
    run_Gaussian_global_reaction_properties_notebook_tasks,
    run_ORCA_manual_notebook_tasks,
    run_Gromacs_MD_notebook_tasks,
    run_Gromacs_MD_notebook_tasks_ORCA,
    check_and_execute_task,  
    run_task_immediately,  
    run_draw_ESP_notebook_tasks,
    run_draw_ESP_notebook_tasks_gbw,
)

from register.decorators import (
    auto_compute_permission_required,
    premium_permission_required,
    ml_prediction_permission_required,
    gaussian_permission_required,
    email_in_valid_domains,
)

import logging

logger = logging.getLogger("django")

from django.http import JsonResponse, HttpResponseForbidden
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect



cipher_suite = Fernet(settings.FERNET_SECRET_KEY)

REMOTE_QC_DOWNLOADS_TARGET = posixpath.join("AutoCompute", "QcCompute", "Downloads")
REMOTE_MD_DOWNLOADS_TARGET = posixpath.join("AutoCompute", "MDCompute", "Downloads")
REMOTE_MARKOV_DOWNLOADS_TARGET = posixpath.join("AutoCompute", "MarkovAnalysis", "Downloads")


def _prepare_task_for_remote_dispatch(task: ComputeTask) -> None:

    task.remote_type = "remote"
    task.status = "queuing"
    task.server_name = None
    task.pid = None
    task.save(update_fields=["remote_type", "status", "server_name", "pid"])


def _build_remote_management_command(
    task: ComputeTask,
    source_dir: str,
    download_dir: str,
    func_path: str,
    remote_target_subpath: str,
    immediate: bool = False,
) -> list:

    command_name = (
        "new_execute_task_immediate_remote"
        if immediate
        else "new_execute_long_task_generic_remote"
    )
    return [
        sys.executable,
        os.path.join(settings.BASE_DIR, "manage.py"),
        command_name,
        str(task.task_id),
        source_dir,
        download_dir,
        func_path,
        remote_target_subpath,
    ]    


def _enqueue_remote_task_for_scheduler(
    task: ComputeTask,
    *,
    source_dir: str,
    download_dir: str,
    func_path: str,
    remote_target_subpath: str,
) -> None:

    _prepare_task_for_remote_dispatch(task)
    persist_remote_dispatch_request(
        task,
        source_dir=source_dir,
        download_dir=download_dir,
        func_path=func_path,
        remote_target_subpath=remote_target_subpath,
    )
    if task.pid is not None:
        task.pid = None
        task.save(update_fields=["pid"])



def encrypt_download_url_list(download_url_list):
    
    url_list_str = json.dumps(download_url_list)

    
    encrypted = cipher_suite.encrypt(url_list_str.encode("utf-8"))

    
    return encrypted.decode("utf-8")



def decrypt_download_url_list(encrypted_id):
    try:
        
        decrypted = cipher_suite.decrypt(encrypted_id.encode("utf-8"))

        
        download_url_list = json.loads(decrypted.decode("utf-8"))

        return download_url_list
    except Exception as e:
        
        print(f"解密失败: {str(e)}")
        return None



def get_molecule_file(request):
    
    component_name = request.GET.get("component_name")

    
    if not component_name:
        raise Http404("Component name not provided.")

    
    file_path = f"/data/Gaussian_database/opt+freq/{component_name}.out"

    
    if not os.path.exists(file_path):
        raise Http404("File not found.")

    
    with open(file_path, "rb") as f:
        file_data = f.read()  

    
    mime_type, _ = mimetypes.guess_type(file_path)

    
    if not mime_type:
        mime_type = "application/octet-stream"

    
    response = HttpResponse(file_data, content_type=mime_type)

    
    response["Content-Disposition"] = f'inline; filename="{component_name}.out"'

    
    return response



def index(request):
    return render(request, "autocompute/home.html")



def SMILESDrawer(request):
    return render(request, "autocompute/SMILESDrawer/SMILESDrawer.htm")



def Visualization(request):
    return render(request, "autocompute/visualization/visualization.html")



def MDVisualization(request):
    return render(request, "autocompute/mdCompute/mdcompute_visualization.html")



@login_required
@premium_permission_required
def database(request):
    return render(request, "autocompute/database/database_display_base.html")



@login_required
@email_in_valid_domains
def QCcompute_base(request):
    context = {
        "gaussian_permssion": request.user.userprofile.gaussian_permission,
    }
    return render(request, "autocompute/qcCompute/QCcompute_base.html", context)




def HTQC_single_point(request):
    context = {
        "gaussian_permission": request.user.userprofile.gaussian_permission,
    }
    return render(
        request, "autocompute/qcCompute/HTQC_single_point_byurl.html", context
    )



def HTQC_binding_energy(request):
    context = {
        "gaussian_permission": request.user.userprofile.gaussian_permission,
    }
    return render(
        request, "autocompute/qcCompute/HTQC_binding_energy_byurl.html", context
    )


@auto_compute_permission_required
@gaussian_permission_required
def HTQC_pka_pkb(request):
    return render(request, "autocompute/qcCompute/HTQC_pka_pkb_byurl.html")



def HTQC_ox_red(request):
    context = {
        "gaussian_permission": request.user.userprofile.gaussian_permission,
    }
    return render(request, "autocompute/qcCompute/HTQC_ox_red_byurl.html", context)



@auto_compute_permission_required
@gaussian_permission_required
def HTQC_reaction_thermo(request):
    return render(request, "autocompute/qcCompute/HTQC_reaction_thermo_byurl.html")



@auto_compute_permission_required
@gaussian_permission_required
def HTQC_global_reaction_properties(request):
    return render(request, "autocompute/qcCompute/HTQC_global_reaction_properties.html")



@login_required

def mdcompute(request):
    context = {
        "gaussian_permission": request.user.userprofile.gaussian_permission,
    }
    return render(request, "autocompute/mdCompute/mdcompute_base_byurl.html", context)



def from_smiles_get_name_page(request):
    
    return render(request, "autocompute/from_smiles_get_name/from_smiles_get_name.html")



def transfer_tool_page_view(request):
    
    return render(request, "autocompute/qcCompute/Transfer_tool_page.html")


def jsmol_test(request):
    
    return render(request, "autocompute/qcCompute/test_jsmol.html")



@login_required
@premium_permission_required
def render_metal_anion_energy_view(request):
    selected_crystal = request.GET.get("crystal")  
    excluded_fields = ["id", "author", "Author"]  
    field_names = metal_anion_energy._meta.get_fields()
    
    field_names_verbose = [
        f.name
        for f in field_names
        if not (f.name in excluded_fields or isinstance(f, metal_anion_energy))
    ]
    
    
    
    data = [
        [getattr(instance, name) for name in field_names_verbose]
        for instance in metal_anion_energy.objects.all()
    ]

    dict = {
        "field_names": field_names_verbose,
        "data": data,  
        "image_extensions": ["jpg", "jpeg", "png", "gif"],
        "file_extensions": ["txt", "csv", "CSV", "pdf"],
    }
    return render(request, "autocompute/database/metal_anion_energy.html", dict)







def example_view(request):
    excluded_fields = ["id", "author", "Author"]  
    fields = Example._meta.get_fields()  
    
    field_names_verbose = [f.name for f in fields if not (f.name in excluded_fields)]
    
    
    data = [
        [getattr(instance, name) for name in field_names_verbose]
        for instance in Example.objects.all()
    ]

    dict = {
        "field_names": field_names_verbose,
        "data": data,  
        "image_extensions": ["jpg", "jpeg", "png", "gif"],
        "file_extensions": ["txt", "csv", "CSV", "pdf"],
    }
    return render(request, "autocompute/database/example.html", dict)



@premium_permission_required
def Cation_view(request):
    fields = Cation._meta.get_fields()  
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [
        [getattr(instance, name) for name in field_names_verbose]
        for instance in Cation.objects.all()
    ]

    dict = {
        "field_names": field_names_verbose,
        "data": data,  
        "image_extensions": ["jpg", "jpeg", "png", "gif"],
        "file_extensions": ["txt", "csv", "CSV", "pdf"],
    }
    return render(request, "autocompute/database/Cation.html", dict)



@premium_permission_required
def Anion_view(request):
    fields = Anion._meta.get_fields()  
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [
        [getattr(instance, name) for name in field_names_verbose]
        for instance in Anion.objects.all()
    ]

    dict = {
        "field_names": field_names_verbose,
        "data": data,  
        "image_extensions": ["jpg", "jpeg", "png", "gif"],
        "file_extensions": ["txt", "csv", "CSV", "pdf"],
    }
    return render(request, "autocompute/database/Anion.html", dict)



@premium_permission_required
def IL_view(request):
    fields = IL._meta.get_fields()  
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [
        [getattr(instance, name) for name in field_names_verbose]
        for instance in IL.objects.all()
    ]

    dict = {
        "field_names": field_names_verbose,
        "data": data,  
        "image_extensions": ["jpg", "jpeg", "png", "gif"],
        "file_extensions": ["txt", "csv", "CSV", "pdf"],
    }
    return render(request, "autocompute/database/IL.html", dict)



@premium_permission_required
def electrolyte_view_paging(request):
    
    per_page = 200
    page_number = request.GET.get("page", 1)  

    
    fields = electrolyte._meta.get_fields()
    field_names_verbose = [f.name for f in fields]
    
    data = [
        [getattr(instance, name) for name in field_names_verbose]
        for instance in electrolyte.objects.all()
    ]

    
    paginator = Paginator(data, per_page)
    page_obj = paginator.get_page(page_number)

    dict = {
        "field_names": field_names_verbose,
        "data": page_obj.object_list,  
        "has_next": page_obj.has_next(),  
        "page_number": page_number,  
    }

    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(dict)  

    
    return render(request, "autocompute/database/electrolyte_paging_test.html", dict)



@premium_permission_required
def Li_electrolyte_view_paging(request):
    
    per_page = 200
    page_number = request.GET.get("page", 1)  

    
    fields = Li_electrolyte._meta.get_fields()
    field_names_verbose = [f.name for f in fields]
    data = [
        [getattr(instance, name) for name in field_names_verbose]
        for instance in Li_electrolyte.objects.all()
    ]

    
    paginator = Paginator(data, per_page)
    page_obj = paginator.get_page(page_number)

    dict = {
        "field_names": field_names_verbose,
        "data": page_obj.object_list,  
        "has_next": page_obj.has_next(),  
        "page_number": page_number,  
    }

    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(dict)  

    
    return render(request, "autocompute/database/Li_electrolyte_paging.html", dict)



@premium_permission_required
def Li_electrolyte_view(request):
    fields = Li_electrolyte._meta.get_fields()  
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [
        [getattr(instance, name) for name in field_names_verbose]
        for instance in Li_electrolyte.objects.all()
    ]

    dict = {
        "field_names": field_names_verbose,
        "data": data,  
        "image_extensions": ["jpg", "jpeg", "png", "gif"],
        "file_extensions": ["txt", "csv", "CSV", "pdf"],
    }
    return render(request, "autocompute/database/Li_electrolyte.html", dict)





@csrf_exempt  
@login_required(login_url="/register/login/")
def upload_excel_QcCoumpute_HTQC_single_point_energy(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        excel_file = request.FILES["excel_file"]  

        
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            return JsonResponse(
                {"error": f"Error reading Excel file: {str(e)}"}, status=400
            )

        
        validation_result = validate_HTQC_single_point_energy_df(df)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        upload_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Uploads", unique_folder
        )

        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        
        file_path = os.path.join(upload_dir, "HTQC.xlsx")

        
        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        
        return JsonResponse(
            {
                "file_path": os.path.join(
                    settings.MEDIA_URL,
                    "AutoCompute/QcCompute/Uploads",
                    unique_folder,
                    "HTQC.xlsx",
                ),
                "validation_result": validation_result,  
            }
        )

    
    return JsonResponse({"error": "File not uploaded"}, status=400)


@csrf_exempt  
@hybrid_login_required  
def upload_excel_QcCoumpute_HTQC_binding_energy(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        excel_file = request.FILES["excel_file"]  

        
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            return JsonResponse(
                {"error": f"Error reading Excel file: {str(e)}"}, status=400
            )

        
        validation_result = validate_HTQC_binding_energy_df(df)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        upload_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Uploads", unique_folder
        )

        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        
        file_path = os.path.join(upload_dir, "Dimer.xlsx")

        
        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        
        return JsonResponse(
            {
                "file_path": os.path.join(
                    settings.MEDIA_URL,
                    "AutoCompute/QcCompute/Uploads",
                    unique_folder,
                    "Dimer.xlsx",
                ),
                "validation_result": validation_result,  
            }
        )

    
    return JsonResponse({"error": "File not uploaded"}, status=400)


@csrf_exempt  
def upload_excel_QcCoumpute_HTQC_ox_red(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        excel_file = request.FILES["excel_file"]  

        
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            return JsonResponse(
                {"error": f"Error reading Excel file: {str(e)}"}, status=400
            )

        
        validation_result = validate_HTQC_single_point_energy_df(df)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        upload_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Uploads", unique_folder
        )

        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        
        file_path = os.path.join(upload_dir, "HTQC_ox_red.xlsx")

        
        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        
        return JsonResponse(
            {
                "file_path": os.path.join(
                    settings.MEDIA_URL,
                    "AutoCompute/QcCompute/Uploads",
                    unique_folder,
                    "HTQC_ox_red.xlsx",
                ),
                "validation_result": validation_result,  
            }
        )

    
    return JsonResponse({"error": "File not uploaded"}, status=400)


@login_required(login_url="/register/login/")
@csrf_exempt  
def upload_excel_QcCoumpute_HTQC_pka_pkb(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        excel_file = request.FILES["excel_file"]  

        
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            return JsonResponse(
                {"error": f"Error reading Excel file: {str(e)}"}, status=400
            )

        
        validation_result = validate_HTQC_pka_pkb_df(df)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        upload_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Uploads", unique_folder
        )

        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        
        file_path = os.path.join(upload_dir, "pkb_DFT.xlsx")

        
        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        
        return JsonResponse(
            {
                "file_path": os.path.join(
                    settings.MEDIA_URL,
                    "AutoCompute/QcCompute/Uploads",
                    unique_folder,
                    "pkb_DFT.xlsx",
                ),
                "validation_result": validation_result,  
            }
        )

    
    return JsonResponse({"error": "File not uploaded"}, status=400)


@hybrid_login_required  
@csrf_exempt  
def upload_excel_QcCoumpute_HTQC_reaction_thermo(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        excel_file = request.FILES["excel_file"]  

        
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            return JsonResponse(
                {"error": f"Error reading Excel file: {str(e)}"}, status=400
            )

        
        

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        upload_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Uploads", unique_folder
        )

        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        
        file_path = os.path.join(upload_dir, "HTQC_reaction_thermo.xlsx")

        
        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        
        return JsonResponse(
            {
                "file_path": os.path.join(
                    settings.MEDIA_URL,
                    "AutoCompute/QcCompute/Uploads",
                    unique_folder,
                    "HTQC_reaction_thermo.xlsx",
                ),
                
            }
        )

    
    return JsonResponse({"error": "File not uploaded"}, status=400)


@login_required(login_url="/register/login/")
@csrf_exempt  
def upload_excel_QcCoumpute_HTQC_global_reaction_properties(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        excel_file = request.FILES["excel_file"]  

        
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            return JsonResponse(
                {"error": f"Error reading Excel file: {str(e)}"}, status=400
            )

        
        validation_result = validate_HTQC_single_point_energy_df(df)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        upload_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Uploads", unique_folder
        )

        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        
        file_path = os.path.join(upload_dir, "HTQC_global_reaction_descriptors.xlsx")

        
        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        
        return JsonResponse(
            {
                "file_path": os.path.join(
                    settings.MEDIA_URL,
                    "AutoCompute/QcCompute/Uploads",
                    unique_folder,
                    "HTQC_global_reaction_descriptors.xlsx",
                ),
                "validation_result": validation_result,  
            }
        )

    
    return JsonResponse({"error": "File not uploaded"}, status=400)


@login_required(login_url="/register/login/")
@csrf_exempt  
def upload_excel_QcCoumpute_single_point_energy(request):
    if request.method == "POST":
        
        name = request.POST.get("nameInput")
        smiles = request.POST.get("smilesInput")

        if name and smiles:
            
            df = pd.DataFrame({"Name": [name], "SMILES": [smiles]})

            
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

            
            unique_folder = f"{current_time}_{str(uuid.uuid4())}"

            
            upload_dir = os.path.join(
                settings.MEDIA_ROOT, "AutoCompute/QcCompute/Uploads", unique_folder
            )

            
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            
            file_path = os.path.join(upload_dir, "single_point_energy.xlsx")

            
            df.to_excel(file_path, index=False)

            
            return JsonResponse(
                {
                    "file_path": os.path.join(
                        settings.MEDIA_URL,
                        "AutoCompute/QcCompute/Uploads",
                        unique_folder,
                        "single_point_energy.xlsx",
                    )
                }
            )

        
        return JsonResponse({"error": "Invalid data provided"}, status=400)

    
    return JsonResponse({"error": "Invalid request method"}, status=400)



def opt_progress_status_QcCoumpute(request):
    progress = cache.get("opt_current_progress", 0)  
    return JsonResponse({"progress": progress})



def energy_progress_status_QcCoumpute(request):
    progress = cache.get("energy_current_progress", 0)  
    return JsonResponse({"progress": progress})



@csrf_exempt  
@hybrid_login_required  
def upload_excel_MDCoumpute(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        excel_file = request.FILES["excel_file"]  

        
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            return JsonResponse(
                {"error": f"Error reading Excel file: {str(e)}"}, status=400
            )

        
        validation_result = validate_MD_system_df(df)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        upload_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/MDCompute/Uploads", unique_folder
        )

        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        
        file_path = os.path.join(upload_dir, "System.xlsx")

        
        with open(file_path, "wb+") as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)

        
        return JsonResponse(
            {
                "file_path": os.path.join(
                    settings.MEDIA_URL,
                    "AutoCompute/MDCompute/Uploads",
                    unique_folder,
                    "System.xlsx",
                ),
                "validation_result": validation_result,  
            }
        )

    
    return JsonResponse({"error": "File not uploaded"}, status=400)



@csrf_exempt
@hybrid_login_required  
def process_excel_MDCoumpute_byurl(request):

    signal, daily_limit = can_submit_today(request)
    
    

    
    if not signal:
        encrypted_id = f"You’ve reached your daily task limit of {daily_limit}. Please try again tomorrow."

        response_data = {
            "encrypted_id": encrypted_id,
        }

        return JsonResponse(response_data)

    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())[:6]}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/MDCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "System.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/MDCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/MDCompute/Downloads",
            unique_folder,
            "System.xlsx",
        )

        
        download_url_list = [download_dir, download_url, zip_download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,
            task_type="MDCoumpute",  
            task_id=encrypted_id,
            folder_path=download_dir,
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR, "autocompute", "static", "MDAutocompute_programe"
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_Gromacs_MD_notebook_tasks_remote",
            remote_target_subpath=REMOTE_MD_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def process_excel_MDCoumpute_ORCA_byurl(request):

    signal, daily_limit = can_submit_today(request)
    
    

    
    if not signal:
        encrypted_id = f"You’ve reached your daily task limit of {daily_limit}. Please try again tomorrow."

        response_data = {
            "encrypted_id": encrypted_id,
        }

        return JsonResponse(response_data)

    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())[:6]}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/MDCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "System.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/MDCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/MDCompute/Downloads",
            unique_folder,
            "System.xlsx",
        )

        
        download_url_list = [download_dir, download_url, zip_download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,
            task_type="MDCoumpute_ORCA",  
            task_id=encrypted_id,
            folder_path=download_dir,
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR, "autocompute", "static", "MDAutocompute_programe_ORCA"
        )

        
        response_data = {
            "encrypted_id": encrypted_id,
        }

        task.remote_type = "local"
        task.save(update_fields=["remote_type"])

        cmd = [
            sys.executable,
            os.path.join(settings.BASE_DIR, "manage.py"),
            "execute_md_task_generic",  
            str(task.task_id),  
            source_dir,  
            download_dir,  
            "autocompute.run_MD_QC_utils.run_Gromacs_MD_notebook_tasks_ORCA",
        ]
        log_path = os.path.join(download_dir, "md.log")
        with open(log_path, "a") as log_file:
            proc = subprocess.Popen(
                cmd,
                cwd=settings.BASE_DIR,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,  
            )

        
        task.pid = proc.pid
        task.save(update_fields=["pid"])

        
        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)


@hybrid_login_required
@csrf_exempt
def process_excel_QcCoumpute_HTQC_single_point_energy_byurl(request):

    signal, daily_limit = can_submit_today(request)
    
    

    
    if not signal:
        encrypted_id = f"You’ve reached your daily task limit of {daily_limit}. Please try again tomorrow."

        response_data = {
            "encrypted_id": encrypted_id,
        }

        return JsonResponse(response_data)

    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "HTQC.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "HTQC.xlsx",
        )

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,  
            task_type="HTQC_single_point_energy",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "HTQC_single_point_energy",
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_Gaussian_single_point_energy_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        
        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)



@hybrid_login_required
@csrf_exempt
def process_excel_QcCoumpute_HTQC_single_point_energy_byurl_orca(request):
    signal, daily_limit = can_submit_today(request)
    
    

    
    if not signal:
        encrypted_id = f"You’ve reached your daily task limit of {daily_limit}. Please try again tomorrow."

        response_data = {
            "encrypted_id": encrypted_id,
        }

        return JsonResponse(response_data)

    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "HTQC.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "HTQC.xlsx",
        )

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,  
            task_type="HTQC_single_point_energy_orca",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "ORCA_HTQC_single_point_energy",
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_ORCA_single_point_energy_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)


@hybrid_login_required  
@csrf_exempt
def process_excel_QcCoumpute_HTQC_binding_energy_byurl(request):
    signal, daily_limit = can_submit_today(request)
    
    

    
    if not signal:
        encrypted_id = f"You’ve reached your daily task limit of {daily_limit}. Please try again tomorrow."

        response_data = {
            "encrypted_id": encrypted_id,
        }

        return JsonResponse(response_data)

    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "Dimer.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "Dimer.xlsx",
        )

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,  
            task_type="HTQC_binding_energy",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "HTQC_binding_energy",
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_Gaussian_binding_energy_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)


@hybrid_login_required  
@csrf_exempt
def process_excel_QcCoumpute_HTQC_binding_energy_byurl_orca(request):
    signal, daily_limit = can_submit_today(request)
    
    

    
    if not signal:
        encrypted_id = f"You’ve reached your daily task limit of {daily_limit}. Please try again tomorrow."

        response_data = {
            "encrypted_id": encrypted_id,
        }

        return JsonResponse(response_data)

    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "Dimer.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "Dimer.xlsx",
        )

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,  
            task_type="HTQC_binding_energy_orca",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )
        
        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "ORCA_HTQC_binding_energy",
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_ORCA_binding_energy_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)



@hybrid_login_required
@csrf_exempt
def process_excel_QcCoumpute_HTQC_pka_pkb(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "pkb_DFT.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "pkb_DFT.xlsx",
        )

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,  
            task_type="HTQC_pka_pkb_calculation",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "HTQC_pka_pkb",
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_Gaussian_pka_pkb_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)


@hybrid_login_required  
@csrf_exempt
def process_excel_QcCoumpute_HTQC_ox_red(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "HTQC_ox_red.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "HTQC_ox_red.xlsx",
        )

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,  
            task_type="HTQC_ox_red_calculation",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )
        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "HTQC_ox_red",
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_Gaussian_ox_red_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)


@hybrid_login_required  
@csrf_exempt
def process_excel_QcCoumpute_HTQC_ox_red_orca(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "HTQC_ox_red.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "HTQC_ox_red.xlsx",
        )

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,  
            task_type="HTQC_ox_red_calculation_orca",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "ORCA_HTQC_ox_red",
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_ORCA_ox_red_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)



@hybrid_login_required  
@csrf_exempt
def process_excel_HTQC_reaction_thermo(request):

    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "HTQC_reaction_thermo.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "HTQC_reaction_thermo.xlsx",
        )

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,  
            task_type="HTQC_reaction_thermo_properties_calculation",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "HTQC_reaction_thermo",
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_Gaussian_reaction_thermo_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)



@hybrid_login_required  
@csrf_exempt
def process_excel_HTQC_global_reaction_properties(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(
            download_dir, "HTQC_global_reaction_descriptors.xlsx"
        )
        df.to_excel(processed_excel_path, index=False)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "HTQC_global_reaction_descriptors.xlsx",
        )

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,  
            task_type="HTQC_global_reaction_properties_descriptors_calculation",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )

        
        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "HTQC_global_reaction_descriptors_calculation",
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_Gaussian_global_reaction_properties_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)



class ElectrolyteListView(generics.ListAPIView):

    queryset = electrolyte.objects.all()  
    serializer_class = ElectrolyteSerializer  
    permission_classes = [IsAuthenticated]  


class ElectrolyteDetailView(generics.RetrieveAPIView):

    queryset = electrolyte.objects.all()  
    serializer_class = ElectrolyteSerializer  
    permission_classes = [IsAuthenticated]  


"""
from ionic_liquid.models import metal_anion_energy,Example 
from ionic_liquid.models import IL,Cation,Anion
from ionic_liquid.models import Li_electrolyte,electrolyte
"""


class Metal_Anion_EnergyListView(generics.ListAPIView):
    queryset = metal_anion_energy.objects.all()  
    serializer_class = Metal_Anion_EnergySerializer  
    permission_classes = [IsAuthenticated]  


class Metal_Anion_EnergyDetailView(generics.RetrieveAPIView):
    queryset = metal_anion_energy.objects.all()  
    serializer_class = Metal_Anion_EnergySerializer  
    permission_classes = [IsAuthenticated]  


class ILListView(generics.ListAPIView):
    queryset = IL.objects.all()  
    serializer_class = ILSerializer  
    permission_classes = [IsAuthenticated]  


class ILDetailView(generics.RetrieveAPIView):
    queryset = IL.objects.all()  
    serializer_class = ILSerializer  
    permission_classes = [IsAuthenticated]  


class CationListView(generics.ListAPIView):
    queryset = Cation.objects.all()  
    serializer_class = CationSerializer  
    permission_classes = [IsAuthenticated]  


class CationDetailView(generics.RetrieveAPIView):
    queryset = Cation.objects.all()  
    serializer_class = CationSerializer  
    permission_classes = [IsAuthenticated]  


class AnionListView(generics.ListAPIView):
    queryset = Anion.objects.all()  
    serializer_class = AnionSerializer  
    permission_classes = [IsAuthenticated]  


class AnionDetailView(generics.RetrieveAPIView):
    queryset = Anion.objects.all()  
    serializer_class = AnionSerializer  
    permission_classes = [IsAuthenticated]  


class Li_ElectrolyteListView(generics.ListAPIView):
    queryset = Li_electrolyte.objects.all()  
    serializer_class = Li_ElectrolyteSerializer  
    permission_classes = [IsAuthenticated]  


class Li_ElectrolyteDetailView(generics.RetrieveAPIView):
    queryset = Li_electrolyte.objects.all()  
    serializer_class = Li_ElectrolyteSerializer  
    permission_classes = [IsAuthenticated]  




def molecule_visualization_upload(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            
            error_message = "No file uploaded."
            return render(
                request,
                "autocompute/visualization/visualization.html",
                {"error_message": error_message},
            )

        else:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            unique_folder = f"{current_time}_{str(uuid.uuid4())}"

            
            upload_folder = os.path.join(
                settings.MEDIA_ROOT, "AutoCompute/QcCompute/Uploads", unique_folder
            )
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            fs = FileSystemStorage(location=upload_folder)

            
            filename = fs.save(uploaded_file.name, uploaded_file)

            
            file_path = os.path.join(upload_folder, filename)

            
            file_url = fs.url(
                os.path.join("AutoCompute/QcCompute/Uploads", unique_folder, filename)
            )

            success_message = "File uploaded successfully."

            
            if uploaded_file.name.endswith(".out"):
                try:
                    
                    def to_float_or_none(value):
                        if value is None:
                            return None
                        try:
                            return float(value)
                        except (TypeError, ValueError):
                            return None

                    
                    energy = to_float_or_none(
                        extract_energy_from_out(file_path)
                    )  
                    dipole = to_float_or_none(
                        extract_dipole_moment(file_path)
                    )  

                    
                    homo_str, lumo_str = extract_homo_lumo(file_path)
                    homo = to_float_or_none(homo_str)  
                    lumo = to_float_or_none(lumo_str)  

                    entropy = to_float_or_none(
                        extract_entropy(file_path)
                    )  
                    enthalpy_correction = to_float_or_none(
                        extract_enthalpy_correction(file_path)
                    )  
                    gibbs_correction = to_float_or_none(
                        extract_gibbs_correction(file_path)
                    )  

                    
                    gibbs_free_energy = (
                        (energy + gibbs_correction)
                        if energy is not None and gibbs_correction is not None
                        else None
                    )
                    enthalpy = (
                        (energy + enthalpy_correction)
                        if energy is not None and enthalpy_correction is not None
                        else None
                    )
                    homo_lumo_gap = (
                        (lumo - homo) if homo is not None and lumo is not None else None
                    )

                    
                    molecular_properties = {
                        "Energy (Hartree)": f"{energy:.6f}"
                        if energy is not None
                        else None,
                        "Dipole Moment (Debye)": f"{dipole:.6f}"
                        if dipole is not None
                        else None,
                        "HOMO (Hartree)": f"{homo:.6f}" if homo is not None else None,
                        "LUMO (Hartree)": f"{lumo:.6f}" if lumo is not None else None,
                        "HOMO-LUMO Gap (Hartree)": f"{homo_lumo_gap:.6f}"
                        if homo_lumo_gap is not None
                        else None,
                        "Entropy (J/mol·K)": f"{entropy:.2f}"
                        if entropy is not None
                        else None,
                        "Enthalpy Correction (Hartree)": f"{enthalpy_correction:.6f}"
                        if enthalpy_correction is not None
                        else None,
                        "Gibbs Correction (Hartree)": f"{gibbs_correction:.6f}"
                        if gibbs_correction is not None
                        else None,
                        "Gibbs Free Energy (Hartree)": f"{gibbs_free_energy:.6f}"
                        if gibbs_free_energy is not None
                        else None,
                        "Enthalpy (Hartree)": f"{enthalpy:.6f}"
                        if enthalpy is not None
                        else None,
                    }

                    
                    context = {
                        "success_message": success_message,
                        "file_url": file_url,
                        "molecular_properties": molecular_properties,
                    }
                    return render(
                        request, "autocompute/visualization/visualization.html", context
                    )

                except Exception as e:
                    error_message = (
                        f"An error occurred while processing the file: {str(e)}"
                    )
                    molecular_properties = None
                    context = {
                        "error_message": error_message,
                        "file_url": file_url,
                        "molecular_properties": molecular_properties,
                    }
                    return render(
                        request, "autocompute/visualization/visualization.html", context
                    )

            else:
                
                molecular_properties = None
                context = {
                    "success_message": success_message,
                    "file_url": file_url,
                    "molecular_properties": molecular_properties,
                }

                return render(
                    request, "autocompute/visualization/visualization.html", context
                )

    else:
        return render(request, "autocompute/visualization/visualization.html")



def predict_conjugate_acid_base(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("excel_file")

        if not uploaded_file:
            error_message = "No file uploaded."
            return render(
                request,
                "autocompute/qcCompute/HTQC_pka_pkb_byurl.html",
                {"error_message": error_message},
            )

        
        if not uploaded_file.name.endswith((".xlsx", ".xls")):
            error_message = "Please upload an Excel file with .xlsx or .xls extension."
            return render(
                request,
                "autocompute/qcCompute/HTQC_pka_pkb_byurl.html",
                {"error_message": error_message},
            )

        try:
            
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_folder = f"{current_time}_{str(uuid.uuid4())}"
            upload_folder = os.path.join(
                settings.MEDIA_ROOT, "AutoCompute/QcCompute/Uploads", unique_folder
            )
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            fs = FileSystemStorage(location=upload_folder)
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_path = os.path.join(upload_folder, filename)

            
            df = pd.read_excel(file_path)

            
            if "Name" not in df.columns or "SMILES" not in df.columns:
                error_message = (
                    "The uploaded Excel file must contain 'Name' and 'SMILES' columns."
                )
                return render(
                    request,
                    "autocompute/qcCompute/HTQC_pka_pkb_byurl.html",
                    {"error_message": error_message},
                )

            
            df["conjugate_base_smiles"] = ""
            df["conjugate_acid_smiles"] = ""

            
            for index, row in df.iterrows():
                smiles = row["SMILES"]
                try:
                    conjugate_base_smiles, conjugate_acid_smiles = (
                        get_conjugate_acid_base(smiles)
                    )
                    df.at[index, "conjugate_base_smiles"] = conjugate_base_smiles
                    df.at[index, "conjugate_acid_smiles"] = conjugate_acid_smiles
                except Exception as e:
                    df.at[index, "conjugate_base_smiles"] = "Error"
                    df.at[index, "conjugate_acid_smiles"] = "Error"

            
            result_filename = f"conjugate_prediction_{current_time}.xlsx"
            result_file_path = os.path.join(upload_folder, result_filename)
            df.to_excel(result_file_path, index=False)

            
            result_file_url = os.path.join(
                settings.MEDIA_URL,
                "AutoCompute/QcCompute/Uploads",
                unique_folder,
                result_filename,
            )

            success_message = "Prediction completed successfully."
            context = {
                "success_message": success_message,
                "result_file_url": result_file_url,
            }
            return render(
                request, "autocompute/qcCompute/HTQC_pka_pkb_byurl.html", context
            )

        except Exception as e:
            error_message = f"An error occurred during processing: {str(e)}"
            return render(
                request,
                "autocompute/qcCompute/HTQC_pka_pkb_byurl.html",
                {"error_message": error_message},
            )

    else:
        return render(request, "autocompute/qcCompute/HTQC_pka_pkb_byurl.html")



@csrf_exempt
@hybrid_login_required
def process_excel_smiles_query_byurl(request):
    if request.method == "POST" and request.FILES["excel_file"]:
        
        excel_file = request.FILES["excel_file"]
        df = pd.read_excel(excel_file)

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())[:6]}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, "processed_file.xlsx")
        df.to_excel(processed_excel_path, index=False)

        
        download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "processed_file.xlsx",
        )

        
        download_url_list = [download_dir, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        task = ComputeTask.objects.create(
            user=request.user,  
            task_type="From SMILES to Name",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )

        task.remote_type = "local"
        task.save(update_fields=["remote_type"])

        source_dir = os.path.join(
            settings.BASE_DIR, "autocompute", "static", "query_SMILES"
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }
        cmd = [
            sys.executable,
            os.path.join(settings.BASE_DIR, "manage.py"),
            "execute_task_immediate",  
            str(task.task_id),  
            source_dir,  
            download_dir,  
            "autocompute.run_MD_QC_utils.run_query_name_CAS_tasks",
        ]
        log_path = os.path.join(download_dir, "query_name_CAS.log")
        with open(log_path, "a") as log_file:
            proc = subprocess.Popen(
                cmd,
                cwd=settings.BASE_DIR,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,  
            )

        
        task.pid = proc.pid
        task.save(update_fields=["pid"])

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)




@csrf_exempt
@hybrid_login_required
def query_smiles_name(request):
    if request.method == "POST":
        smiles_input = request.POST.get("smiles_input")
        if not smiles_input:
            return JsonResponse({"error": "Please input SMILES."})
        name = from_smiles_get_iupac_name(smiles_input)
        safe_name = get_safe_name(name) if name else ""
        data = {"smiles_input": smiles_input, "name": name, "safe_name": safe_name}
        return JsonResponse(data)
    else:
        return render(
            request, "autocompute/from_smiles_get_name/from_smiles_get_name.html"
        )




def manual_mode_qccompute_page(request):
    return render(request, "autocompute/qcCompute/Manual_mode_QCcompute_byurl.html")


@csrf_exempt
def manual_mode_qccompute_byurl(request):
    
    user = get_authenticated_user(request)
    if user is None:
        return JsonResponse(
            {
                "error": "Authentication required. Please login or provide a valid Token."
            },
            status=401,
        )

    signal, daily_limit = can_submit_today(request)
    
    

    
    if not signal:
        encrypted_id = f"You've reached your daily task limit of {daily_limit}. Please try again tomorrow."

        response_data = {
            "encrypted_id": encrypted_id,
        }

        return JsonResponse(response_data)

    if request.method == "POST":
        
        
        xyz_file = request.FILES.get("xyz_file", None)  
        
        charge = request.POST.get("total_charge", None)
        multiplicity = request.POST.get("spin_multiplicity", None)
        
        name = request.POST.get("system_name", None)

        
        if not charge or not multiplicity or not xyz_file or not name:
            return JsonResponse(
                {"error": "Missing charge or spin_multiplicity or file or name."},
                status=400,
            )

        
        

        
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        

        
        
        try:
            coordinate_str = extract_coordinates(xyz_file)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        
        output_inp_file_path = os.path.join(download_dir, f"{name}.inp")
        
        create_ORCA_opt_inputfile(
            coordinate_str, charge, multiplicity, output_inp_file_path
        )

        
        

        
        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = create_result_excel(name, unique_folder)
        
        

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=user,  
            task_type="Manual_Mode_QCcompute",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )

        
        

        
        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "ORCA_manual_mode_opt+freq_energy",
        )
        
        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_ORCA_manual_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)
    return JsonResponse({"error": "Invalid request"}, status=400)



@csrf_exempt
def manual_mode_qccompute_byurl_energy(request):
    
    user = get_authenticated_user(request)
    if user is None:
        return JsonResponse(
            {
                "error": "Authentication required. Please login or provide a valid Token."
            },
            status=401,
        )

    signal, daily_limit = can_submit_today(request)
    
    

    
    if not signal:
        encrypted_id = f"You've reached your daily task limit of {daily_limit}. Please try again tomorrow."

        response_data = {
            "encrypted_id": encrypted_id,
        }

        return JsonResponse(response_data)

    if request.method == "POST":
        
        
        xyz_file = request.FILES.get("xyz_file", None)  
        
        charge = request.POST.get("total_charge", None)
        multiplicity = request.POST.get("spin_multiplicity", None)
        
        name = request.POST.get("system_name", None)

        
        if not charge or not multiplicity or not xyz_file or not name:
            return JsonResponse(
                {"error": "Missing charge or spin_multiplicity or file or name."},
                status=400,
            )

        
        

        
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        
        unique_folder = f"{current_time}_{str(uuid.uuid4())}"

        
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute/QcCompute/Downloads", unique_folder
        )
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        

        
        
        try:
            coordinate_str = extract_coordinates(xyz_file)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)
        
        output_inp_file_path = os.path.join(download_dir, f"{name}.inp")
        
        create_ORCA_energy_inputfile(
            coordinate_str, charge, multiplicity, output_inp_file_path
        )

        
        

        
        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute/QcCompute/Downloads",
            unique_folder,
            "all_results.zip",
        )
        
        download_url = create_result_excel(name, unique_folder)
        
        

        
        download_url_list = [download_dir, zip_download_url, download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=user,  
            task_type="Manual_Mode_QCcompute_energy",  
            task_id=encrypted_id,  
            folder_path=download_dir,  
            status="pending",  
        )

        
        

        
        source_dir = os.path.join(
            settings.BASE_DIR,
            "autocompute",
            "static",
            "QcAutocompute_programe",
            "ORCA_manual_mode_energy",
        )
        
        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_ORCA_manual_notebook_tasks_remote_energy",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)
    return JsonResponse({"error": "Invalid request"}, status=400)



import os
import uuid
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import zipfile



@csrf_exempt
@hybrid_login_required
def convert_chk_to_fchk_view(request):
    if request.method == "POST" and request.FILES.getlist("files"):
        
        uploaded_files = request.FILES.getlist("files")
        logger.info(f"get uploaded_files")
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_folder = f"{current_time}_{uuid.uuid4()}"
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute", "QcCompute", "Downloads", unique_folder
        )
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"generate download_dir")

        
        for chk_file in uploaded_files:
            
            filename = os.path.splitext(os.path.basename(chk_file.name))[0]
            
            chk_path = os.path.join(download_dir, f"{filename}.chk")
            default_storage.save(chk_path, ContentFile(chk_file.read()))

        
        try:
            logger.info(f"{download_dir}")
            convert_chk_to_fchk(download_dir)

        except Exception as e:
            logger.info(f"error: Conversion failed: {str(e)}")
            return JsonResponse({"error": f"Conversion failed: {str(e)}"}, status=500)

        
        zip_filename = os.path.join(download_dir, "all_result.zip")
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            
            for root, dirs, files in os.walk(download_dir):
                for f in files:
                    if f.lower().endswith(".fchk"):
                        full_path = os.path.join(root, f)
                        
                        rel_path = os.path.relpath(full_path, download_dir)
                        zipf.write(full_path, rel_path)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            "all_result.zip",
        )

        return JsonResponse({"zip_download_url": zip_download_url})

    return JsonResponse(
        {"error": "Invalid request: .chk files not provided"}, status=400
    )



@csrf_exempt
@hybrid_login_required
def convert_gbw_to_molden_view(request):
    if request.method == "POST" and request.FILES.getlist("files"):
        
        uploaded_files = request.FILES.getlist("files")

        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_folder = f"{current_time}_{uuid.uuid4()}"
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute", "QcCompute", "Downloads", unique_folder
        )
        os.makedirs(download_dir, exist_ok=True)

        
        for gbw_file in uploaded_files:
            
            filename = os.path.splitext(os.path.basename(gbw_file.name))[0]
            
            gbw_path = os.path.join(download_dir, f"{filename}.gbw")
            default_storage.save(gbw_path, ContentFile(gbw_file.read()))

        
        try:
            convert_gbw_to_molden(download_dir)
        except Exception as e:
            return JsonResponse({"error": f"Conversion failed: {str(e)}"}, status=500)

        
        zip_filename = os.path.join(download_dir, "all_result.zip")
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            
            for root, dirs, files in os.walk(download_dir):
                for f in files:
                    if f.lower().endswith(".molden"):
                        full_path = os.path.join(root, f)
                        
                        rel_path = os.path.relpath(full_path, download_dir)
                        zipf.write(full_path, rel_path)

        
        zip_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            "all_result.zip",
        )

        return JsonResponse({"zip_download_url": zip_download_url})

    return JsonResponse(
        {"error": "Invalid request: .chk files not provided"}, status=400
    )




@csrf_exempt
@login_required
def draw_ESP_page_view(request):
    return render(request, "autocompute/qcCompute/DrawESP_page.html")




@csrf_exempt
@hybrid_login_required
def draw_ESP_view(request):
    if request.method == "POST" and request.FILES.getlist("files"):
        
        uploaded_files = request.FILES.getlist("files")
        logger.info(f"get uploaded_files")
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_folder = f"{current_time}_{uuid.uuid4()}"
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute", "QcCompute", "Downloads", unique_folder
        )
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"generate download_dir")

        
        original_zip_name = "original_draw_file.zip"
        
        original_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            original_zip_name,
        )
        esp_zip_name = "ESP_fig_file.zip"
        esp_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            esp_zip_name,
        )

        
        fs = FileSystemStorage(
            location=download_dir
        )  
        for up_file in uploaded_files:  
            orig_name = os.path.basename(
                up_file.name
            )  
            safe_name = fs.get_valid_name(
                orig_name
            )  
            final_name = fs.get_available_name(
                safe_name
            )  
            fs.save(
                final_name, up_file
            )  

        
        try:
            convert_chk_to_fchk(download_dir)

        except Exception as e:
            logger.info(f"error: Conversion failed: {str(e)}")
            return JsonResponse({"error": f"Conversion failed: {str(e)}"}, status=500)

        
        download_url_list = [download_dir, original_download_url, esp_download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,
            task_type="DrawESP",  
            task_id=encrypted_id,
            folder_path=download_dir,
            status="pending",  
        )

        source_dir = os.path.join(settings.BASE_DIR, "autocompute", "static", "drawESP")

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_draw_ESP_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)



@csrf_exempt
@hybrid_login_required
def draw_ESP_view_gbw(request):
    if request.method == "POST" and request.FILES.getlist("files"):
        
        uploaded_files = request.FILES.getlist("files")
        logger.info(f"get uploaded_files")
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_folder = f"{current_time}_{uuid.uuid4()}"
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute", "QcCompute", "Downloads", unique_folder
        )
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"generate download_dir")

        
        original_zip_name = "original_draw_file.zip"
        
        original_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            original_zip_name,
        )
        esp_zip_name = "ESP_fig_file.zip"
        esp_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            esp_zip_name,
        )

        
        fs = FileSystemStorage(
            location=download_dir
        )  
        for up_file in uploaded_files:  
            orig_name = os.path.basename(
                up_file.name
            )  
            safe_name = fs.get_valid_name(
                orig_name
            )  
            final_name = fs.get_available_name(
                safe_name
            )  
            fs.save(
                final_name, up_file
            )  

        
        try:
            convert_gbw_to_molden(download_dir)

        except Exception as e:
            logger.info(f"error: Conversion failed: {str(e)}")
            return JsonResponse({"error": f"Conversion failed: {str(e)}"}, status=500)

        
        download_url_list = [download_dir, original_download_url, esp_download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,
            task_type="DrawESP_remote",  
            task_id=encrypted_id,
            folder_path=download_dir,
            status="pending",  
        )

        source_dir = os.path.join(settings.BASE_DIR, "autocompute", "static", "drawESP")

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_draw_ESP_notebook_tasks_gbw_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)




@csrf_exempt
@login_required
def draw_HOMO_LUMO_orb_page_view(request):
    return render(request, "autocompute/qcCompute/Draw_HOMO_LUMO_orb_page.html")



@csrf_exempt
@hybrid_login_required
def draw_HOMO_LUMO_orb_remote_view(request):
    if request.method == "POST" and request.FILES.getlist("files"):
        
        uploaded_files = request.FILES.getlist("files")
        logger.info(f"get uploaded_files")
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_folder = f"{current_time}_{uuid.uuid4()}"
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute", "QcCompute", "Downloads", unique_folder
        )
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"generate download_dir")

        
        original_zip_name = "original_draw_file.zip"
        
        original_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            original_zip_name,
        )
        orb_zip_name = "HOMO_LUMO_orb_fig_file.zip"
        orb_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            orb_zip_name,
        )

        
        allowed_exts = {
            ".chk",
            ".gbw",
            ".fchk",
            ".molden",
        }  
        for ufile in uploaded_files:  
            orig_name = os.path.basename(
                ufile.name
            )  
            base, ext = os.path.splitext(
                orig_name
            )  
            ext = ext.lower()  
            if (
                ext not in allowed_exts
            ):  
                
                continue  

            safe_base = get_valid_filename(
                base
            )  
            save_relpath = os.path.join(
                download_dir, f"{safe_base}{ext}"
            )  

            try:
                ufile.seek(0)  
            except Exception:
                pass  

            
            default_storage.save(
                save_relpath, ufile
            )  

        
        try:
            convert_chk_to_fchk(download_dir)
            convert_gbw_to_molden(download_dir)

        except Exception as e:
            logger.info(f"error: Conversion failed: {str(e)}")
            return JsonResponse({"error": f"Conversion failed: {str(e)}"}, status=500)

        
        download_url_list = [download_dir, original_download_url, orb_download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,
            task_type="Draw_HOMO_LUMO_orb",  
            task_id=encrypted_id,
            folder_path=download_dir,
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR, "autocompute", "static", "draw_HOMO_LUMO_orb"
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_draw_HOMO_LUMO_orb_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)




@csrf_exempt
@login_required
def NCI_analysis_page_view(request):
    return render(request, "autocompute/qcCompute/Draw_NCI_page.html")



@csrf_exempt
@hybrid_login_required
def NCI_analysis_view(request):
    if request.method == "POST" and request.FILES.getlist("files"):
        
        uploaded_files = request.FILES.getlist("files")
        logger.info(f"get uploaded_files")
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_folder = f"{current_time}_{uuid.uuid4()}"
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute", "QcCompute", "Downloads", unique_folder
        )
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"generate download_dir")

        
        original_zip_name = "original_draw_file.zip"
        
        original_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            original_zip_name,
        )
        nci_zip_name = "nci_fig_file.zip"
        nci_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            nci_zip_name,
        )

        
        allowed_exts = {
            ".chk",
            ".gbw",
            ".fchk",
            ".molden",
        }  
        for ufile in uploaded_files:  
            orig_name = os.path.basename(
                ufile.name
            )  
            base, ext = os.path.splitext(
                orig_name
            )  
            ext = ext.lower()  
            if (
                ext not in allowed_exts
            ):  
                
                continue  

            safe_base = get_valid_filename(
                base
            )  
            save_relpath = os.path.join(
                download_dir, f"{safe_base}{ext}"
            )  

            try:
                ufile.seek(0)  
            except Exception:
                pass  

            
            default_storage.save(
                save_relpath, ufile
            )  

        
        try:
            convert_chk_to_fchk(download_dir)
            convert_gbw_to_molden(download_dir)

        except Exception as e:
            logger.info(f"error: Conversion failed: {str(e)}")
            return JsonResponse({"error": f"Conversion failed: {str(e)}"}, status=500)

        
        download_url_list = [download_dir, original_download_url, nci_download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,
            task_type="NCI_analysis",  
            task_id=encrypted_id,
            folder_path=download_dir,
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR, "autocompute", "static", "NCIanalysis"
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_NCI_SCF_analysis_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)



@csrf_exempt
@hybrid_login_required
def NCI_promolecular_analysis_view(request):
    if request.method == "POST" and request.FILES.getlist("files"):
        
        uploaded_files = request.FILES.getlist("files")
        logger.info(f"get uploaded_files")
        
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_folder = f"{current_time}_{uuid.uuid4()}"
        download_dir = os.path.join(
            settings.MEDIA_ROOT, "AutoCompute", "QcCompute", "Downloads", unique_folder
        )
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"generate download_dir")

        
        original_zip_name = "original_draw_file.zip"
        
        original_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            original_zip_name,
        )
        nci_zip_name = "nci_fig_file.zip"
        nci_download_url = os.path.join(
            settings.MEDIA_URL,
            "AutoCompute",
            "QcCompute",
            "Downloads",
            unique_folder,
            nci_zip_name,
        )

        
        allowed_exts = {
            ".pdb",
            ".xyz",
            ".mol",
            ".mol2",
        }  
        for ufile in uploaded_files:  
            orig_name = os.path.basename(
                ufile.name
            )  
            base, ext = os.path.splitext(
                orig_name
            )  
            ext = ext.lower()  
            if (
                ext not in allowed_exts
            ):  
                
                continue  

            safe_base = get_valid_filename(
                base
            )  
            save_relpath = os.path.join(
                download_dir, f"{safe_base}{ext}"
            )  

            try:
                ufile.seek(0)  
            except Exception:
                pass  

            
            default_storage.save(
                save_relpath, ufile
            )  

        
        download_url_list = [download_dir, original_download_url, nci_download_url]

        
        encrypted_id = encrypt_download_url_list(download_url_list)

        
        task = ComputeTask.objects.create(
            user=request.user,
            task_type="NCI_promolecular_analysis",  
            task_id=encrypted_id,
            folder_path=download_dir,
            status="pending",  
        )

        source_dir = os.path.join(
            settings.BASE_DIR, "autocompute", "static", "NCI_analysis_promolecular"
        )

        response_data = {
            "encrypted_id": encrypted_id,
        }

        _enqueue_remote_task_for_scheduler(
            task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path="autocompute.remote_utils.run_NCI_promolecular_analysis_notebook_tasks_remote",
            remote_target_subpath=REMOTE_QC_DOWNLOADS_TARGET,
        )

        return JsonResponse(response_data)

    return JsonResponse({"error": "Invalid request"}, status=400)







def _parse_validation_result(result_message, total_count):
    """
    Parse validation result message into structured JSON

    Args:
        result_message: String from validate function (with <br> separators)
        total_count: Total number of rows

    Returns:
        JsonResponse with structured validation result
    """
    lines = result_message.split("<br>")

    errors = []
    warnings = []

    for line in lines:
        line = line.strip()
        if line.startswith("❌"):
            errors.append(line.replace("❌", "").strip())
        elif line.startswith("⚠️"):
            warnings.append(line.replace("⚠️", "").strip())

    valid_count = len([line for line in lines if "✅" in line])
    success = len(errors) == 0

    return JsonResponse(
        {
            "success": success,
            "message": result_message,
            "errors": errors,
            "warnings": warnings,
            "valid_count": valid_count,
            "total_count": total_count,
        }
    )


@csrf_exempt
def validate_HTQC_single_point_energy_api(request):
    """
    Validate single point energy data from JSON

    Expected JSON:
    {
        "data": [
            {"Name": "mol1", "SMILES": "CCO"},
            {"Name": "mol2", "SMILES": "NCCO"}
        ]
    }

    Returns:
    {
        "success": true/false,
        "message": "validation result with <br> separators",
        "errors": ["error1", "error2"],
        "warnings": ["warning1"],
        "valid_count": 2,
        "total_count": 2
    }
    """
    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Only POST method is allowed",
                "errors": ["Method not allowed"],
                "warnings": [],
                "valid_count": 0,
                "total_count": 0,
            },
            status=405,
        )

    try:
        
        request_data = json.loads(request.body)
        data_list = request_data.get("data", [])

        if not data_list:
            return JsonResponse(
                {
                    "success": False,
                    "message": "❌ No data provided",
                    "errors": ["No data provided"],
                    "warnings": [],
                    "valid_count": 0,
                    "total_count": 0,
                }
            )

        
        df = pd.DataFrame(data_list)

        
        validation_result = validate_HTQC_single_point_energy_df(df)
        
        
        return _parse_validation_result(validation_result, len(df))
        

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "errors": [str(e)],
                "warnings": [],
                "valid_count": 0,
                "total_count": 0,
            },
            status=400,
        )


@csrf_exempt
def validate_HTQC_binding_energy_api(request):
    """
    Validate binding energy data from JSON

    Expected JSON:
    {
        "data": [
            {
                "Dimer Name": "EMIM_BF4",
                "Dimer SMILES": "CCN(C)C.B(F)(F)F",
                "Component Name A": "EMIM_cation",
                "Component SMILES A": "CCN(C)C",
                "Component Name B": "BF4_anion",
                "Component SMILES B": "B(F)(F)F"
            }
        ]
    }
    """
    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Only POST method is allowed",
                "errors": ["Method not allowed"],
                "warnings": [],
                "valid_count": 0,
                "total_count": 0,
            },
            status=405,
        )

    try:
        request_data = json.loads(request.body)
        data_list = request_data.get("data", [])

        if not data_list:
            return JsonResponse(
                {
                    "success": False,
                    "message": "❌ No data provided",
                    "errors": ["No data provided"],
                    "warnings": [],
                    "valid_count": 0,
                    "total_count": 0,
                }
            )

        df = pd.DataFrame(data_list)
        validation_result = validate_HTQC_binding_energy_df(df)

        return _parse_validation_result(validation_result, len(df))

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "errors": [str(e)],
                "warnings": [],
                "valid_count": 0,
                "total_count": 0,
            },
            status=400,
        )


@csrf_exempt
def validate_HTQC_pka_pkb_api(request):
    """
    Validate pKa/pKb data from JSON

    Expected JSON:
    {
        "data": [
            {
                "Acid_Name": "Acid1",
                "Acid_SMILES": "CCC([NH3+])=O",
                "Conjugate_Alkali_Name": "Conjugate_Alkali1",
                "Conjugate_Alkali_SMILES": "CCC(N)=O"
            }
        ]
    }
    """
    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Only POST method is allowed",
                "errors": ["Method not allowed"],
                "warnings": [],
                "valid_count": 0,
                "total_count": 0,
            },
            status=405,
        )

    try:
        request_data = json.loads(request.body)
        data_list = request_data.get("data", [])

        if not data_list:
            return JsonResponse(
                {
                    "success": False,
                    "message": "❌ No data provided",
                    "errors": ["No data provided"],
                    "warnings": [],
                    "valid_count": 0,
                    "total_count": 0,
                }
            )

        df = pd.DataFrame(data_list)
        validation_result = validate_HTQC_pka_pkb_df(df)

        return _parse_validation_result(validation_result, len(df))

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "errors": [str(e)],
                "warnings": [],
                "valid_count": 0,
                "total_count": 0,
            },
            status=400,
        )


@csrf_exempt
def validate_MD_system_api(request):
    """
    Validate molecular dynamics system data from JSON

    Expected JSON:
    {
        "data": [
            {
                "Serial Number": 1,
                "Name": "EMIM",
                "is polymer": False,
                "repeating unit": 1,
                "SMILES": "CCN(C)C",
                "Number": 100,
                "temperature (K)": 298.15,
                "center atom": "EMIM",
                "scale_charge": 0.8,
                "is polymer melt": False
            }
        ]
    }
    """
    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "message": "Only POST method is allowed",
                "errors": ["Method not allowed"],
                "warnings": [],
                "valid_count": 0,
                "total_count": 0,
            },
            status=405,
        )

    try:
        request_data = json.loads(request.body)
        data_list = request_data.get("data", [])

        if not data_list:
            return JsonResponse(
                {
                    "success": False,
                    "message": "❌ No data provided",
                    "errors": ["No data provided"],
                    "warnings": [],
                    "valid_count": 0,
                    "total_count": 0,
                }
            )

        df = pd.DataFrame(data_list)
        validation_result = validate_MD_system_df(df)

        return _parse_validation_result(validation_result, len(df))

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": f"Validation error: {str(e)}",
                "errors": [str(e)],
                "warnings": [],
                "valid_count": 0,
                "total_count": 0,
            },
            status=400,
        )






from pathlib import Path
from django.http import FileResponse


AUTOCOMPUTE_DIST_DIR = Path(settings.BASE_DIR) / "autocompute" / "dist"
AUTOCOMPUTE_ASSETS_DIR = AUTOCOMPUTE_DIST_DIR / "assets"


def spa_index(request):
    index_path = AUTOCOMPUTE_DIST_DIR / "index.html"
    if not index_path.exists():
        return HttpResponse("Build not found. Run `npm run build`.", status=404)
    return FileResponse(open(index_path, "rb"), content_type="text/html; charset=utf-8")


def spa_assets(request, path: str):
    file_path = (AUTOCOMPUTE_ASSETS_DIR / path).resolve()
    if not str(file_path).startswith(str(AUTOCOMPUTE_ASSETS_DIR.resolve())):
        raise Http404
    if not file_path.is_file():
        raise Http404

    ctype, _ = mimetypes.guess_type(str(file_path))
    resp = FileResponse(
        open(file_path, "rb"), content_type=ctype or "application/octet-stream"
    )
    resp["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp


def spa_static(request, filename: str):
    
    allowed_files = {
        "HTQC.xlsx",  
        "HTQC_Binding.xlsx",  
        "HTQC_pka_pkb_template.xlsx",  
        "HTQC_Redox.xlsx",  
        "HTQC_reaction_thermo.xlsx",  
        "HTQC_global_reaction_descriptors.xlsx",  
        "System.xlsx",  
        "System_tutorial.pdf",  
        "System_tutorial_Chinese.pdf",  
    }

    
    if filename.startswith("ketcher/"):
        file_path = (AUTOCOMPUTE_DIST_DIR / filename).resolve()
    elif filename in allowed_files:
        file_path = (AUTOCOMPUTE_DIST_DIR / filename).resolve()
    else:
        raise Http404(f"File '{filename}' not allowed")

    
    if not str(file_path).startswith(str(AUTOCOMPUTE_DIST_DIR.resolve())):
        raise Http404("Invalid path")

    if not file_path.is_file():
        raise Http404(f"File '{filename}' not found")

    ctype, _ = mimetypes.guess_type(str(file_path))
    resp = FileResponse(
        open(file_path, "rb"), content_type=ctype or "application/octet-stream"
    )
    resp["Cache-Control"] = "public, max-age=31536000, immutable"
    if filename.startswith("ketcher/"):
        resp["X-Frame-Options"] = "SAMEORIGIN"
    return resp
