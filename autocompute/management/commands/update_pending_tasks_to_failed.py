import os
from django.core.management.base import BaseCommand
from autocompute.failure_utils import mark_task_failed
from autocompute.models import ComputeTask


PENDING_BULK_FAIL_MESSAGE = 'Pending task was manually marked as failed by maintenance command.'


class Command(BaseCommand):
    help = 'Update all pending ComputeTask statuses to failed'

    def handle(self, *args, **kwargs):
        
        updated_count = 0
        for task in ComputeTask.objects.filter(status='pending'):
            mark_task_failed(
                task,
                PENDING_BULK_FAIL_MESSAGE,
                write_failure_file=True,
                create_failure_dir=False,
                overwrite_failure_file=False,
            )
            updated_count += 1
        
        
        self.stdout.write(self.style.SUCCESS(f'{updated_count} tasks updated from "pending" to "failed".'))
