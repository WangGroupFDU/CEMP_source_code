"""科学计算任务公共文件的复制工具。"""

from __future__ import annotations

import shutil
from pathlib import Path

from django.conf import settings


SETTINGS_MODULE_NAME = "cemp_software_settings.py"


def workflow_settings_source_path() -> Path:
    """
    功能目的：定位仓库内唯一的科学软件配置模块。
    输入参数：无。
    返回值：配置模块的绝对路径。
    关键流程：以 Django BASE_DIR 为根目录构造稳定路径。
    可能报错或边界情况：路径不存在时由复制函数给出明确错误。
    """
    return Path(settings.BASE_DIR) / "autocompute" / "static" / SETTINGS_MODULE_NAME


def copy_workflow_settings_module(destination_dir: str) -> Path:
    """
    功能目的：将共享配置模块复制到 notebook 的实际任务目录。
    输入参数：destination_dir 为本地任务目录。
    返回值：复制后的模块路径。
    关键流程：检查源文件、创建目标目录并覆盖旧副本，确保本地和远程任务使用同一版本。
    可能报错或边界情况：共享模块缺失时抛出 FileNotFoundError；目录无写权限时保留系统异常。
    """
    source = workflow_settings_source_path()
    if not source.is_file():
        raise FileNotFoundError(f"Workflow settings module not found: {source}")

    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / SETTINGS_MODULE_NAME
    shutil.copy2(source, target)
    return target
