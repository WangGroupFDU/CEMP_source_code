


from django.core.management.base import BaseCommand  
from autocompute.models import ComputeTask 
from autocompute.remote_utils import persist_remote_dispatch_request


class Command(BaseCommand):
    help = "兼容旧入口：只登记远程任务，由 run_remote_queue_scheduler 单实例调度执行。"

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
        parser.add_argument(
            "remote_target", type=str,
            help=(
                "计算节点的工作路径"
                "形如 '/path/to/example/AutoCompute/QcCompute/Downloads'"
            ),
        )

    def handle(self, *args, **options):
        task_id = options["task_id"]
        source_dir = options["source_dir"]
        download_dir = options["download_dir"]
        func_path   = options["func_path"]
        remote_target = options["remote_target"]

        
        try:
            task = ComputeTask.objects.get(task_id=task_id)
        except ComputeTask.DoesNotExist:
            self.stderr.write(f"Error: ComputeTask(task_id={task_id}) 不存在。")
            return
        
        
        task.remote_type = "remote"
        task.status = "queuing"
        task.server_name = None
        task.pid = None
        task.save(update_fields=["remote_type", "status", "server_name", "pid"])
        persist_remote_dispatch_request(
            task=task,
            source_dir=source_dir,
            download_dir=download_dir,
            func_path=func_path,
            remote_target_subpath=remote_target,
        )
        self.stdout.write(f"Remote task {task.id} queued for single scheduler.")
