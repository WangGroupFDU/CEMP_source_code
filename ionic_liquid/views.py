from django.shortcuts import render


from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.shortcuts import render
from .forms import IonicLiquidNameForm, IonicLiquidFilterForm, Psi4TheoryForm, Psi4BasisForm, Psi4MethodForm
from .models import IL_properties, IL_smiles_psi4, IL_smiles_rdkit,metal_anion_energy
from . import ionic_liquid_utils
from pandas import DataFrame
import traceback
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
import json
from django.core.cache import cache
from rdkit import Chem
from datetime import datetime 
import zipfile 
import os
from django.conf import settings 
from django.core.exceptions import ValidationError
import mimetypes
from pathlib import Path
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from ionic_liquid.models import ILgenerator_IL, IL_ML_data, Cation_QC_data, Anion_QC_data, IL_Tm_conductivity_ECW_data 

def ionic_liquid_base_page(request):
    return render(request,"ionic_base_display.html")

def ionic_liquid_database_card_page(request):
    return render(request,"database/ionc_liquid_database_card_display_base.html")


def ionic_liquid_search(request):
    data_table = """<table border="0" class="display" id="ionic_liquid_table" style="width:100%">
                      <thead><tr style="text-align: right;"><th>Feature</th><th>Value</th></tr></thead>
                      <tbody></tbody>
                      </thead></table>
                    """
    form_type = IonicLiquidFilterForm()
    form_name = IonicLiquidNameForm()

    if request.method == "POST": 
        if request.POST.get('cation_type') is not None:
            print(request.POST)
            cation_type = request.POST.get('cation_type')
            anion_type = request.POST.get('anion_type')
            display_level = request.POST.get('dataset')
            filter_choice = "type"
        elif request.POST.get('cation_name') is not None:
            cation_name= request.POST.get('cation_name')
            anion_name = request.POST.get('anion_name')
            display_level = request.POST.get('dataset')
            filter_choice = "name"

        if "physical" in display_level:
            print("physical_info")
            
            model = IL_properties
            field_names = list(model._meta.get_fields())
            print(field_names)
            
            titles_table = [ 'label', 'formula', 'cation', 'anion', 'cation_type', 'anion_type', 'ECW',
                            'melting_point', 'conductivity',  'T_conductivity', 'viscosity', 'T_viscosity',
                            'density', 'T_density']
            if filter_choice == "type":
                data_table = [[getattr(ins, name) for name in titles_table]
                          for ins in model.objects.filter(cation_type=cation_type, anion_type=anion_type)]
                data_table = DataFrame(data=data_table, columns=titles_table)
                data_table = data_table.to_html(table_id="ionic_liquid_table",
                                                                              classes="display",
                                                                              border="0")
            elif filter_choice == "name":
                data_table = [[getattr(ins, name) for name in titles_table]
                          for ins in model.objects.filter(cation=cation_name, anion=anion_name)]
                data_table = DataFrame(data=data_table, columns=titles_table)
                data_table = data_table.to_html(table_id="ionic_liquid_table",
                                                                              classes="display",
                                                                              border="0")

        if "rdkit" in display_level:
            print("rdkit_info")
            
            model = IL_smiles_rdkit
            field_names = list(model._meta.get_fields())
            titles_table = ['name', 'smile_form', 'Asphericity', 'Eccentricity', 'NPR1', 'NPR2', 'PMI1', 'PMI2',
                            'PMI3', 'RadiusOfGyration', 'SpherocityIndex', 'ExactMolWt', 'FpDensityMorgan1',
                            'FpDensityMorgan2','HeavyAtomMolWt', 'MaxAbsPartialCharge', 'MaxPartialCharge',
                            'MinPartialCharge', 'NumRadicalElectrons', 'NumValenceElectrons', 'volume', 'type']
            print(cation_name, anion_name)
            data_table = [[getattr(ins, name) for name in titles_table]
                                    for ins in model.objects.filter(name__in=[cation_name, anion_name])]
            data_table = DataFrame(data=data_table,columns=titles_table)
            data_table = data_table.set_index('name').transpose().to_html(table_id="ionic_liquid_table",
                                                                                classes="display",
                                                                                border="0")


        if "psi4" in display_level:
            print("psi4_info")
            
            model = IL_smiles_psi4
            titles_table = ['name', 'smile_form', 'energy', 'HOMO', 'LUMO',
                            'dipole_x', 'dipole_y', 'dipole_z', 'dipole_total', 'type']
            print(cation_name, anion_name)
            data_table = [[getattr(ins, name) for name in titles_table]
                                    for ins in model.objects.filter(name__in=[cation_name.lower(), anion_name.lower()])]
            data_table = DataFrame(data=data_table,columns=titles_table)
            
            
            data_table = data_table.set_index('name').transpose().to_html(table_id="ionic_liquid_table",
                                                                                classes="display",
                                                                                border="0")

            pass
    else:
        pass

    return render(request, 'ionic_liquid_search.html', {'form_type': form_type, 'form_name': form_name,
                                                 'data_table': data_table})


