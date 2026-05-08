from django.db import models
from django.contrib.auth.models import User




class ComputationTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    upload_file_path = models.CharField(max_length=255)
    download_file_path = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    progress = models.FloatField(default=0)

    def __str__(self):
        return f"Task {self.id} for {self.user.username}"
    


class ComputeTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    task_type = models.CharField(max_length=255, default='default_type', null=True, blank=True)  
    task_id = models.CharField(max_length=255)  
    folder_path = models.CharField(max_length=255)  
    created_at = models.DateTimeField(auto_now_add=True)  
    status = models.CharField(max_length=50, default='pending')  
    pid = models.IntegerField(null=True, blank=True)  
    statusemail = models.BooleanField(null=True, blank=True, default=False)  
    priority = models.PositiveSmallIntegerField(null=False, blank=False, default=3)  
    
    scope_name = models.CharField(
        max_length=200,     
        null=True,          
        blank=True,         
        help_text="任务所属 cgroup.scope 名称（如 CEMPjobs.slice）"
    )
    
    core_hours = models.FloatField(
        null=True,          
        blank=True,         
        help_text="任务消耗的总核心小时数（CPU hours）"
    )
    remote_type = models.CharField(max_length=255, null=True, blank=True)  
    server_name = models.CharField(max_length=255, null=True, blank=True)  
    status_message = models.TextField(
        null=True,
        blank=True,
        help_text="补充记录任务状态变化原因，例如超期清理、人工终止等。",
    )
    last_heartbeat_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="远程任务最近一次确认仍在推进的时间戳，用于识别假活跃 pending。",
    )

    def __str__(self):
        return f"Task {self.task_id} for {self.user.username}"
    


class RunningTask(ComputeTask):
    class Meta:
        proxy = True
        verbose_name = "Running Task"
        verbose_name_plural = "Running Tasks"


class QueuedTask(ComputeTask):
    class Meta:
        proxy = True
        verbose_name = "Queued Task"
        verbose_name_plural = "Queued Tasks"

class CompletedTask(ComputeTask):
    class Meta:
        proxy = True
        verbose_name = "Completed Task"
        verbose_name_plural = "Completed Tasks"

class TaskMonitor(ComputeTask):
    class Meta:
        proxy = True                     
        verbose_name = "Task Monitor"     
        verbose_name_plural = "Task Monitor"  
