
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from autocompute.failure_utils import mark_task_failed
from autocompute.models import ComputeTask  


OLD_QUEUING_FAIL_MESSAGE = 'Queued task exceeded the allowed waiting time and was marked as failed.'


class Command(BaseCommand):
    help = '将指定时间之前创建且状态为 queuing 的任务更新为 failed'

    def add_arguments(self, parser):
        
        parser.add_argument('cutoff', type=str, help='截止时间，格式为 "YYYY-MM-DD HH:MM:SS"')

    def handle(self, *args, **kwargs):
        cutoff_str = kwargs['cutoff']
        try:
            
            cutoff_datetime = datetime.strptime(cutoff_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            self.stdout.write(self.style.ERROR('截止时间格式错误，请使用 "YYYY-MM-DD HH:MM:SS" 格式'))
            return
        
        
        if timezone.is_naive(cutoff_datetime):
            cutoff_datetime = timezone.make_aware(cutoff_datetime, timezone.get_current_timezone())

        
        tasks_to_fail = ComputeTask.objects.filter(
            created_at__lt=cutoff_datetime,
            status='queuing'
        )
        updated_count = 0
        for task in tasks_to_fail:
            mark_task_failed(
                task,
                OLD_QUEUING_FAIL_MESSAGE,
                write_failure_file=True,
                create_failure_dir=False,
                overwrite_failure_file=False,
            )
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'成功更新了 {updated_count} 个任务状态为 failed'))
