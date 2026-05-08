import os
import shutil
import subprocess
import zipfile
from threading import Thread
import time
import traceback
from autocompute.models import ComputeTask
from autocompute.failure_utils import mark_task_failed
from home.md_previews import build_md_preview_manifest
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
import logging  
from django.conf import settings  
from django.db import transaction  
import json  
from autocompute.remote_utils import select_least_utilized_remote_server

MAX_RUNNING_LENGTH=6 

REMOTE_MAX_RUNNING_LENGTH=18 

import logging
logger = logging.getLogger('django')



def check_and_execute_task(task_func, source_dir, download_dir, task, MAX_RUNNING_LENGTH=MAX_RUNNING_LENGTH):
    while True:
        time.sleep(1)
        
        
        
        running_cnt = (ComputeTask.objects
                        .filter(status='pending', remote_type='local')  
                        .count())                                        

        
        if running_cnt >= MAX_RUNNING_LENGTH:
            
            if task.status != 'queuing':
                task.status = 'queuing'
                task.save(update_fields=['status'])
            continue

        
        
        top_task = (ComputeTask.objects
                    .filter(status='queuing', remote_type='local')
                    .order_by('-priority', 'created_at')
                    .first())

        
        if top_task is None:
            top_task = task                 

        
        if top_task.task_id == task.task_id:
            with transaction.atomic():
                
                task.refresh_from_db() 
                task.status = 'pending'
                task.save(update_fields=['status'])

            
            task_func(source_dir, download_dir, task)
            break

        
        continue



def run_task_immediately(task_func, source_dir, download_dir, task):
    from django.db import transaction  

    
    with transaction.atomic():                 
        task.refresh_from_db()                 
        task.status = 'pending'                
        task.save(update_fields=['status'])    

    
    try:
        task_func(source_dir, download_dir, task)  
    except Exception as e:                          
        mark_task_failed(
            task,
            f'{type(e).__name__}: {e}',
            write_failure_file=True,
            failure_dir=download_dir,
            create_failure_dir=True,
            overwrite_failure_file=False,
        )
        raise                                       

    
    
    
    
    

    return task                                     






def decide_run_location(local_limit=MAX_RUNNING_LENGTH,       
                        remote_limit=REMOTE_MAX_RUNNING_LENGTH 
                        ) -> str:

    
    PENDING_STATUS = 'pending'                           

    
    with transaction.atomic():
        
        local_pending = (ComputeTask.objects
                         .filter(remote_type='local', status=PENDING_STATUS)
                         .count())

        
        remote_pending = (ComputeTask.objects
                          .filter(remote_type='remote', status=PENDING_STATUS)
                          .count())

        logger.info(f"local_pending: {local_pending}, remote_pending: {remote_pending}")
        
        if remote_pending < remote_limit: 
            return 'remote'
        if local_pending < local_limit:  
            return 'local'
        return 'local'  

def decide_remote_server(
    server_info_file_path=os.path.join(  
        settings.BASE_DIR, 'static', 'remote_server_info', 'remote_server_info.json'
    ),
):
    selected_server = select_least_utilized_remote_server(
        server_info_file_path=server_info_file_path,
    )
    if selected_server is not None:
        return {
            "server_name": selected_server["server_name"],
            "IP": selected_server["IP"],
            "remote_target_dir": selected_server["remote_target_dir"],
        }

    
    return {
        'server_name': "local",  
        'IP': "user@<PRIVATE_HOST>:",  
        'remote_target_dir': '/path/to/example/media',  
    }



