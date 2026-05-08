


from django_cron import CronJobBase, Schedule
from autocompute.models import ComputeTask 
from datetime import timedelta, datetime
from django.utils import timezone
from cryptography.fernet import Fernet  
from django.conf import settings 
import psutil  
import json
import os
from django.db.models import Q 
from django.core.mail import send_mail
import time
import shutil
import sys

from autocompute.failure_utils import mark_task_failed




cipher_suite = Fernet(settings.FERNET_SECRET_KEY)


UNEXPECTED_INTERRUPTION_MESSAGE = 'The program was unexpectedly interrupted. Please try again.'


PENDING_TIMEOUT_MESSAGE = 'Pending task exceeded timeout limit.'


def decrypt_download_url_list(encrypted_id):
    try:
        
        decrypted = cipher_suite.decrypt(encrypted_id.encode('utf-8'))

        
        download_url_list = json.loads(decrypted.decode('utf-8'))

        return download_url_list
    except Exception as e:
        
        print(f"解密失败: {str(e)}")
        return None


class TaskStatusChecker(CronJobBase):
    
    RUN_EVERY_MINS = 1  

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'autocompute.TaskStatusChecker'  

    def do(self):
        
        tasks = ComputeTask.objects.filter(Q(status='pending') | Q(status='queuing'))

        
        now = timezone.now()

        for task in tasks:
            pid = task.pid

            
            if pid is None:
                continue
            
            try:
                
                process = psutil.Process(pid)
                
                
                if process.create_time() > task.created_at.timestamp(): 
                    
                    continue
                
            except psutil.NoSuchProcess:
                
                pass

            
            if psutil.pid_exists(pid):
                
                continue

            
            task_id = task.task_id
            download_url_list = decrypt_download_url_list(task_id)
            task_directory = download_url_list[0]

            
            success_file = os.path.join(task_directory, 'success.txt')
            failure_file = os.path.join(task_directory, 'failure.txt')

            if os.path.exists(success_file):
                
                task.status = 'success'
                task.save(update_fields=['status'])
            elif os.path.exists(failure_file):
                
                task.status = 'failed'
                task.save(update_fields=['status'])
            else:
                
                mark_task_failed(
                    task,
                    UNEXPECTED_INTERRUPTION_MESSAGE,
                    write_failure_file=True,
                    failure_dir=task_directory,
                    create_failure_dir=True,
                    overwrite_failure_file=False,
                )


class CheckPendingTasks(CronJobBase):
    RUN_EVERY_MINS = 1  

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    
    
    code = 'autocompute.CheckPendingTasks'  

    def do(self):
        
        now = timezone.now()
        timeout_threshold = now - timedelta(hours=300)

        
        tasks = ComputeTask.objects.filter(status='pending')

        for task in tasks:
            
            if now - task.created_at >= timedelta(hours=300):
                
                mark_task_failed(
                    task,
                    PENDING_TIMEOUT_MESSAGE,
                    write_failure_file=True,
                    create_failure_dir=False,
                    overwrite_failure_file=False,
                )


class TaskStatusEmailCronJob(CronJobBase):
    
    RUN_EVERY_MINS = 1

    
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    
    
    code = 'autocompute.task_status_email_cron'

    def do(self):
        
        current_time = timezone.now()

        
        tasks = ComputeTask.objects.filter(status__in=['success', 'failed'], statusemail=False)

        
        for task in tasks:
            user = task.user  
            created_time = task.created_at.strftime('%Y-%m-%d %H:%M:%S')  
            task_type = task.task_type  
            task_status = task.status.capitalize()  

            
            subject = f'Task Completion Notice - CEMP Platform'
            
            
            message = f"""
            Hello {user.username},

            We are pleased to inform you that the task you submitted on {created_time} as part of the CEMP (Clean Energy Material Project) platform has been completed. 

            Task Details:
            - Task Type: {task_type}
            - Submission Time: {created_time}
            - Completion Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
            - Task Status: {task_status}

            Please note that the data will be stored for 30 days only. We encourage you to log in to the CEMP platform (https://example.com) and manage your task as soon as possible.
            
            !!!!!!Note!!!!!!: When using this functionality in scientific publications, please cite the following references:
            [1] Wang, J.; Ju, J.; Wang, Y. CEMP: a platform unifying high-throughput online calculation, databases and predictive models for clean energy materials. arXiv preprint arXiv:2507.04423, 2025.
            
            Best regards,
            The CEMP Team
            """

            try:
                
                send_mail(
                    subject,  
                    message,  
                    'user@example.com',  
                    [user.email],  
                    fail_silently=False,
                )
                
                task.statusemail = True
                task.save()

            except Exception as e:
                
                print(f"Failed to send email to {user.email}: {str(e)}")


class DeleteOldFolders(CronJobBase):
    RUN_EVERY_MINS = 1 

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'autocompute.DeleteOldFolders'  

    def do(self):
        
        now = time.time()
        
        threshold = now - 30 * 24 * 60 * 60

        
        directories = [
            os.path.join(settings.MEDIA_ROOT, 'AutoCompute/MDCompute/Downloads'),
            os.path.join(settings.MEDIA_ROOT, 'AutoCompute/MDCompute/Uploads'),
            os.path.join(settings.MEDIA_ROOT, 'AutoCompute/QcCompute/Downloads'),
            os.path.join(settings.MEDIA_ROOT, 'AutoCompute/QcCompute/Uploads'),
            os.path.join(settings.MEDIA_ROOT, 'AutoCompute/Crystal/prediction'),
            os.path.join(settings.MEDIA_ROOT, 'AutoCompute/Crystal/visualization_crystal_structure'),
            os.path.join(settings.MEDIA_ROOT, 'ionic_liquid/ILpredict_XGBoost/Downloads'),
            os.path.join(settings.MEDIA_ROOT, 'ionic_liquid/ILpredict_XGBoost/Uploads'),
            os.path.join(settings.MEDIA_ROOT, 'Polymer/GeneratePolymer'),
            os.path.join(settings.MEDIA_ROOT, 'Polymer/visualization_polymer_structure'),
        ]

        
        for dir_path in directories:
            
            if os.path.exists(dir_path):
                
                for folder in os.listdir(dir_path):
                    folder_path = os.path.join(dir_path, folder)
                    
                    if os.path.isdir(folder_path) and os.path.getctime(folder_path) < threshold:
                        
                        shutil.rmtree(folder_path)
                        print(f"Deleted folder: {folder_path}")
            else:
                print(f"Directory does not exist: {dir_path}")