def load_anion_types(request):
    cation_type = request.GET.get('cation_type')
    model = IL_properties
    anion_type = model.objects.filter(cation_type=cation_type).values_list('anion_type', flat=True).distinct()
    return render(request, 'load_anion_types.html', {'anion_type': anion_type})
    


def load_anion_names(request):
    print("Ajax for anion manes")
    print(request.GET)
    cation_name= request.GET.get('cation_name')
    model = IL_properties
    anion_name = model.objects.filter(cation=cation_name).values_list('anion', flat=True).distinct()

    return render(request, 'load_anion_names.html', {'anion_name': anion_name})


def ionic_liquid_calculate(request):
    theory_form = Psi4TheoryForm()
    basis_form = Psi4BasisForm()
    method_form = Psi4MethodForm()
    cation_figure_path = 'images/Cation.png'
    anion_figure_path = 'images/Anion.png'
    cation_html = """<table border="0" class="display" id="cation_table">
                      <thead><tr style="text-align: right;"><th>Feature</th><th>Value</th></tr></thead>
                      <tbody></tbody>
                      </thead></table>
                    """
    anion_html = """<table border="0" class="display" id="anion_table">
                      <thead><tr style="text-align: right;"><th>Feature</th><th>Value</th></tr></thead>
                      <tbody></tbody>
                      </thead></table>
                    """
    threeD_colum = ["Asphericity", "Eccentricity", "InertialShapeFactor", "NPR1", "NPR2", "PMI1", "PMI2",
                    "PMI3", "RadiusOfGyration", "SpherocityIndex"]
    mol_colum = ["ExactMolWt", "FpDensityMorgan1", "FpDensityMorgan2", "HeavyAtomMolWt", "MaxAbsPartialCharge",
                 "MaxPartialCharge", "MinPartialCharge", "NumRadicalElectrons", "NumValenceElectrons", "volume"]
    psi4_column = ["Method", "basis_sets", "energy", "HOMO", "LUMO", "Dipole_x", "Dipole_y", "Dipole_z", "Dipole_Total"]
    if request.method == "POST":
        theory = request.POST.get('theory')
        basis_set = request.POST.get('basis_set')
        method = request.POST.get('method')
        if request.POST.get('cation_smile') is not None:
            print("Cation info!")
            cation_smile = request.POST.get('cation_smile')
            cation_figure_path = ionic_liquid_utils.drawSMILEs(cation_smile)
            print(cation_figure_path)
            if "error" not in cation_figure_path:
                cation_3Ddescriptor = ionic_liquid_utils.cal3Ddescriptor(cation_smile)
                cation_Moldescriptor= ionic_liquid_utils.calMoldescriptor(cation_smile)

                cation_psi4 = ionic_liquid_utils.psi4Calculation(cation_smile,basis_sets=theory+"/"+basis_set,
                                                                    method = method)

                cation_results = DataFrame(data = [['Value']+cation_3Ddescriptor + cation_Moldescriptor + cation_psi4],
                                           columns = ['Feature']+threeD_colum+mol_colum+psi4_column)
                cation_html = cation_results.set_index('Feature').transpose().to_html(table_id = "cation_table",
                                                                                      classes = "display",
                                                                                      border = "0")
            else:
                pass

        if request.POST.get('anion_smile') is not None:
            print("Anion info!")
            anion_smile = request.POST.get('anion_smile')
            anion_figure_path = ionic_liquid_utils.drawSMILEs(anion_smile)
            if "error" not in anion_figure_path:
                anion_3Ddescriptor = ionic_liquid_utils.cal3Ddescriptor(anion_smile)
                anion_Moldescriptor = ionic_liquid_utils.calMoldescriptor(anion_smile)

                anion_psi4 = ionic_liquid_utils.psi4Calculation(anion_smile,basis_sets=theory+"/"+basis_set,
                                                                    method = method)

                anion_results = DataFrame(data = [['Value']+anion_3Ddescriptor + anion_Moldescriptor + anion_psi4],
                                           columns = ['Feature']+threeD_colum+mol_colum+psi4_column)
                anion_html = anion_results.set_index('Feature').transpose().to_html(table_id = "anion_table",
                                                                                    classes = "display",
                                                                                    border = "0")
            else:
                pass
    return render(request, 'ionic_liquid_calculate.html', {'theory_form': theory_form,
            'basis_form': basis_form, 'method_form': method_form, 'url_cation':cation_figure_path,
           'url_anion': anion_figure_path, 'cation_html': cation_html, 'anion_html': anion_html})