def run_Gromacs_MD_notebook_tasks(source_dir, download_dir, task):
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    notebooks_to_run = [
        '1_Polymer_RESP_repeat_unit.ipynb',
        '2_Polymer_chg_and_Polymer_creation_ Linear_polymer.ipynb',
        '3_create_Polymer_itp_top.ipynb',
        '4_generate_Gaussian_inputfile.ipynb',
        '5_opt+freq_calculation.ipynb',
        '6_opt+freq_failure_correction.ipynb',
        '7_opt+freq_imaginary_frequencies.ipynb',
        '8_MD_process.ipynb',
        '9_post_analysis.ipynb',
        '11_component_energy_calculation.ipynb',
        '12_calculate_solvent_cage_escape_energy.ipynb',
        '13_coordination_environment_distribution.ipynb',
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
            
            error_output = f"Error running notebook: {notebook_name}\n"
            error_output += f"Return code: {e.returncode}\n"
            error_output += f"Standard output:\n{e.stdout}\n"
            error_output += f"Standard error:\n{e.stderr}\n"
            
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(error_output)

            
            task.status = 'failed'
            task.save()
            return

        except Exception as e:
            
            error_message = f"An unexpected error occurred while running {notebook_name}: {str(e)}\n"
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(error_message)
            
            task.status = 'failed'
            task.save()
            return

    
    
    
    try:
        build_md_preview_manifest(download_dir=download_dir, force_rebuild=True)
    except Exception as exc:
        logger.warning("Failed to build MD query previews for %s: %s", download_dir, exc)

    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    task.status = 'success'
    task.save()


def run_Gromacs_MD_notebook_tasks_ORCA(source_dir, download_dir, task):
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    notebooks_to_run = [
        '1_Polymer_RESP_repeat_unit.ipynb',
        '2_Polymer_chg_and_Polymer_creation_ Linear_polymer.ipynb',
        '3_create_Polymer_itp_top.ipynb',
        '4_generate_Gaussian_inputfile.ipynb',
        '5_opt+freq_calculation.ipynb',
        '6_opt+freq_imaginary_frequencies.ipynb',
        '8_MD_process.ipynb',
        '9_post_analysis.ipynb',
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
            
            error_output = f"Error running notebook: {notebook_name}\n"
            error_output += f"Return code: {e.returncode}\n"
            error_output += f"Standard output:\n{e.stdout}\n"
            error_output += f"Standard error:\n{e.stderr}\n"
            
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(error_output)

            
            task.status = 'failed'
            task.save()
            return

        except Exception as e:
            
            error_message = f"An unexpected error occurred while running {notebook_name}: {str(e)}\n"
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(error_message)
            
            task.status = 'failed'
            task.save()
            return

    try:
        build_md_preview_manifest(download_dir=download_dir, force_rebuild=True)
    except Exception as exc:
        logger.warning("Failed to build MD query previews for %s: %s", download_dir, exc)

    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    task.status = 'success'
    task.save()


def run_Gaussian_single_point_energy_notebook_tasks(source_dir, download_dir, task): 
    
    
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = [
        'Gas_component_1_generate_Gaussian_inputfile.ipynb',
        'Gas_component_2_opt+freq_calculation.ipynb',
        'Gas_component_3_opt+freq_failure_correction.ipynb',
        'Gas_component_4_opt+freq_imaginary_frequencies.ipynb',
        'Gas_component_5_energy_calculation.ipynb',
        'Gas_component_6_energy_failure_correction.ipynb',
        'Gas_component_7_Extracting_energy_and_free_energy_corrections.ipynb'
    ]

    
    try:
        for notebook_name in notebooks_to_run:
            notebook_path = os.path.join(download_dir, notebook_name)
            subprocess.run(
                ["jupyter", "nbconvert", "--to", "notebook", "--execute",
                "--output", notebook_path, notebook_path],
                check=True, timeout=None, capture_output=True, text=True
            )

        
        success_signal = os.path.join(download_dir, 'success.txt')
        with open(success_signal, 'w') as success_file:
            success_file.write("All notebooks executed successfully.")
        
        
        task.status = 'success'
        task.save()

    except subprocess.CalledProcessError as e:
        
        failure_signal = os.path.join(download_dir, 'failure.txt')
        with open(failure_signal, 'w') as failure_file:
            failure_file.write(f"Failed to run notebook: {str(e)}")
        
        
        task.status = 'failed'
        task.save()

    except Exception as e:
        
        failure_signal = os.path.join(download_dir, 'failure.txt')
        with open(failure_signal, 'w') as failure_file:
            failure_file.write(f"Failed to run notebook: {str(e)}")
        
        
        task.status = 'failed'
        task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        opt_dir = os.path.join(download_dir, 'opt+freq')
        for root, dirs, files in os.walk(opt_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
        
        
        energy_dir = os.path.join(download_dir, 'energy')
        for root, dirs, files in os.walk(energy_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
                

def run_ORCA_single_point_energy_notebook_tasks(source_dir, download_dir, task):
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = [
        'ORCA_Gas_1_generate_ORCA_inputfile.ipynb',
        'ORCA_Gas_2_opt+freq_calculation.ipynb',
        'ORCA_Gas_3_opt+freq_imaginary_frequencies.ipynb',
        'ORCA_Gas_4_energy_calculation.ipynb',
        'ORCA_Gas_5_Extracting_energy_and_free_energy_corrections.ipynb',
    ]

    
    try:
        for notebook_name in notebooks_to_run:
            notebook_path = os.path.join(download_dir, notebook_name)
            subprocess.run(
                ["jupyter", "nbconvert", "--to", "notebook", "--execute",
                "--output", notebook_path, notebook_path],
                check=True, timeout=None, capture_output=True, text=True
            )

        
        success_signal = os.path.join(download_dir, 'success.txt')
        with open(success_signal, 'w') as success_file:
            success_file.write("All notebooks executed successfully.")
        
        
        task.status = 'success'
        task.save()

    except subprocess.CalledProcessError as e:
        
        failure_signal = os.path.join(download_dir, 'failure.txt')
        with open(failure_signal, 'w') as failure_file:
            failure_file.write(f"Failed to run notebook: {str(e)}")
        
        
        task.status = 'failed'
        task.save()

    except Exception as e:
        
        failure_signal = os.path.join(download_dir, 'failure.txt')
        with open(failure_signal, 'w') as failure_file:
            failure_file.write(f"Failed to run notebook: {str(e)}")
        
        
        task.status = 'failed'
        task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        opt_dir = os.path.join(download_dir, 'opt+freq')
        for root, dirs, files in os.walk(opt_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
        
        
        energy_dir = os.path.join(download_dir, 'energy')
        for root, dirs, files in os.walk(energy_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))


def run_Gaussian_binding_energy_notebook_tasks(source_dir, download_dir, task):
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['Gas_component_1_generate_Gaussian_inputfile.ipynb', 'Gas_component_2_opt+freq_calculation.ipynb'
                    , 'Gas_component_3_opt+freq_failure_correction.ipynb', 'Gas_component_4_opt+freq_imaginary_frequencies.ipynb', 'Gas_component_5_energy_calculation.ipynb'
                    , 'Gas_component_6_energy_failure_correction.ipynb', 'Gas_component_7_Extracting_energy_and_free_energy_corrections.ipynb', 'Gas_dimer_1_generate_Gaussian_inputfile.ipynb'
                    , 'Gas_dimer_2_opt+freq_calculation.ipynb', 'Gas_dimer_3_opt+freq_failure_correction.ipynb', 'Gas_dimer_4_opt+freq_imaginary_frequencies.ipynb'
                    , 'Gas_dimer_5_energy_calculation.ipynb', 'Gas_dimer_6_energy_failure_correction.ipynb', 'Gas_dimer_7_Extracting_energy_and_free_energy_corrections.ipynb'
                    , 'Data_processing .ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        component_dir = os.path.join(download_dir, 'component_gas')
        for root, dirs, files in os.walk(component_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
        
        
        dimer_dir = os.path.join(download_dir, 'dimer_gas')
        for root, dirs, files in os.walk(dimer_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
                

def run_ORCA_binding_energy_notebook_tasks(source_dir, download_dir, task):
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['ORCA_Gas_component_1_generate_ORCA_inputfile.ipynb', 'ORCA_Gas_component_2_opt+freq_calculation.ipynb'
                    , 'ORCA_Gas_component_3_opt+freq_imaginary_frequencies.ipynb', 'ORCA_Gas_component_4_energy_calculation.ipynb', 'ORCA_Gas_component_5_Extracting_energy_and_free_energy_corrections.ipynb'
                    , 'ORCA_Gas_dimer_1_generate_ORCA_inputfile.ipynb', 'ORCA_Gas_dimer_2_opt+freq_calculation.ipynb', 'ORCA_Gas_dimer_3_opt+freq_imaginary_frequencies.ipynb'
                    , 'ORCA_Gas_dimer_4_energy_calculation.ipynb', 'ORCA_Gas_dimer_5_Extracting_energy_and_free_energy_corrections.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        component_dir = os.path.join(download_dir, 'component_gas')
        for root, dirs, files in os.walk(component_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
        
        
        dimer_dir = os.path.join(download_dir, 'dimer_gas')
        for root, dirs, files in os.walk(dimer_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
                
                

def run_Gaussian_pka_pkb_notebook_tasks(source_dir, download_dir, task):
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = [ 'pkb_DFT_1_generate_Gaussian_inputfile.ipynb', 'pkb_DFT_2_opt+freq_calculation.ipynb', 'pkb_DFT_3_opt+freq_failure_correction.ipynb'
                    , 'pkb_DFT_4_opt+freq_imaginary_frequencies.ipynb', 'pkb_DFT_5_energy_calculation.ipynb', 'pkb_DFT_6_energy_failure_correction.ipynb'
                    , 'pkb_DFT_7_Extracting_energy_and_free_energy_corrections.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')


    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        opt_dir = os.path.join(download_dir, 'opt+freq')
        for root, dirs, files in os.walk(opt_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
        
        
        energy_dir = os.path.join(download_dir, 'energy')
        for root, dirs, files in os.walk(energy_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))


def run_Gaussian_ox_red_notebook_tasks(source_dir, download_dir, task):
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['ox_red_1_generate_Gaussian_inputfile.ipynb', 'ox_red_2_opt+freq_calculation.ipynb'
            , 'ox_red_3_opt+freq_failure_correction.ipynb', 'ox_red_4_opt+freq_imaginary_frequencies.ipynb', 'ox_red_5_energy_calculation.ipynb'
            , 'ox_red_6_energy_failure_correction.ipynb', 'ox_red_7_Extracting_energy_and_free_energy_corrections.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')


    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        opt_dir = os.path.join(download_dir, 'opt+freq')
        for root, dirs, files in os.walk(opt_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
        
        
        energy_dir = os.path.join(download_dir, 'energy')
        for root, dirs, files in os.walk(energy_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))


def run_ORCA_ox_red_notebook_tasks(source_dir, download_dir, task):
    
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['ORCA_ox_red_1_generate_ORCA_inputfile.ipynb', 'ORCA_ox_red_2_opt+freq_calculation.ipynb'
            , 'ORCA_ox_red_3_opt+freq_imaginary_frequencies.ipynb', 'ORCA_ox_red_4_energy_calculation.ipynb'
            , 'ORCA_ox_red_5_Extracting_energy_and_free_energy_corrections.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')


    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        opt_dir = os.path.join(download_dir, 'opt+freq')
        for root, dirs, files in os.walk(opt_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
        
        
        energy_dir = os.path.join(download_dir, 'energy')
        for root, dirs, files in os.walk(energy_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
                

def run_Gaussian_reaction_thermo_notebook_tasks(source_dir, download_dir, task):
    
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['reaction_thermo_1_generate_Gaussian_inputfile.ipynb', 'reaction_thermo_2_opt+freq_calculation.ipynb'
                    , 'reaction_thermo_3_opt+freq_failure_correction.ipynb', 'reaction_thermo_4_opt+freq_imaginary_frequencies.ipynb', 'reaction_thermo_5_energy_calculation.ipynb'
                    , 'reaction_thermo_6_Extracting_energy_and_free_energy_corrections.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')


    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        opt_dir = os.path.join(download_dir, 'opt+freq')
        for root, dirs, files in os.walk(opt_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
        
        
        energy_dir = os.path.join(download_dir, 'energy')
        for root, dirs, files in os.walk(energy_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
                

def run_Gaussian_global_reaction_properties_notebook_tasks(source_dir, download_dir, task):
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['reaction_1_generate_Gaussian_inputfile.ipynb', 'reaction_2_opt+freq_calculation.ipynb'
                    , 'reaction_3_opt+freq_failure_correction.ipynb', 'reaction_4_opt+freq_imaginary_frequencies.ipynb', 'reaction_5_energy_calculation.ipynb'
                    , 'reaction_6_Extracting_energy_and_free_energy_corrections.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        opt_dir = os.path.join(download_dir, 'opt+freq')
        for root, dirs, files in os.walk(opt_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
        
        
        energy_dir = os.path.join(download_dir, 'energy')
        for root, dirs, files in os.walk(energy_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
                
        
        fukui_dir = os.path.join(download_dir, 'fukui')
        for root, dirs, files in os.walk(fukui_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))            
                

def run_ORCA_manual_notebook_tasks(source_dir, download_dir, task):
    
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = [
        'ORCA_Gas_2_opt+freq_calculation.ipynb',
        'ORCA_Gas_3_opt+freq_imaginary_frequencies.ipynb',
        'ORCA_Gas_4_energy_calculation.ipynb',
        'ORCA_Gas_5_Extracting_energy_and_free_energy_corrections.ipynb',
    ]

    
    try:
        for notebook_name in notebooks_to_run:
            notebook_path = os.path.join(download_dir, notebook_name)
            subprocess.run(
                ["jupyter", "nbconvert", "--to", "notebook", "--execute",
                "--output", notebook_path, notebook_path],
                check=True, timeout=None, capture_output=True, text=True
            )

        
        success_signal = os.path.join(download_dir, 'success.txt')
        with open(success_signal, 'w') as success_file:
            success_file.write("All notebooks executed successfully.")
        
        
        task.status = 'success'
        task.save()

    except subprocess.CalledProcessError as e:
        
        failure_signal = os.path.join(download_dir, 'failure.txt')
        with open(failure_signal, 'w') as failure_file:
            failure_file.write(f"Failed to run notebook: {str(e)}")
        
        
        task.status = 'failed'
        task.save()

    except Exception as e:
        
        failure_signal = os.path.join(download_dir, 'failure.txt')
        with open(failure_signal, 'w') as failure_file:
            failure_file.write(f"Failed to run notebook: {str(e)}")
        
        
        task.status = 'failed'
        task.save()

    
    zip_filename = os.path.join(download_dir, 'all_results.zip')
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        
        opt_dir = os.path.join(download_dir, 'opt+freq')
        for root, dirs, files in os.walk(opt_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
        
        
        energy_dir = os.path.join(download_dir, 'energy')
        for root, dirs, files in os.walk(energy_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), download_dir))
                


def run_draw_ESP_notebook_tasks(source_dir, download_dir, task):
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['auto_draw_ESP.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    
    
    original_zip_name = 'original_draw_file.zip'
    original_zip_path = os.path.join(download_dir, original_zip_name)
    with zipfile.ZipFile(original_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(download_dir):
            for fname in files:
                if fname.lower().endswith(('.fchk', '.cub', '.vmd')):
                    full_path = os.path.join(root, fname)
                    
                    rel_path = os.path.relpath(full_path, download_dir)
                    zipf.write(full_path, rel_path)

    
    esp_zip_name = 'ESP_fig_file.zip'
    esp_zip_path = os.path.join(download_dir, esp_zip_name)
    with zipfile.ZipFile(esp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(download_dir):
            for fname in files:
                if fname.lower().endswith('.tga'):
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, download_dir)
                    zipf.write(full_path, rel_path)


def run_draw_ESP_notebook_tasks_gbw(source_dir, download_dir, task):
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['auto_draw_ESP_gbw.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    
    
    original_zip_name = 'original_draw_file.zip'
    original_zip_path = os.path.join(download_dir, original_zip_name)
    with zipfile.ZipFile(original_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(download_dir):
            for fname in files:
                if fname.lower().endswith(('.fchk', '.cub', '.vmd')):
                    full_path = os.path.join(root, fname)
                    
                    rel_path = os.path.relpath(full_path, download_dir)
                    zipf.write(full_path, rel_path)

    
    esp_zip_name = 'ESP_fig_file.zip'
    esp_zip_path = os.path.join(download_dir, esp_zip_name)
    with zipfile.ZipFile(esp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(download_dir):
            for fname in files:
                if fname.lower().endswith('.tga'):
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, download_dir)
                    zipf.write(full_path, rel_path)



def run_draw_HOMO_LUMO_orb_notebook_tasks(source_dir, download_dir, task):
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['draw_HOMO_LUMO_orb.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    
    
    original_zip_name = 'original_draw_file.zip'
    original_zip_path = os.path.join(download_dir, original_zip_name)
    with zipfile.ZipFile(original_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(download_dir):
            for fname in files:
                if fname.lower().endswith(('.fchk', '.cub', '.vmd', '.molden')):
                    full_path = os.path.join(root, fname)
                    
                    rel_path = os.path.relpath(full_path, download_dir)
                    zipf.write(full_path, rel_path)

    
    orb_zip_name = 'HOMO_LUMO_orb_fig_file.zip'
    orb_zip_path = os.path.join(download_dir, orb_zip_name)
    with zipfile.ZipFile(orb_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(download_dir):
            for fname in files:
                if fname.lower().endswith('.tga'):
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, download_dir)
                    zipf.write(full_path, rel_path)



def run_NCI_SCF_analysis_notebook_tasks(source_dir, download_dir, task):
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['NCI_analysis.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    
    
    original_zip_name = 'original_draw_file.zip'
    original_zip_path = os.path.join(download_dir, original_zip_name)
    with zipfile.ZipFile(original_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(download_dir):
            for fname in files:
                if fname.lower().endswith(('.fchk', '.cub', '.vmd', '.molden', '.csv')):
                    full_path = os.path.join(root, fname)
                    
                    rel_path = os.path.relpath(full_path, download_dir)
                    zipf.write(full_path, rel_path)

    
    nci_zip_name = 'nci_fig_file.zip'
    nci_zip_path = os.path.join(download_dir, nci_zip_name)
    with zipfile.ZipFile(nci_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(download_dir):
            for fname in files:
                if fname.lower().endswith(('.tga', '.png')):
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, download_dir)
                    zipf.write(full_path, rel_path)



def run_NCI_promolecular_analysis_notebook_tasks(source_dir, download_dir, task):
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    notebooks_to_run = ['NCI_analysis_promolecular.ipynb']

    
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
                failure_file.write(f"Failed to run notebook: {str(e)}")

            
            task.status = 'failed'
            task.save()

            
            error_message = f'Failed to run notebook: {str(e)}'
            stdout_output = e.stdout 
            stderr_output = e.stderr 
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str, 'stdout': stdout_output, 'stderr': stderr_output}, status=500)
        
        except Exception as e:
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(f"Failed to run notebook: {str(e)}")
            
            
            task.status = 'failed'
            task.save()
            
            
            error_message = f'An error occurred: {str(e)}'
            traceback_str = traceback.format_exc()  
            return JsonResponse({'error': error_message, 'traceback': traceback_str}, status=500)
    
    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    
    
    task.status = 'success'
    task.save()

    
    
    
    original_zip_name = 'original_draw_file.zip'
    original_zip_path = os.path.join(download_dir, original_zip_name)
    with zipfile.ZipFile(original_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(download_dir):
            for fname in files:
                if fname.lower().endswith(('.fchk', '.cub', '.vmd', '.molden', '.csv', ".pdb", ".xyz", ".mol", ".mol2")):
                    full_path = os.path.join(root, fname)
                    
                    rel_path = os.path.relpath(full_path, download_dir)
                    zipf.write(full_path, rel_path)

    
    nci_zip_name = 'nci_fig_file.zip'
    nci_zip_path = os.path.join(download_dir, nci_zip_name)
    with zipfile.ZipFile(nci_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(download_dir):
            for fname in files:
                if fname.lower().endswith(('.tga', '.png')):
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, download_dir)
                    zipf.write(full_path, rel_path)



def run_query_name_CAS_tasks(source_dir, download_dir, task):
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    notebooks_to_run = [
        'query_simliar_monomer.ipynb',
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
            
            error_output = f"Error running notebook: {notebook_name}\n"
            error_output += f"Return code: {e.returncode}\n"
            error_output += f"Standard output:\n{e.stdout}\n"
            error_output += f"Standard error:\n{e.stderr}\n"
            
            
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(error_output)

            
            task.status = 'failed'
            task.save()
            return

        except Exception as e:
            
            error_message = f"An unexpected error occurred while running {notebook_name}: {str(e)}\n"
            failure_signal = os.path.join(download_dir, 'failure.txt')
            with open(failure_signal, 'w') as failure_file:
                failure_file.write(error_message)
            
            task.status = 'failed'
            task.save()
            return

    
    success_signal = os.path.join(download_dir, 'success.txt')
    with open(success_signal, 'w') as success_file:
        success_file.write("All notebooks executed successfully.")
    task.status = 'success'
    task.save()
