from django.shortcuts import render
from autocompute.failure_utils import mark_task_failed
from autocompute.models import ComputeTask
from django.core.management.base import BaseCommand


QUEUING_BULK_FAIL_MESSAGE = 'Queued task without a PID was manually marked as failed by maintenance command.'


def update_queuing_tasks_to_failed():
    
    tasks_to_update = ComputeTask.objects.filter(pid__isnull=True, status='queuing')

    
    for task in tasks_to_update:
        mark_task_failed(
            task,
            QUEUING_BULK_FAIL_MESSAGE,
            write_failure_file=True,
            create_failure_dir=False,
            overwrite_failure_file=False,
        )
    
class Command(BaseCommand):
    help = 'Update queuing tasks with pid=None to failed'

    def handle(self, *args, **kwargs):
        update_queuing_tasks_to_failed()
        self.stdout.write(self.style.SUCCESS('Successfully updated queuing tasks to failed'))

