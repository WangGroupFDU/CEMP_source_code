


import os                                  
import logging                             
from datetime import datetime              
import importlib
from django.core.management.base import BaseCommand  
from django.conf import settings           
from autocompute.models import ComputeTask 
from autocompute.run_MD_QC_utils import run_task_immediately


class Command(BaseCommand):
    help = "执行单个 ORCA-MD 任务：run_task_immediately + <任意计算函数>"

    def add_arguments(self, parser):
        parser.add_argument(
            "task_id",
            type=str,
            help="ComputeTask.task_id（加密字符串）",
        )
        parser.add_argument(
            "source_dir",
            type=str,
            help="程序源代码所在目录",
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
        source_dir = options["source_dir"]
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

        
        run_task_immediately(
            task_func,  
            source_dir,
            download_dir,
            task,
        )