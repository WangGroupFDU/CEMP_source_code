from autocompute.models import ComputeTask
from django.core.management.base import BaseCommand

def update_empty_task_type():
    tasks_to_update = ComputeTask.objects.filter(task_type__isnull=True)  
    tasks_to_update.update(task_type='default_type')  

class Command(BaseCommand):
    help = 'Update tasks with empty task_type to default_type'

    def handle(self, *args, **kwargs):
        update_empty_task_type()
        self.stdout.write(self.style.SUCCESS('Successfully updated tasks with empty task_type to default_type'))