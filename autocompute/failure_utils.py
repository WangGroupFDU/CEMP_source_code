
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

from autocompute.models import ComputeTask
from autocompute.sqlite_retry import save_task_with_sqlite_retry


logger = logging.getLogger("django")


DEFAULT_FAILURE_CONTENT = "Task failed, but no detailed failure log was captured."


FAILURE_REASON_ALIASES = {
    "expired_cleanup": "Task expired and was cleaned up by the system.",
}


def normalize_failure_message(message: Optional[str]) -> str:

    normalized = (message or "").strip()
    if not normalized:
        return DEFAULT_FAILURE_CONTENT
    return normalized


def merge_failure_messages(existing_message: Optional[str], new_message: Optional[str]) -> str:

    normalized_existing = (existing_message or "").strip()
    normalized_new = normalize_failure_message(new_message)
    if not normalized_existing:
        return normalized_new
    if normalized_new in normalized_existing:
        return normalized_existing
    return f"{normalized_existing}\n{normalized_new}"


def format_status_message_for_query(status_message: Optional[str]) -> str:

    normalized = normalize_failure_message(status_message)
    mapped_lines = []
    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        mapped_lines.append(FAILURE_REASON_ALIASES.get(line, line))
    if not mapped_lines:
        return DEFAULT_FAILURE_CONTENT
    return "\n".join(mapped_lines)


def get_task_failure_file_path(
    task: ComputeTask,
    failure_dir: Optional[Union[str, Path]] = None,
) -> Optional[Path]:

    base_dir = failure_dir if failure_dir is not None else getattr(task, "folder_path", None)
    if not base_dir:
        return None
    return Path(base_dir) / "failure.txt"


def write_task_failure_file(
    task: ComputeTask,
    failure_message: Optional[str],
    *,
    failure_dir: Optional[Union[str, Path]] = None,
    create_parent: bool = False,
    overwrite: bool = False,
) -> Optional[Path]:

    failure_path = get_task_failure_file_path(task, failure_dir=failure_dir)
    if failure_path is None:
        return None

    try:
        if failure_path.exists() and not overwrite:
            return failure_path

        parent_dir = failure_path.parent
        if not parent_dir.exists():
            if not create_parent:
                logger.warning(
                    "任务失败文件父目录不存在且不允许自动创建，跳过写入 failure.txt。task_id=%s, path=%s",
                    getattr(task, "task_id", ""),
                    str(failure_path),
                )
                return None
            parent_dir.mkdir(parents=True, exist_ok=True)

        failure_path.write_text(
            normalize_failure_message(failure_message),
            encoding="utf-8",
        )
        return failure_path
    except Exception:
        logger.exception(
            "写入 failure.txt 失败，task_id=%s, path=%s",
            getattr(task, "task_id", ""),
            str(failure_path),
        )
        return None


def mark_task_failed(
    task: ComputeTask,
    failure_message: Optional[str],
    *,
    write_failure_file: bool = False,
    failure_dir: Optional[Union[str, Path]] = None,
    create_failure_dir: bool = False,
    overwrite_failure_file: bool = False,
) -> str:

    merged_message = merge_failure_messages(getattr(task, "status_message", ""), failure_message)

    try:
        task.status = "failed"
        task.status_message = merged_message
        save_task_with_sqlite_retry(
            task,
            update_fields=["status", "status_message"],
            operation_name="mark_task_failed",
        )
    except Exception:
        logger.exception("写入任务失败状态时出现异常，task_id=%s", getattr(task, "task_id", ""))

    if write_failure_file:
        write_task_failure_file(
            task,
            merged_message,
            failure_dir=failure_dir,
            create_parent=create_failure_dir,
            overwrite=overwrite_failure_file,
        )

    return merged_message
