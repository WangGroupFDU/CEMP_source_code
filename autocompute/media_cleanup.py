
from __future__ import annotations

import os
import posixpath
import re
import shlex
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from django.conf import settings
from django.utils import timezone

from autocompute.models import ComputationTask, ComputeTask
from autocompute.remote_utils import _build_ssh_command, _load_remote_server_pool



TASK_FOLDER_PATTERN = re.compile(r"^(?P<timestamp>\d{8}_\d{6})_.+$")


ACTIVE_COMPUTE_TASK_STATUSES = {"pending", "queuing"}
ACTIVE_COMPUTATION_TASK_STATUSES = {"PENDING", "RUNNING"}


EXPIRED_CLEANUP_REASON = "expired_cleanup"


@dataclass(frozen=True)
class CleanupRootSpec:

    relative_path: str
    mirror_remote: bool

    @property
    def absolute_path(self) -> Path:

        return Path(settings.MEDIA_ROOT) / self.relative_path


@dataclass(frozen=True)
class CleanupCandidate:

    root_spec: CleanupRootSpec
    folder_name: str
    local_path: Path
    created_at: datetime
    age_days: int


def get_cleanup_root_specs() -> List[CleanupRootSpec]:

    return [
        CleanupRootSpec("AutoCompute/QcCompute/Downloads", True),
        CleanupRootSpec("AutoCompute/QcCompute/Uploads", False),
        CleanupRootSpec("AutoCompute/MDCompute/Downloads", True),
        CleanupRootSpec("AutoCompute/MDCompute/Uploads", False),
        CleanupRootSpec("ionic_liquid/ILpredict_XGBoost/Downloads", False),
        CleanupRootSpec("ionic_liquid/ILpredict_XGBoost/Uploads", False),
        CleanupRootSpec("Polymer/GeneratePolymer", True),
        CleanupRootSpec("Polymer/polymer_predict/Downloads", False),
        CleanupRootSpec("Polymer/polymer_predict/Uploads", False),
        CleanupRootSpec("Polymer/visualization_polymer_structure", False),
    ]


def parse_task_folder_timestamp(folder_name: str) -> Optional[datetime]:

    match = TASK_FOLDER_PATTERN.match(folder_name)
    if not match:
        return None

    try:
        naive_dt = datetime.strptime(match.group("timestamp"), "%Y%m%d_%H%M%S")
    except ValueError:
        return None

    return timezone.make_aware(naive_dt, timezone.get_current_timezone())


