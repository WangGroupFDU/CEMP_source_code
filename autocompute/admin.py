from django.contrib import admin


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import redirect
from autocompute.models import ComputeTask
from autocompute.models import RunningTask, QueuedTask, CompletedTask, TaskMonitor

class CustomUserAdmin(BaseUserAdmin):
    
    list_display = BaseUserAdmin.list_display + ('date_joined', 'task_count',)

    def get_queryset(self, request):
        
        qs = super().get_queryset(request)
        
        qs = qs.annotate(task_count=Count('computetask'))
        return qs

    def task_count(self, obj):
        
        return obj.task_count
    task_count.short_description = 'Total Processed Task Number'  


@admin.register(RunningTask)
class RunningTaskAdmin(admin.ModelAdmin):
    list_display  = ('user', 'task_type', 'created_at', 'status')
    list_filter   = ('task_type',)
    ordering      = ('-created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status='pending')


@admin.register(QueuedTask)
class QueuedTaskAdmin(admin.ModelAdmin):
    list_display  = ('user', 'task_type', 'created_at', 'status')
    list_filter   = ('task_type',)
    ordering      = ('-created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status='queuing')


@admin.register(CompletedTask)
class CompletedTaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'task_type', 'created_at', 'status')
    ordering     = ('-created_at',)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        return qs.filter(status__in=['failed', 'success'])


@admin.register(TaskMonitor)
class TaskMonitorAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        
        return redirect('home:admin_query')


admin.site.unregister(User)

admin.site.register(User, CustomUserAdmin)