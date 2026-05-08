import os          
import json        
import shutil      
import shlex       
import posixpath   
import subprocess  
import traceback   
from django.http import JsonResponse  

import logging
logger = logging.getLogger('django')  
from autocompute.remote_utils import (
    _build_rsync_remote_prefix,
    _build_ssh_command,
    _resolve_remote_connection_info,
    _write_worker_heartbeat_signal,
    _write_worker_result_signal,
)

remote_IP = "user@<PRIVATE_HOST>:"


def run_task_immediately_remote(task_func, source_dir, download_dir, task, remote_target, remote_IP = remote_IP):
    from django.db import transaction  
    
    
    with transaction.atomic():                 
        task.refresh_from_db()                 
        task.status = 'pending'                
        task.save(update_fields=['status'])    

    
    try:
        
        result = task_func(source_dir, download_dir, task, remote_target, remote_IP=remote_IP)

        
        if isinstance(result, JsonResponse):                         
            status_code = getattr(result, 'status_code', 200)        
            if status_code >= 400:                                   
                
                task.status = 'failed'                               
                if hasattr(task, 'error_message'):                   
                    
                    try:
                        detail = result.content.decode('utf-8', errors='ignore')
                    except Exception:
                        detail = 'Remote task returned HTTP error'
                    task.error_message = f'HTTP {status_code}: {detail[:2000]}'  
                    task.save(update_fields=['status', 'error_message'])          
                else:
                    task.save(update_fields=['status'])                           
                
                return task                                                      
        
        
    except Exception as e:                                     
        try:
            task.status = 'failed'                             
            if hasattr(task, 'error_message'):                 
                
                task.error_message = f'{type(e).__name__}: {e}'
                task.save(update_fields=['status', 'error_message'])
            else:
                task.save(update_fields=['status'])            
        except Exception:
            pass                                               
        raise                                                  

    return task                                                


def _pull_remote_to_local(remote_IP, remote_work_dir, abs_download_dir):
    remote_src_prefix, ssh_transport = _build_rsync_remote_prefix(remote_IP)
    remote_src = remote_src_prefix + remote_work_dir.rstrip("/")
    pull_cmd = [
        "rsync", "-avz", "--delete", "-I",
        "-e", ssh_transport,
        remote_src + "/",
        os.path.abspath(abs_download_dir).rstrip("/") + "/"
    ]
    subprocess.run(pull_cmd, check=True)


def _ssh_run(remote_login: str, cmd: str, timeout=None):
    
    script = "set -euo pipefail\n"  
    script += (cmd.rstrip() + "\n") 
    script += "exit\n"              

    
    ssh_cmd = _build_ssh_command(
        remote_login,
        batch_mode=True,
        allocate_tty=True,
    )

    
    return subprocess.run(
        ssh_cmd,
        input=script,               
        text=True,                  
        capture_output=True,        
        check=True,                 
        timeout=timeout             
    )


def copy_unique_folder(download_dir: str,
                       remote_target: str, 
                       remote_IP=remote_IP):

    
    abs_download_dir = os.path.abspath(download_dir)  

    
    if not os.path.exists(abs_download_dir):          
        os.makedirs(abs_download_dir)                 

    
    remote_login, _, _ = _resolve_remote_connection_info(remote_IP)
    remote_ip, ssh_transport = _build_rsync_remote_prefix(remote_IP)

    
    
    mkdir_cmd = _build_ssh_command(
        remote_login,
        batch_mode=True,
        allocate_tty=False,
    ) + [f"mkdir -p {shlex.quote(remote_target)}"]

    
    try:
        subprocess.run(mkdir_cmd, check=True)         
    except subprocess.CalledProcessError as e:        
        print(f"❌ 远程目录创建失败：{e}")             
        return                                        

    
    
    rsync_cmd = [
        "rsync", "-avz",                              
        "-e", ssh_transport,                          
        abs_download_dir,                             
        remote_ip + remote_target                     
    ]

    
    try:
        subprocess.run(rsync_cmd, check=True)         
        print(f"✅ Successfully copied {abs_download_dir} to {remote_login}:{remote_target}")  
    except subprocess.CalledProcessError as e:        
        print(f"❌ rsync failed: {e}")                

def _write_local_signal_file(download_dir: str, filename: str, content: str) -> None:

    os.makedirs(download_dir, exist_ok=True)
    with open(os.path.join(download_dir, filename), "w", encoding="utf-8") as handle:
        handle.write(content.rstrip() + "\n")


def _signal_polymer_worker_progress(download_dir: str, scheduler_managed: bool, stage: str, detail: str = "") -> None:

    if scheduler_managed:
        _write_worker_heartbeat_signal(download_dir, stage=stage, detail=detail)


