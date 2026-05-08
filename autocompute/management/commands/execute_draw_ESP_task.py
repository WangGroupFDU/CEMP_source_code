


import os                                  
import logging                             
from datetime import datetime              
import importlib
from django.core.management.base import BaseCommand  
from django.conf import settings           
from autocompute.models import ComputeTask 
from autocompute.run_MD_QC_utils import check_and_execute_draw_ESP_task


class Command(BaseCommand):
    help = "执行单个 绘制静电势 任务：check_and_execute_draw_ESP_task + <计算静电势函数>"

    def add_arguments(self, parser):
        parser.add_argument(
            "task_id",
            type=str,
            help="ComputeTask.task_id（加密字符串）",
        )
        parser.add_argument(
            "download_dir",
            type=str,
            help="任务工作目录（Excel 已保存的位置）",
        )
        parser.add_argument(
            "func_path", type=str,
            help=(
                "要执行的函数的完整限定路径，不能使用简写"
                "形如 'autocompute.run_MD_QC_utils.run_Gaussian_single_point_energy_notebook_tasks'"
            ),
        )

    def handle(self, *args, **options):
        task_id = options["task_id"]
        download_dir = options["download_dir"]
        func_path   = options["func_path"]

        
        try:
            task = ComputeTask.objects.get(task_id=task_id)
        except ComputeTask.DoesNotExist:
            self.stderr.write(f"Error: ComputeTask(task_id={task_id}) 不存在。")
            return
        
        
        try:
            module_name, func_name = func_path.rsplit(".", 1) 
            module = importlib.import_module(module_name) 
            task_func = getattr(module, func_name) 
        except (ValueError, ModuleNotFoundError, AttributeError) as exc:
            self.stderr.write(f"无法导入 {func_path}：{exc}")
            return

        
        check_and_execute_draw_ESP_task(
            task_func,  
            download_dir,
            task,
        )