import pandas as pd
import re
from rdkit import Chem
import pubchempy as pcp
import os
from cryptography.fernet import Fernet  
import json
from django.conf import settings 
from django.shortcuts import render
from django.http import JsonResponse, Http404 
import os
from django.conf import settings 
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
from django.core.paginator import Paginator


from rest_framework import generics
from rest_framework.permissions import IsAuthenticated 
import re
import mimetypes
from urllib.parse import unquote_plus  
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import io
from autocompute.models import ComputeTask  
import logging

logger = logging.getLogger('django')  


def decrypt_download_url_list(encrypted_id):
    cipher_suite = Fernet(settings.FERNET_SECRET_KEY)
    
    try:
        
        decrypted = cipher_suite.decrypt(encrypted_id.encode('utf-8'))

        
        download_url_list = json.loads(decrypted.decode('utf-8'))

        return download_url_list
    except Exception as e:
        
        print(f"解密失败: {str(e)}")
        return None


def generate_polymer_run_notebook_tasks(source_dir, download_dir, task):
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['1_Polymer_RESP_repeat_unit.ipynb', 
                        '2_Polymer_chg_and_Polymer_creation_ Linear_polymer.ipynb', 
                        '3_create_Polymer_itp_top.ipynb',
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
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {notebook_name}\n")
                failure_file.write(f"Return Code: {e.returncode}\n")
                failure_file.write(f"Standard Output:\n{e.stdout}\n")
                failure_file.write(f"Standard Error:\n{e.stderr}\n")

            
            task.status = 'failed'
            task.save()

            
            logger.error(f"Failed to run notebook {notebook_name}: {e.stderr}")

            
            task.error_message = e.stderr
            task.save()

        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"An unexpected error occurred while running notebook: {notebook_name}\n")
                failure_file.write(f"Error Message: {str(e)}\n")
                failure_file.write(f"Traceback:\n{traceback.format_exc()}\n")  

            
            task.status = 'failed'
            task.save()

            
            logger.error(f"An unexpected error occurred while running notebook {notebook_name}: {str(e)}")

            
            task.error_message = str(e)
            task.save()
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')

    
    structure_dir = os.path.join(download_dir, 'polymer_structure')
    topology_dir = os.path.join(download_dir, 'polymer_topology')

    
    if not os.path.exists(structure_dir):
        os.makedirs(structure_dir)
    if not os.path.exists(topology_dir):
        os.makedirs(topology_dir)

    
    structure_extensions = ('.xyz', '.pdb', '.mol2')
    topology_extensions = ('.top', '.itp', '.chg')

    
    for root, dirs, files in os.walk(download_dir):
        
        if root == download_dir:
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(structure_extensions):
                    
                    shutil.move(file_path, structure_dir)
                elif file.endswith(topology_extensions):
                    
                    shutil.move(file_path, topology_dir)

    
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        for root, dirs, files in os.walk(structure_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                zipf.write(file_path, os.path.relpath(file_path, download_dir))
        
        
        for root, dirs, files in os.walk(topology_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, download_dir))