def build_expired_candidates(
    days: int = 60,
    root_filters: Optional[Sequence[str]] = None,
    now: Optional[datetime] = None,
) -> List[CleanupCandidate]:

    if now is None:
        now = timezone.localtime(timezone.now())

    allowed_filters = set(root_filters or [])
    candidates: List[CleanupCandidate] = []

    for root_spec in get_cleanup_root_specs():
        if allowed_filters and root_spec.relative_path not in allowed_filters:
            continue

        root_path = root_spec.absolute_path
        if not root_path.exists():
            continue

        try:
            with os.scandir(root_path) as entries:
                for entry in entries:
                    if not entry.is_dir(follow_symlinks=False):
                        continue

                    created_at = parse_task_folder_timestamp(entry.name)
                    if created_at is None:
                        continue

                    age_days = int((now - created_at).total_seconds() // 86400)
                    if age_days < days:
                        continue

                    candidates.append(
                        CleanupCandidate(
                            root_spec=root_spec,
                            folder_name=entry.name,
                            local_path=Path(entry.path),
                            created_at=created_at,
                            age_days=age_days,
                        )
                    )
        except FileNotFoundError:
            continue

    candidates.sort(key=lambda item: (item.created_at, item.root_spec.relative_path, item.folder_name))
    return candidates


def _basename_from_any_path(path_value: Optional[str]) -> Optional[str]:

    if not path_value:
        return None

    normalized = str(path_value).rstrip("/\\")
    if not normalized:
        return None

    path_obj = Path(normalized)
    name = path_obj.name
    if not name:
        return None

    
    if "." in name and path_obj.parent.name:
        return path_obj.parent.name

    return name


def build_task_folder_indexes() -> Tuple[Dict[str, List[ComputeTask]], Dict[str, List[ComputationTask]]]:

    compute_index: Dict[str, List[ComputeTask]] = {}
    computation_index: Dict[str, List[ComputationTask]] = {}

    for task in ComputeTask.objects.all().iterator():
        folder_name = _basename_from_any_path(task.folder_path)
        if folder_name:
            compute_index.setdefault(folder_name, []).append(task)

    for task in ComputationTask.objects.all().iterator():
        seen_folder_names = set()
        for raw_path in (task.upload_file_path, task.download_file_path):
            folder_name = _basename_from_any_path(raw_path)
            if folder_name:
                seen_folder_names.add(folder_name)
        for folder_name in seen_folder_names:
            computation_index.setdefault(folder_name, []).append(task)

    return compute_index, computation_index


def _pid_exists(pid: int) -> bool:

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def terminate_local_process(pid: Optional[int], wait_seconds: float = 3.0) -> Dict[str, object]:

    if not pid:
        return {"status": "no_pid", "success": True, "error": ""}

    if not _pid_exists(pid):
        return {"status": "not_found", "success": True, "error": ""}

    try:
        try:
            process_group_id = os.getpgid(pid)
        except ProcessLookupError:
            return {"status": "not_found", "success": True, "error": ""}

        try:
            os.killpg(process_group_id, signal.SIGTERM)
        except ProcessLookupError:
            return {"status": "not_found", "success": True, "error": ""}

        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            if not _pid_exists(pid):
                return {"status": "terminated", "success": True, "error": ""}
            time.sleep(0.2)

        if _pid_exists(pid):
            try:
                os.killpg(process_group_id, signal.SIGKILL)
            except ProcessLookupError:
                return {"status": "not_found", "success": True, "error": ""}

            time.sleep(0.2)

        if _pid_exists(pid):
            return {
                "status": "kill_failed",
                "success": False,
                "error": f"PID {pid} 发送 TERM/KILL 后仍存活。",
            }

        return {"status": "killed", "success": True, "error": ""}

    except Exception as exc:  
        return {"status": "error", "success": False, "error": str(exc)}


def _run_remote_bash(
    remote_login: str,
    command: str,
    timeout: int = 60,
) -> subprocess.CompletedProcess:

    ssh_cmd = _build_ssh_command(
        remote_login,
        batch_mode=True,
        allocate_tty=False,
    )
    return subprocess.run(
        ssh_cmd + ["bash", "-lc", command],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def terminate_remote_processes(remote_login: str, remote_dir: str) -> Dict[str, object]:

    quoted_remote_dir = shlex.quote(remote_dir)
    command = f"""
target={quoted_remote_dir}
if [ ! -d "$target" ]; then
  echo "__CEMP_DIR_MISSING__"
  exit 0
fi
pids="$(pgrep -f -- "$target" || true)"
if [ -z "$pids" ]; then
  echo "__CEMP_NO_PROCESS__"
  exit 0
fi
kill -TERM $pids || true
sleep 2
pids="$(pgrep -f -- "$target" || true)"
if [ -n "$pids" ]; then
  kill -KILL $pids || true
fi
echo "__CEMP_REMOTE_KILL_DONE__"
"""

    try:
        completed = _run_remote_bash(remote_login, command)
    except subprocess.CalledProcessError as exc:
        return {
            "status": "error",
            "success": False,
            "error": str(exc),
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
    except Exception as exc:  
        return {
            "status": "error",
            "success": False,
            "error": str(exc),
            "stdout": "",
            "stderr": "",
        }

    stdout_text = completed.stdout or ""
    if "__CEMP_DIR_MISSING__" in stdout_text:
        status = "missing"
    elif "__CEMP_NO_PROCESS__" in stdout_text:
        status = "no_process"
    else:
        status = "terminated"

    return {
        "status": status,
        "success": True,
        "error": "",
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def delete_remote_directory(remote_login: str, remote_dir: str) -> Dict[str, object]:

    quoted_remote_dir = shlex.quote(remote_dir)
    command = f"""
target={quoted_remote_dir}
if [ ! -e "$target" ]; then
  echo "__CEMP_DIR_MISSING__"
  exit 0
fi
rm -rf -- "$target"
echo "__CEMP_REMOTE_DELETE_DONE__"
"""

    try:
        completed = _run_remote_bash(remote_login, command)
    except subprocess.CalledProcessError as exc:
        return {
            "status": "error",
            "success": False,
            "error": str(exc),
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }
    except Exception as exc:  
        return {
            "status": "error",
            "success": False,
            "error": str(exc),
            "stdout": "",
            "stderr": "",
        }

    stdout_text = completed.stdout or ""
    if "__CEMP_DIR_MISSING__" in stdout_text:
        status = "missing"
    else:
        status = "deleted"

    return {
        "status": status,
        "success": True,
        "error": "",
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def delete_local_directory(local_path: Path) -> Dict[str, object]:

    if not local_path.exists():
        return {"status": "missing", "success": True, "error": ""}

    try:
        shutil.rmtree(local_path)
        return {"status": "deleted", "success": True, "error": ""}
    except Exception as exc:
        return {"status": "error", "success": False, "error": str(exc)}


def _append_reason(existing_value: Optional[str], reason: str) -> str:

    normalized_existing = (existing_value or "").strip()
    if not normalized_existing:
        return reason
    if reason in normalized_existing:
        return normalized_existing
    return f"{normalized_existing}\n{reason}"


def update_task_records_for_expired_cleanup(
    compute_tasks: Sequence[ComputeTask],
    computation_tasks: Sequence[ComputationTask],
) -> Dict[str, object]:

    updated_compute_count = 0
    updated_computation_count = 0

    try:
        for task in compute_tasks:
            if task.status not in ACTIVE_COMPUTE_TASK_STATUSES:
                continue
            task.status = "failed"
            task.pid = None
            task.status_message = _append_reason(task.status_message, EXPIRED_CLEANUP_REASON)
            task.save(update_fields=["status", "pid", "status_message"])
            updated_compute_count += 1

        for task in computation_tasks:
            if task.status not in ACTIVE_COMPUTATION_TASK_STATUSES:
                continue
            task.status = "FAILED"
            task.error_message = _append_reason(task.error_message, EXPIRED_CLEANUP_REASON)
            task.save(update_fields=["status", "error_message", "updated_at"])
            updated_computation_count += 1

        return {
            "status": "updated",
            "success": True,
            "updated_compute_count": updated_compute_count,
            "updated_computation_count": updated_computation_count,
            "error": "",
        }
    except Exception as exc:  
        return {
            "status": "error",
            "success": False,
            "updated_compute_count": updated_compute_count,
            "updated_computation_count": updated_computation_count,
            "error": str(exc),
        }


def _build_remote_directory_candidates(
    candidate: CleanupCandidate,
    server_pool: Sequence[Dict[str, object]],
) -> List[Tuple[str, str, int, str]]:

    if not candidate.root_spec.mirror_remote:
        return []

    remote_candidates: List[Tuple[str, str, int, str]] = []
    for server in server_pool:
        remote_login = str(server.get("remote_login") or server["IP"]).rstrip(":")
        ssh_port = int(server.get("ssh_port", 22))
        remote_dir = posixpath.join(
            str(server["remote_target_dir"]).rstrip("/"),
            candidate.root_spec.relative_path.replace("\\", "/"),
            candidate.folder_name,
        )
        remote_candidates.append((str(server["server_name"]), remote_login, ssh_port, remote_dir))

    return remote_candidates


def cleanup_expired_task_directories(
    days: int = 60,
    dry_run: bool = False,
    limit: Optional[int] = None,
    root_filters: Optional[Sequence[str]] = None,
    now: Optional[datetime] = None,
) -> List[Dict[str, object]]:

    compute_index, computation_index = build_task_folder_indexes()
    server_pool = _load_remote_server_pool()
    candidates = build_expired_candidates(days=days, root_filters=root_filters, now=now)
    if limit is not None:
        candidates = candidates[:limit]

    results: List[Dict[str, object]] = []

    for candidate in candidates:
        matched_compute_tasks = compute_index.get(candidate.folder_name, [])
        matched_computation_tasks = computation_index.get(candidate.folder_name, [])

        active_compute_tasks = [
            task for task in matched_compute_tasks if task.status in ACTIVE_COMPUTE_TASK_STATUSES
        ]
        active_computation_tasks = [
            task for task in matched_computation_tasks if task.status in ACTIVE_COMPUTATION_TASK_STATUSES
        ]
        is_active_task = bool(active_compute_tasks or active_computation_tasks)

        matched_task_ids = [
            f"compute:{task.task_id}" for task in matched_compute_tasks
        ] + [
            f"computation:{task.id}" for task in matched_computation_tasks
        ]

        record: Dict[str, object] = {
            "root": candidate.root_spec.relative_path,
            "folder_name": candidate.folder_name,
            "local_path": str(candidate.local_path),
            "age_days": candidate.age_days,
            "created_at": candidate.created_at.isoformat(),
            "is_active_task": is_active_task,
            "matched_task_id": matched_task_ids[0] if matched_task_ids else "",
            "matched_task_ids": matched_task_ids,
            "task_status_before": {
                "compute": [task.status for task in matched_compute_tasks],
                "computation": [task.status for task in matched_computation_tasks],
            },
            "dry_run": dry_run,
            "kill_local_status": [],
            "kill_remote_status": [],
            "db_update_status": "skipped",
            "remote_delete_status": [],
            "local_delete_status": "skipped",
            "error": "",
        }

        remote_targets = _build_remote_directory_candidates(candidate, server_pool)

        if dry_run:
            record["remote_targets"] = [
                {"server_name": server_name, "remote_login": remote_login, "remote_dir": remote_dir}
                for server_name, remote_login, _ssh_port, remote_dir in remote_targets
            ]
            results.append(record)
            continue

        if candidate.root_spec.mirror_remote and not remote_targets:
            record["error"] = "需要同步清理远端目录，但当前远程服务器池为空。"
            results.append(record)
            continue

        fatal_error = False

        if is_active_task:
            for task in active_compute_tasks:
                kill_result = terminate_local_process(task.pid)
                record["kill_local_status"].append(
                    {
                        "task_id": task.task_id,
                        "pid": task.pid,
                        "status": kill_result["status"],
                        "error": kill_result["error"],
                    }
                )
                if not kill_result["success"]:
                    fatal_error = True

            if candidate.root_spec.mirror_remote:
                for server_name, remote_login, _ssh_port, remote_dir in remote_targets:
                    kill_result = terminate_remote_processes(remote_login, remote_dir)
                    record["kill_remote_status"].append(
                        {
                            "server_name": server_name,
                            "remote_login": remote_login,
                            "remote_dir": remote_dir,
                            "status": kill_result["status"],
                            "error": kill_result["error"],
                        }
                    )
                    if not kill_result["success"]:
                        fatal_error = True

            if fatal_error:
                record["error"] = "活跃任务终止阶段出现错误，本轮不执行数据库回写与目录删除。"
                results.append(record)
                continue

            db_update_result = update_task_records_for_expired_cleanup(
                active_compute_tasks,
                active_computation_tasks,
            )
            record["db_update_status"] = db_update_result
            if not db_update_result["success"]:
                record["error"] = "数据库状态回写失败，本轮不执行目录删除。"
                results.append(record)
                continue

        if candidate.root_spec.mirror_remote:
            remote_delete_failed = False
            for server_name, remote_login, _ssh_port, remote_dir in remote_targets:
                delete_result = delete_remote_directory(remote_login, remote_dir)
                record["remote_delete_status"].append(
                    {
                        "server_name": server_name,
                        "remote_login": remote_login,
                        "remote_dir": remote_dir,
                        "status": delete_result["status"],
                        "error": delete_result["error"],
                    }
                )
                if not delete_result["success"]:
                    remote_delete_failed = True

            if remote_delete_failed:
                record["error"] = "远端目录删除失败，本地目录本轮不删除。"
                results.append(record)
                continue

        local_delete_result = delete_local_directory(candidate.local_path)
        record["local_delete_status"] = local_delete_result
        if not local_delete_result["success"]:
            record["error"] = "本地目录删除失败。"

        results.append(record)

    return results