def generate_polymer_run_notebook_tasks_remote(
    source_dir,
    download_dir,
    task,
    remote_target,
    remote_IP=remote_IP,
    scheduler_managed=False,
):
    
    
    
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    
    
    copy_unique_folder(download_dir,
                       remote_target=remote_target,
                       remote_IP=remote_IP)
    _signal_polymer_worker_progress(download_dir, scheduler_managed, "copy_to_remote_done")

    
    abs_download_dir = os.path.abspath(download_dir)                                 
    remote_work_dir = posixpath.join(                                                
        remote_target.rstrip("/"),                                                   
        os.path.basename(abs_download_dir)                                           
    )

    
    remote_login = remote_IP[:-1] if remote_IP.endswith(":") else remote_IP          

    
    
    
    
    notebooks_to_run = [
        '1_Polymer_RESP_repeat_unit.ipynb',
        '2_Polymer_chg_and_Polymer_creation_Linear_polymer.ipynb',
        '3_create_Polymer_itp_top.ipynb',
    ]

    error_info = None  

    
    for notebook_name in notebooks_to_run:                                                        
        _signal_polymer_worker_progress(
            download_dir,
            scheduler_managed,
            "notebook_start",
            notebook_name,
        )
        
        
        
        run_cmd = (
            f"cd {shlex.quote(remote_work_dir)} && "
            f"nb={shlex.quote(notebook_name)}; "                      
            f'log="${{nb}}.log"; '                                    
            "export PYTHONUNBUFFERED=1; "                             
            "stdbuf -oL -eL "                                         
            "jupyter nbconvert --to notebook --execute "
            "--ExecutePreprocessor.timeout=None "
            f"--output {shlex.quote(notebook_name)} {shlex.quote(notebook_name)} "
            '2>&1 | tee -a "${log}"'                                  
        )

        try:
            _ssh_run(remote_login, run_cmd)                                                       
            _signal_polymer_worker_progress(
                download_dir,
                scheduler_managed,
                "notebook_success",
                notebook_name,
            )

        except subprocess.CalledProcessError as e:                                                
            
            failure_msg = f"Failed to run notebook {notebook_name}: {e.stderr or e.stdout or str(e)}"  
            echo_fail = (
                f"cd {shlex.quote(remote_work_dir)} && "                                          
                f"printf '%s\\n' {shlex.quote(failure_msg)} > failure.txt"                        
            )
            try:
                _ssh_run(remote_login, echo_fail)                                                 
                
                append_log_tail = (
                    f"cd {shlex.quote(remote_work_dir)} && "
                    
                    f"printf '\\n===== TAIL of {shlex.quote(notebook_name)}.log (last 200 lines) =====\\n' >> failure.txt; "
                    
                    f"test -s {shlex.quote(notebook_name + '.log')} && tail -n 200 {shlex.quote(notebook_name + '.log')} >> failure.txt || true"
                )
                try:
                    _ssh_run(remote_login, append_log_tail)
                except Exception:
                    pass
            except Exception:
                pass                                                                              

            
            if not scheduler_managed:
                task.status = 'failed'                                                            
                task.save()                                                                       

            error_message = f'Failed to run notebook on remote: {str(e)}'                         
            stdout_output = e.stdout                                                              
            stderr_output = e.stderr                                                              
            traceback_str = traceback.format_exc()                                                
            error_info = {                                                          
                'error': error_message,
                'traceback': traceback_str,
                'stdout': stdout_output,
                'stderr': stderr_output,
            }
            break
        
        except Exception as e:                                                                    
            
            failure_msg = f"Local wrapper error before/after remote run: {str(e)}"                
            echo_fail = (
                f"cd {shlex.quote(remote_work_dir)} && "                                          
                f"printf '%s\\n' {shlex.quote(failure_msg)} > failure.txt"                        
            )
            try:
                _ssh_run(remote_login, echo_fail)                                                 
            except Exception:
                pass                                                                              

            if not scheduler_managed:
                task.status = 'failed'                                                            
                task.save()                                                                       

            error_message = f'An error occurred in local wrapper: {str(e)}'                       
            traceback_str = traceback.format_exc()                                                
            error_info = {
                'error': error_message,
                'traceback': traceback_str,
            }
            break
    
    if error_info is None:
        
        echo_success = (
            f"cd {shlex.quote(remote_work_dir)} && "
            f"printf '%s\\n' {shlex.quote('All notebooks executed successfully.')} > success.txt"
        )
        _ssh_run(remote_login, echo_success)

        if not scheduler_managed:
            task.status = 'success'
            task.save()
    
    
    
    try:
        _signal_polymer_worker_progress(download_dir, scheduler_managed, "pull_from_remote_start")
        _pull_remote_to_local(remote_IP, remote_work_dir, abs_download_dir)
        _signal_polymer_worker_progress(download_dir, scheduler_managed, "pull_from_remote_done")
    except Exception as e:
        
        if error_info is None:
            error_info = {
                'error': f'Rsync pull failed: {str(e)}',
                'traceback': traceback.format_exc(),
            }

    if scheduler_managed:
        if error_info is None:
            _write_local_signal_file(download_dir, "success.txt", "All notebooks executed successfully.")
            _write_worker_result_signal(download_dir, status="success", message="Polymer worker finished successfully.")
        else:
            message = json.dumps(error_info, ensure_ascii=False, default=str)
            _write_local_signal_file(download_dir, "failure.txt", message)
            _write_worker_result_signal(download_dir, status="failed", message=message)