def ionic_liquid_predict(request):
    state = ""
    type = ""
    cation_smile = ""
    anion_smile = ""
    cation_html = """<table border="0" class="display" id="cation_table">
                      <thead><tr style="text-align: right;"><th>Feature</th><th>Value</th></tr></thead>
                      <tbody></tbody>
                      </thead></table>
                    """
    anion_html = """<table border="0" class="display" id="anion_table">
                      <thead><tr style="text-align: right;"><th>Feature</th><th>Value</th></tr></thead>
                      <tbody></tbody>
                      </thead></table>
                    """
    print("Predict")

    if request.method == "POST":
        ionic_liquid_utils.modelPredictionTest()
        
        
        

    return render(request, 'ionic_liquid_predict.html', { 'state': state, 'type': type,
                                                          "cation_smile": cation_smile,
                                                          "anion_smile": anion_smile})










    












@login_required
def XGBoost_predict_page(request):
    return render(request,"XGBoost_predict_IL_property/XGBoost_predict_base.html")
@csrf_exempt  
def upload_excel_ILpredict_XGBoost_view(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']  

            
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')

            
            unique_folder = f"{current_time}_{str(uuid.uuid4())}"
            
            
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'ionic_liquid/ILpredict_XGBoost/Uploads', unique_folder)
            
            
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            
            file_path = os.path.join(upload_dir, 'Ionic_liquid_list.xlsx')
            
            
            with open(file_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)
            
            
            return JsonResponse({
                'file_path': os.path.join(settings.MEDIA_URL, 'ionic_liquid/ILpredict_XGBoost/Uploads', unique_folder, 'Ionic_liquid_list.xlsx')
            })
        else:
            return JsonResponse({'error': 'No file provided'}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def process_excel_ILpredict_XGBoost_view(request):
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

        
        download_dir = os.path.join(settings.MEDIA_ROOT, 'ionic_liquid/ILpredict_XGBoost/Downloads', unique_folder)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        
        processed_excel_path = os.path.join(download_dir, 'Ionic_liquid_list.xlsx')
        try:
            df.to_excel(processed_excel_path, index=False)
        except Exception as e:
            error_message = f"Failed to save Excel file: {str(e)}"
            traceback_str = traceback.format_exc()
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)

        
        source_dir = os.path.join(settings.BASE_DIR, 'ionic_liquid', 'static', 'program', 'predict_IL_properties_excel_batch')
        for filename in os.listdir(source_dir):
            source_file = os.path.join(source_dir, filename)
            if os.path.isfile(source_file):
                shutil.copy(source_file, download_dir)
            elif os.path.isdir(source_file):
                shutil.copytree(source_file, os.path.join(download_dir, filename))

        
        notebooks_to_run = [
            '1_IL_predict_with_xgboost.ipynb',
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

        
        download_url = settings.MEDIA_URL + '/ionic_liquid/ILpredict_XGBoost/Downloads/' + unique_folder + '/Ionic_liquid_list_output.xlsx'

        
        return JsonResponse({'download_url': download_url}) 
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def IL_ML_data_view_paging(request):
    
    per_page = 200
    page_number = request.GET.get('page', 1)  

    
    fields = IL_ML_data._meta.get_fields()
    field_names_verbose = [f.name for f in fields]
    data = [[getattr(instance, name) for name in field_names_verbose] for instance in IL_ML_data.objects.all()]

    
    paginator = Paginator(data, per_page)
    page_obj = paginator.get_page(page_number)

    dict = {
        'field_names': field_names_verbose,
        'data': page_obj.object_list,  
        'has_next': page_obj.has_next(),  
        'page_number': page_number,  
    }

    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(dict)  

    
    return render(request, "database/IL_ML_data_database_paging.html", dict)



def Cation_QC_data_view(request):
    fields = Cation_QC_data._meta.get_fields() 
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [[getattr(instance, name) for name in field_names_verbose] for instance in Cation_QC_data.objects.all()]
    
    dict = {
        'field_names':field_names_verbose,
        'data':data, 
        'image_extensions': ['jpg', 'jpeg', 'png', 'gif'],
        'file_extensions': ['txt', 'csv','CSV', 'pdf'],
    }
    return render(request,"database/database_display.html",dict)


def Anion_QC_data_view(request):
    fields = Anion_QC_data._meta.get_fields() 
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [[getattr(instance, name) for name in field_names_verbose] for instance in Anion_QC_data.objects.all()]
    
    dict = {
        'field_names':field_names_verbose,
        'data':data, 
        'image_extensions': ['jpg', 'jpeg', 'png', 'gif'],
        'file_extensions': ['txt', 'csv','CSV', 'pdf'],
    }
    return render(request,"database/database_display.html",dict)


def IL_Tm_conductivity_ECW_data_view(request):
    fields = IL_Tm_conductivity_ECW_data._meta.get_fields() 
    
    field_names_verbose = [f.name for f in fields]
    
    
    data = [[getattr(instance, name) for name in field_names_verbose] for instance in IL_Tm_conductivity_ECW_data.objects.all()]
    
    dict = {
        'field_names':field_names_verbose,
        'data':data, 
        'image_extensions': ['jpg', 'jpeg', 'png', 'gif'],
        'file_extensions': ['txt', 'csv','CSV', 'pdf'],
    }
    return render(request,"database/database_display.html",dict)








_IL_FINGERPRINT_CACHE = {}


IL_PROPERTY_COLS = ["ECW (V)", "Tm (K)", "Conductivity (mS/cm)"]
ION_PROPERTY_COLS = ["HOMO (Hatree)", "LUMO (Hatree)"]

def _load_il_databases():
    """
    Load all 6 fingerprint databases once and cache globally.
    Returns dict with keys: experiment_IL, generated_IL, experiment_cation,
    generated_cation, experiment_anion, generated_anion
    """
    if _IL_FINGERPRINT_CACHE:
        return _IL_FINGERPRINT_CACHE

    import logging
    logger = logging.getLogger("django")

    
    from ionic_liquid.ionic_liquid_utils import load_morgan_fp_data_list

    
    test_box_path = os.path.join(os.path.dirname(__file__), 'test_box', 'query_similar_IL')

    
    

    logger.info(f"Loading databases from: {test_box_path}")
    logger.info(f"Directory exists: {os.path.exists(test_box_path)}")
    if os.path.exists(test_box_path):
        
        logger.info(f"Files in directory: {os.listdir(test_box_path)}")

    db_files = {
        'experiment_il': 'experiment_IL_smiles_morgan_fp.json.gz',
        'generated_il': 'generated_IL_smiles_morgan_fp.json.gz',
        'experiment_cation': 'experiment_cation_smiles_morgan_fp.json.gz',
        'generated_cation': 'generated_cation_smiles_morgan_fp.json.gz',
        'experiment_anion': 'experiment_anion_smiles_morgan_fp.json.gz',
        'generated_anion': 'generated_anion_smiles_morgan_fp.json.gz',
    }

    
    for key, filename in db_files.items():
        file_path = os.path.join(test_box_path, filename)
        logger.info(f"Checking {key}: {file_path}")
        logger.info(f"  File exists: {os.path.exists(file_path)}")

        if os.path.exists(file_path):
            try:
                data = load_morgan_fp_data_list(file_path)
                print(f"{file_path} safely loaded!,length is {len(data)}")
                _IL_FINGERPRINT_CACHE[key] = data
                logger.info(f"  Loaded {len(data)} entries for {key}")
            except Exception as e:
                logger.error(f"  Failed to load {key}: {e}")
                _IL_FINGERPRINT_CACHE[key] = []
        else:
            logger.warning(f"  File not found: {file_path}")
            _IL_FINGERPRINT_CACHE[key] = []

    logger.info(f"Cache keys: {list(_IL_FINGERPRINT_CACHE.keys())}")
    logger.info(f"Cache sizes: {[(k, len(v)) for k, v in _IL_FINGERPRINT_CACHE.items()]}")

    return _IL_FINGERPRINT_CACHE


@csrf_exempt
def api_il_similarity_search(request):
    """
    API endpoint for ionic liquid similarity search.

    Input (JSON):
        - smiles: Query SMILES string
        - mol_type: Material type - "IL", "Cation", or "Anion"
        - source: Data source - "experiment" or "generated"
        - topk: Number of top results (default: 10)
        - method: Similarity method - "tanimoto", "dice", "cosine", "tversky" (default: "tanimoto")

    Output (JSON):
        {
            "results": [
                {
                    "SMILES": "...",
                    "similarity": "95.50%",
                    "Name": "...",
                    "CAS": "...",
                    "properties": {
                        "ECW (V)": "...",
                        "Tm (K)": "...",
                        "Conductivity (mS/cm)": "..."
                    }
                }
            ],
            "status": "success"
        }
    """
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    if request.method == 'POST':
        try:
            
            from ionic_liquid.ionic_liquid_utils import topk_similar_smiles

            
            data = json.loads(request.body)
            query_smiles = data.get('smiles', '')
            mol_type = data.get('mol_type', 'IL').strip().lower()
            source = data.get('source', 'experiment').strip().lower()
            topk = int(data.get('topk', 10))
            method = data.get('method', 'tanimoto')

            
            if not query_smiles:
                return JsonResponse({'error': 'SMILES parameter is required'}, status=400)

            if mol_type not in ['il', 'cation', 'anion']:
                return JsonResponse({'error': 'mol_type must be "il", "cation", "anion:"'}, status=400)

            if source not in ['experiment', 'generated']:
                return JsonResponse({'error': 'source must be "experiment" or "generated"'}, status=400)

            
            databases = _load_il_databases()

            
            db_key = f"{source}_{mol_type}"
            if mol_type == 'il':
                property_col_list = IL_PROPERTY_COLS
            else:  
                property_col_list = ION_PROPERTY_COLS

            data_list = databases.get(db_key, [])
            print(databases.keys())
            if not data_list:
                return JsonResponse({'error': f'Database for {db_key} ({mol_type}/{source}) not found or empty. Found {len(data_list)} entries.'}, status=404)

            
            results = topk_similar_smiles(
                query_smiles=query_smiles,
                data_list=data_list,
                topk=topk,
                method=method,
                property_col_list=property_col_list
            )

            response = JsonResponse({
                'results': results,
                'status': 'success',
                'query': {
                    'smiles': query_smiles,
                    'mol_type': mol_type,
                    'source': source,
                    'topk': topk,
                    'method': method
                }
            })
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            import traceback
            return JsonResponse({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def api_il_property_filter(request):
    """
    API endpoint for filtering ionic liquids by property ranges.
    Only supports IL (not cation/anion).

    Input (JSON):
        - ecw_range: [min, max] or null (Electrochemical Window in V)
        - conductivity_range: [min, max] or null (Conductivity in mS/cm)
        - tm_range: [min, max] or null (Melting point in K)
        - source: "experiment" or "generated"

    Note: Any range can be null (no constraint), or [min, null], or [null, max]

    Output (JSON):
        {
            "results": [
                {
                    "Name": "...",
                    "SMILES": "...",
                    "CAS": "...",
                    "properties": {
                        "ECW (V)": 4.5,
                        "Tm (K)": 320.5,
                        "Conductivity (mS/cm)": 15.2
                    }
                }
            ],
            "count": 156,
            "status": "success"
        }
    """
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    if request.method == 'POST':
        try:
            
            from ionic_liquid.ionic_liquid_utils import filter_il_by_property_ranges

            
            data = json.loads(request.body)
            ecw_range = data.get('ecw_range', None)
            conductivity_range = data.get('conductivity_range', None)
            tm_range = data.get('tm_range', None)
            source = data.get('source', 'experiment').strip().lower()

            
            if source not in ['experiment', 'generated']:
                return JsonResponse({'error': 'source must be "experiment" or "generated"'}, status=400)

            
            databases = _load_il_databases()

            
            results = filter_il_by_property_ranges(
                ecw_range=ecw_range,
                conductivity_range=conductivity_range,
                tm_range=tm_range,
                source=source,
                experiment_IL_data_list=databases.get('experiment_il', []),
                generated_IL_data_list=databases.get('generated_il', [])
            )

            response = JsonResponse({
                'results': results,
                'count': len(results),
                'status': 'success',
                'filters': {
                    'ecw_range': ecw_range,
                    'conductivity_range': conductivity_range,
                    'tm_range': tm_range,
                    'source': source
                }
            })
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            import traceback
            return JsonResponse({
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def ionic_liquid_analysis_page(request):
    """
    Display the main ionic liquid analysis page.
    This page provides:
    1. Similarity search interface (by SMILES)
    2. Property filter interface (by ECW, conductivity, melting point)
    """
    return render(request, 'ionic_liquid/ionic_liquid_analysis.html')


def download_il_output(request, filename):
    
    allowed_files = ['IL_output.csv', 'New_Cation.csv', 'New_Anion.csv']

    if filename not in allowed_files:
        return HttpResponse('文件不存在或无权访问', status=404)

    
    file_path = os.path.join(settings.MEDIA_ROOT, filename)

    
    if not os.path.exists(file_path):
        return HttpResponse(f'文件 {filename} 不存在', status=404)

    
    try:
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    except Exception as e:
        return HttpResponse(f'下载文件时出错: {str(e)}', status=500)


def download_il_template(request, template_type):
    template_dir = os.path.join(settings.BASE_DIR, 'ionic_liquid', 'views_utils')

    template_files = {
        'cation': 'Cation_core_backbone.xlsx',
        'anion': 'Anion_core_backbone.xlsx'
    }

    if template_type not in template_files:
        return HttpResponse('模板类型不存在', status=404)

    filename = template_files[template_type]
    file_path = os.path.join(template_dir, filename)

    
    if not os.path.exists(file_path):
        return HttpResponse(f'模板文件 {filename} 不存在', status=404)

    
    try:
        with open(file_path, 'rb') as f:
            response = HttpResponse(
                f.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    except Exception as e:
        return HttpResponse(f'下载模板时出错: {str(e)}', status=500)


DATABASE_EXPORT_FILES = {
    'Cation_QC_data': 'Cation_QC_data.xlsx',
    'Anion_QC_data': 'Anion_QC_data.xlsx',
    'IL_Tm_conductivity_ECW_data': 'IL_Tm_conductivity_ECW_data.xlsx',
    'IL_ML_data': 'IL_ML_data.xlsx',
}


def _build_export_file_response(filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'ionic_liquid', 'Database_full', filename)
    if not os.path.exists(file_path):
        return None

    response = FileResponse(
        open(file_path, 'rb'),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@csrf_exempt
def download_database_export_file(request, filename):
    if filename not in DATABASE_EXPORT_FILES.values():
        raise Http404("File not allowed")

    response = _build_export_file_response(filename)
    if response is None:
        raise Http404("Export file not found. Please run update_database_exports.py first")

    return response





DIST_DIR = Path(settings.BASE_DIR) / 'ionic_liquid' / 'dist'
ASSETS_DIR = DIST_DIR / 'assets'

def spa_index(request):
    """Serve Vue SPA index.html for all frontend routes"""
    index_path = DIST_DIR / 'index.html'
    if not index_path.exists():
        return HttpResponse("Build not found. Run `npm run build`.", status=404)
    return FileResponse(open(index_path, 'rb'), content_type='text/html; charset=utf-8')

def spa_assets(request, path: str):
    """Serve Vue build assets (JS/CSS/images) with proper MIME types"""
    file_path = (ASSETS_DIR / path).resolve()
    if not str(file_path).startswith(str(ASSETS_DIR.resolve())):
        raise Http404
    if not file_path.is_file():
        raise Http404

    ctype, _ = mimetypes.guess_type(str(file_path))
    resp = FileResponse(open(file_path, 'rb'), content_type=ctype or 'application/octet-stream')
    resp['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resp

def spa_static(request, filename: str):
    """Serve static files from dist root (RDKit, templates)"""
    allowed_files = {
        'RDKit_minimal.js',
        'RDKit_minimal.wasm',
        'Cation_core.xlsx',
        'Cation_backbone.xlsx',
        'Anion_core.xlsx',
        'Anion_backbone.xlsx',
        'Ionic_liquid_list.xlsx'
    }

    if filename not in allowed_files:
        raise Http404(f"File '{filename}' not allowed")

    file_path = (DIST_DIR / filename).resolve()

    
    if not str(file_path).startswith(str(DIST_DIR.resolve())):
        raise Http404
    if not file_path.is_file():
        raise Http404

    ctype, _ = mimetypes.guess_type(str(file_path))
    if filename.endswith('.wasm'):
        ctype = 'application/wasm'
    resp = FileResponse(
        open(file_path, 'rb'), 
        content_type=ctype or 'application/octet-stream'
        )
    resp['Cache-Control'] = 'public, max-age=3600'
    return resp
