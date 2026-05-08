

from django.core.management.base import BaseCommand
from django.db.models import Count
from autocompute.models import ComputeTask

class Command(BaseCommand):
    help = '统计每个用户的任务提交数量'

    def handle(self, *args, **options):
        
        task_stats = ComputeTask.objects.values('user__username').annotate(task_count=Count('id')).order_by('user__username')
        
        
        for entry in task_stats:
            username = entry.get('user__username', '未知用户')
            task_count = entry.get('task_count', 0)
            self.stdout.write(f"用户: {username}，任务数量: {task_count}")