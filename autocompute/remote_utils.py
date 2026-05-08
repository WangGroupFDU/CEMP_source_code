import json
import logging
import os
import posixpath
import shlex
import shutil
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from datetime import timedelta
import fcntl
import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import psutil
from django.conf import settings
from django.db import OperationalError, transaction
from django.db.models import Count, Max
from django.http import JsonResponse
from django.utils import timezone

from autocompute.capability_registry import (
    MARKOV_ANALYSIS,
    get_required_capability,
    get_required_settings_keys_for_task,
    is_deprecated_remote_task_type,
)
from autocompute.failure_utils import mark_task_failed
from autocompute.models import ComputeTask
from autocompute.sqlite_retry import (
    save_task_with_sqlite_retry,
    touch_task_heartbeat,
)
from home.md_previews import build_md_preview_manifest


remote_IP = "user@<PRIVATE_HOST>:"

MAX_RUNNING_LENGTH=3 

REMOTE_MAX_RUNNING_LENGTH=18 

logger = logging.getLogger('django')  

REMOTE_TASK_POLL_INTERVAL = 1
REMOTE_HEALTH_CACHE_TTL_SECONDS = 60
CLAIM_REMOTE_SLOT_RETRY_DELAYS_SECONDS = (1, 2, 3)
SQLITE_LOCK_ERROR_MARKER = "database is locked"
QUEUED_DISPATCHER_DISAPPEARED_MESSAGE = (
    "Queued dispatcher process disappeared before slot claim."
)
PENDING_REMOTE_PROCESS_DISAPPEARED_MESSAGE = (
    "Remote task process disappeared unexpectedly before completion."
)
PENDING_REMOTE_HEARTBEAT_TIMEOUT_MESSAGE = (
    "Remote task stopped making progress and exceeded the heartbeat timeout."
)
REMOTE_RECONCILE_SCAN_LIMIT_PER_LOOP = 10
REMOTE_QUEUE_SCHEDULER_LOCK_FILENAME = "remote_queue_scheduler.lock"
REMOTE_DISPATCH_REQUEST_FILENAME = "remote_dispatch_request.json"
REMOTE_WORKER_STARTED_FILENAME = "worker_started.json"
REMOTE_WORKER_HEARTBEAT_FILENAME = "worker_heartbeat.json"
REMOTE_WORKER_RESULT_FILENAME = "worker_result.json"


REMOTE_TASK_HEARTBEAT_TIMEOUTS = {
    "MDCoumpute": timedelta(hours=48),
    "Markov_GDyNet_analysis": timedelta(hours=24),
    "Manual_Mode_QCcompute": timedelta(hours=48),
    "Manual_Mode_QCcompute_energy": timedelta(hours=48),
    "DrawESP": timedelta(hours=2),
    "DrawESP_remote": timedelta(hours=2),
    "Draw_HOMO_LUMO_orb": timedelta(hours=2),
    "NCI_analysis": timedelta(hours=2),
    "NCI_promolecular_analysis": timedelta(hours=2),
}
REMOTE_TASK_TYPE_HEARTBEAT_PREFIX_TIMEOUTS = {
    "HTQC_": timedelta(hours=48),
}



_REMOTE_HEALTH_CACHE: Dict[Tuple[str, str], Dict[str, Any]] = {}


def _task_folder_path(task: ComputeTask) -> str:

    raw_path = str(getattr(task, "folder_path", "") or "").strip()
    if not raw_path:
        return ""
    return os.path.abspath(raw_path)


def _worker_signal_path(task_or_dir: Union[ComputeTask, str], filename: str) -> str:

    if isinstance(task_or_dir, ComputeTask):
        base_dir = _task_folder_path(task_or_dir)
    else:
        base_dir = os.path.abspath(str(task_or_dir or "").strip())
    if not base_dir:
        raise ValueError("Task folder path is empty; cannot build worker signal path.")
    return os.path.join(base_dir, filename)


def _write_json_file(path: str, payload: Dict[str, Any]) -> None:

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _read_json_file(path: str) -> Optional[Dict[str, Any]]:

    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON payload at {path} must be an object.")
    return payload


def _normalise_remote_target_subpath(remote_target: str) -> str:

    raw_target = str(remote_target or "").replace("\\", "/").strip()
    if not raw_target:
        return ""
    try:
        for server in _load_remote_server_pool():
            base_dir = str(server.get("remote_target_dir") or "").replace("\\", "/").rstrip("/")
            if base_dir and (raw_target == base_dir or raw_target.startswith(base_dir + "/")):
                return raw_target[len(base_dir):].strip("/")
    except Exception:
        pass
    return raw_target.strip("/")


def persist_remote_dispatch_request(
    task: ComputeTask,
    *,
    source_dir: str,
    download_dir: str,
    func_path: str,
    remote_target_subpath: str,
) -> str:

    request_path = _worker_signal_path(task, REMOTE_DISPATCH_REQUEST_FILENAME)
    payload = {
        "version": 1,
        "task_id": task.task_id,
        "task_type": task.task_type,
        "source_dir": os.path.abspath(str(source_dir)),
        "download_dir": os.path.abspath(str(download_dir)),
        "func_path": str(func_path),
        "remote_target_subpath": _normalise_remote_target_subpath(remote_target_subpath),
        "enqueued_at": timezone.now().isoformat(),
    }
    _write_json_file(request_path, payload)
    return request_path


def _load_remote_dispatch_request(task: ComputeTask) -> Dict[str, Any]:

    request_path = _worker_signal_path(task, REMOTE_DISPATCH_REQUEST_FILENAME)
    payload = _read_json_file(request_path)
    if payload is None:
        raise FileNotFoundError(f"Missing remote dispatch request: {request_path}")
    required_fields = [
        "source_dir",
        "download_dir",
        "func_path",
        "remote_target_subpath",
    ]
    missing_fields = [field for field in required_fields if not str(payload.get(field) or "").strip()]
    if missing_fields:
        raise ValueError(
            f"Remote dispatch request is missing required fields {missing_fields}: {request_path}"
        )
    return payload


def _write_worker_started_signal(task_dir: str, *, pid: int, server_name: str, remote_target: str) -> None:

    _write_json_file(
        _worker_signal_path(task_dir, REMOTE_WORKER_STARTED_FILENAME),
        {
            "pid": int(pid),
            "server_name": str(server_name),
            "remote_target": str(remote_target),
            "started_at": timezone.now().isoformat(),
        },
    )


def _write_worker_heartbeat_signal(
    task_dir: str,
    *,
    stage: str,
    detail: str = "",
) -> None:

    _write_json_file(
        _worker_signal_path(task_dir, REMOTE_WORKER_HEARTBEAT_FILENAME),
        {
            "pid": os.getpid(),
            "stage": str(stage),
            "detail": str(detail or ""),
            "timestamp": timezone.now().isoformat(),
        },
    )


def _write_worker_result_signal(
    task_dir: str,
    *,
    status: str,
    message: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:

    payload: Dict[str, Any] = {
        "pid": os.getpid(),
        "status": str(status),
        "message": str(message),
        "finished_at": timezone.now().isoformat(),
    }
    if extra:
        payload.update(extra)
    _write_json_file(
        _worker_signal_path(task_dir, REMOTE_WORKER_RESULT_FILENAME),
        payload,
    )


def _get_remote_server_info_file_path() -> str:

    return os.path.join(
        settings.BASE_DIR,
        "static",
        "remote_server_info",
        "remote_server_info.json",
    )


def _load_remote_server_pool(
    server_info_file_path: Optional[str] = None,
) -> List[Dict[str, Any]]:

    if server_info_file_path is None:
        server_info_file_path = _get_remote_server_info_file_path()

    try:
        with open(server_info_file_path, "r", encoding="utf-8") as handle:
            raw_servers = json.load(handle)
    except FileNotFoundError:
        logger.error("远程服务器配置文件不存在：%s", server_info_file_path)
        return []
    except json.JSONDecodeError as exc:
        logger.error("远程服务器配置文件不是合法 JSON：%s", exc)
        return []

    if not isinstance(raw_servers, list):
        logger.error("远程服务器配置必须是列表结构：%s", server_info_file_path)
        return []

    normalized_servers: List[Dict[str, Any]] = []
    for order, item in enumerate(raw_servers):
        if not isinstance(item, dict):
            continue

        server_name = item.get("server_name")
        raw_remote_ip = item.get("IP")
        remote_target_dir = item.get("remote_target_dir")
        try:
            task_limit = int(item.get("task_limit"))
            ssh_port = int(item.get("ssh_port", 22))
        except (TypeError, ValueError):
            continue

        enabled = bool(item.get("enabled", True))
        remote_login = _normalize_remote_login(raw_remote_ip)
        remote_ip = _normalize_remote_ip(raw_remote_ip)
        capabilities = _normalize_capabilities(item.get("capabilities"))

        if (
            not server_name
            or not remote_login
            or not remote_target_dir
            or task_limit <= 0
            or ssh_port <= 0
        ):
            continue

        normalized_servers.append(
            {
                "server_name": server_name,
                "IP": remote_ip,
                "remote_login": remote_login,
                "task_limit": task_limit,
                "ssh_port": ssh_port,
                "enabled": enabled,
                "capabilities": capabilities,
                "remote_target_dir": str(remote_target_dir).rstrip("/"),
                "order": order,
            }
        )

    return normalized_servers


def _normalize_remote_login(remote_login: Any) -> str:

    normalized = str(remote_login or "").strip()
    if normalized.endswith(":"):
        normalized = normalized[:-1]
    return normalized


def _normalize_remote_ip(remote_login: Any) -> str:

    normalized_login = _normalize_remote_login(remote_login)
    if not normalized_login:
        return ""
    return f"{normalized_login}:"


def _normalize_capabilities(raw_capabilities: Any) -> List[str]:

    if raw_capabilities is None:
        return []

    if isinstance(raw_capabilities, str):
        candidates: Sequence[Any] = [raw_capabilities]
    elif isinstance(raw_capabilities, (list, tuple, set)):
        candidates = list(raw_capabilities)
    else:
        return []

    normalized: List[str] = []
    for item in candidates:
        capability = str(item or "").strip()
        if not capability:
            continue
        if capability not in normalized:
            normalized.append(capability)
    return normalized


def _filter_servers_by_capability(
    servers: Sequence[Dict[str, Any]],
    required_capability: str,
) -> List[Dict[str, Any]]:

    return [
        server
        for server in servers
        if server.get("enabled", False)
        and required_capability in server.get("capabilities", [])
    ]


def _get_remote_server_by_login(
    remote_login: str,
    server_info_file_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:

    normalized_login = _normalize_remote_login(remote_login)
    for server in _load_remote_server_pool(server_info_file_path=server_info_file_path):
        if server.get("remote_login") == normalized_login:
            return server
    return None


def _resolve_remote_connection_info(
    remote_login: str,
    server_info_file_path: Optional[str] = None,
) -> Tuple[str, int, str]:

    normalized_login = _normalize_remote_login(remote_login)
    matched_server = _get_remote_server_by_login(
        normalized_login,
        server_info_file_path=server_info_file_path,
    )
    ssh_port = int(matched_server["ssh_port"]) if matched_server is not None else 22
    remote_ip = (
        str(matched_server["IP"])
        if matched_server is not None
        else _normalize_remote_ip(normalized_login)
    )
    return normalized_login, ssh_port, remote_ip


def _build_ssh_command(
    remote_login: str,
    *,
    batch_mode: bool = True,
    allocate_tty: bool = False,
    ssh_port: Optional[int] = None,
    server_info_file_path: Optional[str] = None,
) -> List[str]:

    normalized_login = _normalize_remote_login(remote_login)
    resolved_ssh_port = ssh_port
    if resolved_ssh_port is None:
        _, resolved_ssh_port, _ = _resolve_remote_connection_info(
            remote_login,
            server_info_file_path=server_info_file_path,
        )
    ssh_cmd: List[str] = ["ssh"]
    if batch_mode:
        ssh_cmd.extend(["-o", "BatchMode=yes"])
    if allocate_tty:
        ssh_cmd.append("-tt")
    if resolved_ssh_port:
        ssh_cmd.extend(["-p", str(resolved_ssh_port)])
    ssh_cmd.append(normalized_login)
    return ssh_cmd


def _build_rsync_remote_prefix(
    remote_login: str,
    *,
    ssh_port: Optional[int] = None,
    server_info_file_path: Optional[str] = None,
) -> Tuple[str, str]:

    normalized_login = _normalize_remote_login(remote_login)
    remote_ip = _normalize_remote_ip(normalized_login)
    resolved_ssh_port = ssh_port
    if resolved_ssh_port is None:
        _, resolved_ssh_port, remote_ip = _resolve_remote_connection_info(
            remote_login,
            server_info_file_path=server_info_file_path,
        )
    ssh_transport = f"ssh -o BatchMode=yes -p {resolved_ssh_port}"
    return remote_ip, ssh_transport


def _run_remote_settings_check(
    remote_login: str,
    task_type: str,
    *,
    ssh_port: Optional[int] = None,
) -> Tuple[bool, str]:

    required_keys = get_required_settings_keys_for_task(task_type)
    if not required_keys:
        return True, ""

    keys_json = json.dumps(required_keys, ensure_ascii=False)
    settings_path = "/etc/cemp/CEMPsettings.ini"
    python_code = f"""
import json
import os

from cemp_software_settings import load_and_apply_settings

required_keys = json.loads({keys_json!r})
result = load_and_apply_settings({settings_path!r})
missing = []
for key in required_keys:
    value = result.get(key)
    if not value:
        missing.append({{"key": key, "reason": "empty", "value": value}})
        continue
    if not os.path.exists(str(value)):
        missing.append({{"key": key, "reason": "missing_path", "value": str(value)}})
if missing:
    print(json.dumps({{"ok": False, "missing": missing}}, ensure_ascii=False))
    raise SystemExit(2)
print(json.dumps({{"ok": True}}, ensure_ascii=False))
""".strip()

    try:
        completed = _ssh_run_command(
            remote_login,
            ["python3", "-c", python_code],
            timeout=90,
            ssh_port=ssh_port,
        )
    except subprocess.CalledProcessError as exc:
        stderr_text = (exc.stderr or "").strip()
        stdout_text = (exc.stdout or "").strip()
        detail = stderr_text or stdout_text or str(exc)
        return False, f"cemp_software_settings validation failed: {detail[:2000]}"

    stdout_text = (completed.stdout or "").strip()
    if not stdout_text:
        return False, "cemp_software_settings validation returned empty output."
    last_line = stdout_text.splitlines()[-1]
    try:
        payload = json.loads(last_line)
    except json.JSONDecodeError:
        return False, f"cemp_software_settings validation returned non-JSON output: {last_line[:500]}"
    if not payload.get("ok"):
        return False, json.dumps(payload, ensure_ascii=False)
    return True, ""


def _run_markov_runtime_check(
    remote_login: str,
    *,
    ssh_port: Optional[int] = None,
) -> Tuple[bool, str]:

    gdynet_dir = str(getattr(settings, "MARKOV_GDYNET_PACKAGE_DIR", "") or "").strip()
    if not gdynet_dir:
        return False, "MARKOV_GDYNET_PACKAGE_DIR is not configured."

    python_code = (
        "import os, sys; "
        f"ok = os.path.isdir({gdynet_dir!r}) and os.path.isdir('/etc/cemp'); "
        "sys.exit(0 if ok else 1)"
    )
    try:
        _ssh_run_command(
            remote_login,
            ["python3", "-c", python_code],
            timeout=30,
            ssh_port=ssh_port,
        )
    except subprocess.CalledProcessError as exc:
        stderr_text = (exc.stderr or "").strip()
        stdout_text = (exc.stdout or "").strip()
        detail = stderr_text or stdout_text or str(exc)
        return False, f"Markov runtime validation failed: {detail[:2000]}"
    return True, ""


def _check_remote_server_runtime_health(
    server: Dict[str, Any],
    task_type: str,
    *,
    cache_ttl_seconds: int = REMOTE_HEALTH_CACHE_TTL_SECONDS,
) -> Tuple[bool, str]:

    capability = get_required_capability(task_type)
    if capability is None:
        return False, f"Task type {task_type} is not registered for remote capability dispatch."

    cache_key = (str(server["server_name"]), task_type)
    now_ts = time.time()
    cached = _REMOTE_HEALTH_CACHE.get(cache_key)
    if cached and now_ts - cached.get("checked_at", 0.0) <= cache_ttl_seconds:
        return bool(cached.get("success")), str(cached.get("error", ""))

    remote_login = str(server["remote_login"])
    ssh_port = int(server.get("ssh_port", 22))
    remote_target_dir = str(server["remote_target_dir"])

    try:
        _ssh_run_command(
            remote_login,
            [
                "python3",
                "-c",
                (
                    "import os, sys; "
                    f"sys.exit(0 if os.path.isdir({remote_target_dir!r}) else 1)"
                ),
            ],
            timeout=20,
            ssh_port=ssh_port,
        )
    except subprocess.TimeoutExpired as exc:
        result = (False, f"Remote target directory check timed out: {exc}")
        _REMOTE_HEALTH_CACHE[cache_key] = {
            "checked_at": now_ts,
            "success": result[0],
            "error": result[1],
        }
        return result
    except subprocess.CalledProcessError as exc:
        stderr_text = (exc.stderr or "").strip()
        stdout_text = (exc.stdout or "").strip()
        detail = stderr_text or stdout_text or str(exc)
        result = (False, f"Remote target directory check failed: {detail[:1000]}")
        _REMOTE_HEALTH_CACHE[cache_key] = {
            "checked_at": now_ts,
            "success": result[0],
            "error": result[1],
        }
        return result

    if capability == MARKOV_ANALYSIS:
        success, error_message = _run_markov_runtime_check(remote_login, ssh_port=ssh_port)
    else:
        success, error_message = _run_remote_settings_check(
            remote_login,
            task_type,
            ssh_port=ssh_port,
        )

    _REMOTE_HEALTH_CACHE[cache_key] = {
        "checked_at": now_ts,
        "success": success,
        "error": error_message,
    }
    return success, error_message


def _normalize_remote_target_subpath(
    remote_target: str,
    servers: List[Dict[str, Any]],
) -> str:

    normalized_target = str(remote_target or "").replace("\\", "/").rstrip("/")
    if not normalized_target:
        return ""

    for server in servers:
        base_dir = str(server["remote_target_dir"]).replace("\\", "/").rstrip("/")
        if normalized_target == base_dir:
            return ""
        prefix = f"{base_dir}/"
        if normalized_target.startswith(prefix):
            return normalized_target[len(prefix) :]

    if normalized_target.startswith("/"):
        return normalized_target.lstrip("/")

    return normalized_target.strip("/")


def _build_remote_target_path(server: Dict[str, Any], remote_target_subpath: str) -> str:

    base_dir = str(server["remote_target_dir"]).replace("\\", "/").rstrip("/")
    parts = [part for part in remote_target_subpath.split("/") if part]
    if not parts:
        return base_dir
    return posixpath.join(base_dir, *parts)


def _get_remote_server_by_name(
    server_name: str,
    server_info_file_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:

    for server in _load_remote_server_pool(server_info_file_path=server_info_file_path):
        if server["server_name"] == server_name:
            return server
    return None


def select_least_utilized_remote_server(
    server_info_file_path: Optional[str] = None,
    required_capability: Optional[str] = None,
    task_type: Optional[str] = None,
    enable_health_checks: bool = False,
) -> Optional[Dict[str, Any]]:

    servers = _load_remote_server_pool(server_info_file_path=server_info_file_path)
    if not servers:
        return None

    if required_capability is not None:
        servers = _filter_servers_by_capability(servers, required_capability)
    else:
        servers = [server for server in servers if server.get("enabled", False)]

    if not servers:
        return None

    server_names = [server["server_name"] for server in servers]
    pending_rows = (
        ComputeTask.objects.filter(
            remote_type="remote",
            status="pending",
            server_name__in=server_names,
        )
        .values("server_name")
        .annotate(pending_count=Count("id"))
    )
    pending_map = {
        row["server_name"]: row["pending_count"] for row in pending_rows if row["server_name"]
    }

    
    last_assigned_rows = (
        ComputeTask.objects.filter(
            remote_type="remote",
            server_name__in=server_names,
        )
        .exclude(server_name__isnull=True)
        .exclude(server_name="")
        .values("server_name")
        .annotate(last_assigned_at=Max("created_at"))
    )
    last_assigned_map = {
        row["server_name"]: row["last_assigned_at"]
        for row in last_assigned_rows
        if row["server_name"]
    }

    candidates: List[Dict[str, Any]] = []
    for server in servers:
        if enable_health_checks and task_type:
            is_healthy, health_error = _check_remote_server_runtime_health(server, task_type)
            if not is_healthy:
                logger.warning(
                    "Remote server skipped by health check: server_name=%s, task_type=%s, error=%s",
                    server["server_name"],
                    task_type,
                    health_error,
                )
                continue

        pending_count = pending_map.get(server["server_name"], 0)
        task_limit = server["task_limit"]
        if pending_count >= task_limit:
            continue

        last_assigned_at = last_assigned_map.get(server["server_name"])
        sort_last_assigned = (
            last_assigned_at.timestamp() if last_assigned_at is not None else float("-inf")
        )
        candidates.append(
            {
                **server,
                "pending_count": pending_count,
                "utilization": pending_count / task_limit,
                "last_assigned_at": last_assigned_at,
                "_sort_last_assigned": sort_last_assigned,
            }
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item["utilization"],
            item["_sort_last_assigned"],
            item["order"],
        )
    )
    selected_server = candidates[0].copy()
    selected_server.pop("_sort_last_assigned", None)
    return selected_server


def _mark_task_failed(task: ComputeTask, error_message: str) -> None:

    mark_task_failed(
        task,
        error_message,
        write_failure_file=True,
        create_failure_dir=False,
        overwrite_failure_file=False,
    )


def _task_has_terminal_signal_files(task: ComputeTask) -> Tuple[bool, bool]:

    task_dir = str(getattr(task, "folder_path", "") or "").strip()
    if not task_dir:
        return False, False

    success_file = os.path.join(task_dir, "success.txt")
    failure_file = os.path.join(task_dir, "failure.txt")
    return os.path.exists(success_file), os.path.exists(failure_file)


def _task_pid_is_alive(task: ComputeTask) -> bool:

    raw_pid = getattr(task, "pid", None)
    if raw_pid in (None, ""):
        return False

    try:
        return bool(psutil.pid_exists(int(raw_pid)))
    except (TypeError, ValueError, psutil.Error):
        return False


def _remote_task_heartbeat_timeout(task: ComputeTask) -> Optional[timedelta]:

    task_type = str(getattr(task, "task_type", "") or "").strip()
    if not task_type:
        return None
    if task_type in REMOTE_TASK_HEARTBEAT_TIMEOUTS:
        return REMOTE_TASK_HEARTBEAT_TIMEOUTS[task_type]
    for prefix, timeout_value in REMOTE_TASK_TYPE_HEARTBEAT_PREFIX_TIMEOUTS.items():
        if task_type.startswith(prefix):
            return timeout_value
    return None


def _task_last_progress_at(task: ComputeTask):

    return getattr(task, "last_heartbeat_at", None)


def _is_remote_task_heartbeat_stale(
    task: ComputeTask,
    *,
    now=None,
) -> bool:

    if getattr(task, "remote_type", None) != "remote":
        return False
    if getattr(task, "status", None) != "pending":
        return False

    timeout_value = _remote_task_heartbeat_timeout(task)
    if timeout_value is None:
        return False

    has_success, has_failure = _task_has_terminal_signal_files(task)
    if has_success or has_failure:
        return False

    last_progress_at = _task_last_progress_at(task)
    if last_progress_at is None:
        return False

    current_time = now or timezone.now()
    return current_time - last_progress_at > timeout_value


def _kill_task_pid_tree(task: ComputeTask) -> Dict[str, Any]:

    raw_pid = getattr(task, "pid", None)
    result = {
        "pid": raw_pid,
        "terminated": 0,
        "killed": 0,
        "missing": 0,
    }
    if raw_pid in (None, ""):
        return result

    try:
        process = psutil.Process(int(raw_pid))
    except (TypeError, ValueError, psutil.Error):
        result["missing"] = 1
        return result

    processes = process.children(recursive=True)
    processes.append(process)

    for item in processes:
        try:
            item.terminate()
            result["terminated"] += 1
        except psutil.NoSuchProcess:
            result["missing"] += 1
        except psutil.Error:
            logger.warning("Failed to terminate pid=%s for task_id=%s", item.pid, task.task_id)

    gone, alive = psutil.wait_procs(processes, timeout=5)
    for item in alive:
        try:
            item.kill()
            result["killed"] += 1
        except psutil.NoSuchProcess:
            result["missing"] += 1
        except psutil.Error:
            logger.warning("Failed to kill pid=%s for task_id=%s", item.pid, task.task_id)

    return result


def _mark_task_success(task: ComputeTask) -> None:

    task.status = "success"
    task.last_heartbeat_at = timezone.now()
    save_task_with_sqlite_retry(
        task,
        update_fields=["status", "last_heartbeat_at"],
        operation_name="mark_task_success",
    )


def _touch_remote_task_heartbeat(task: ComputeTask) -> None:

    if _remote_task_heartbeat_timeout(task) is None:
        return
    touch_task_heartbeat(task)


def _signal_remote_task_progress(
    task: ComputeTask,
    *,
    scheduler_managed: bool,
    task_dir: str,
    stage: str,
    detail: str = "",
) -> None:

    if scheduler_managed:
        _write_worker_heartbeat_signal(task_dir, stage=stage, detail=detail)
        return
    _touch_remote_task_heartbeat(task)


def _write_local_text_signal(path: str, content: str) -> None:

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(str(content))


def _sync_task_heartbeat_from_worker_signal(task: ComputeTask) -> bool:

    try:
        payload = _read_json_file(_worker_signal_path(task, REMOTE_WORKER_HEARTBEAT_FILENAME))
    except Exception:
        logger.exception("Failed to read worker heartbeat signal for task_id=%s", task.task_id)
        return False
    if payload is None:
        return False

    timestamp_text = str(payload.get("timestamp") or "").strip()
    if not timestamp_text:
        return False
    try:
        heartbeat_at = timezone.datetime.fromisoformat(timestamp_text)
        if timezone.is_naive(heartbeat_at):
            heartbeat_at = timezone.make_aware(heartbeat_at, timezone.get_current_timezone())
    except Exception:
        logger.warning(
            "Invalid worker heartbeat timestamp for task_id=%s: %s",
            task.task_id,
            timestamp_text,
        )
        return False

    current_value = getattr(task, "last_heartbeat_at", None)
    if current_value is not None and heartbeat_at <= current_value:
        return False

    task.last_heartbeat_at = heartbeat_at
    save_task_with_sqlite_retry(
        task,
        update_fields=["last_heartbeat_at"],
        operation_name="scheduler_sync_worker_heartbeat",
    )
    return True


def _is_stale_remote_task(task: ComputeTask) -> bool:

    if getattr(task, "remote_type", None) != "remote":
        return False
    if getattr(task, "status", None) not in {"queuing", "pending"}:
        return False
    if getattr(task, "pid", None) in (None, ""):
        return False
    if _task_pid_is_alive(task):
        return False

    has_success, has_failure = _task_has_terminal_signal_files(task)
    return not (has_success or has_failure)


def reap_stale_remote_tasks(
    *,
    statuses: Sequence[str] = ("queuing", "pending"),
    limit: Optional[int] = None,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:

    normalized_statuses = [str(status).strip() for status in statuses if str(status).strip()]
    if not normalized_statuses:
        return []

    queryset = ComputeTask.objects.filter(
        remote_type="remote",
        status__in=normalized_statuses,
    ).order_by("-priority", "created_at")

    if limit is not None:
        queryset = queryset[:limit]

    reaped_tasks: List[Dict[str, Any]] = []
    for task in list(queryset):
        if not _is_stale_remote_task(task):
            continue

        status_before = str(task.status)
        failure_message = (
            QUEUED_DISPATCHER_DISAPPEARED_MESSAGE
            if status_before == "queuing"
            else PENDING_REMOTE_PROCESS_DISAPPEARED_MESSAGE
        )
        logger.warning(
            "Stale remote task detected: id=%s, task_id=%s, task_type=%s, status=%s, pid=%s, dry_run=%s",
            task.id,
            task.task_id,
            task.task_type,
            status_before,
            task.pid,
            dry_run,
        )

        if not dry_run:
            mark_task_failed(
                task,
                failure_message,
                write_failure_file=True,
                create_failure_dir=False,
                overwrite_failure_file=False,
            )

        reaped_tasks.append(
            {
                "id": task.id,
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status_before": status_before,
                "failure_message": failure_message,
                "folder_path": getattr(task, "folder_path", ""),
            }
        )

    return reaped_tasks


def reconcile_remote_tasks(
    *,
    limit: Optional[int] = None,
    dry_run: bool = False,
    kill_stuck_pids: bool = True,
) -> List[Dict[str, Any]]:

    queryset = (
        ComputeTask.objects.filter(remote_type="remote", status__in=["queuing", "pending"])
        .order_by("created_at", "id")
    )
    if limit is not None:
        queryset = queryset[:limit]

    reconciled: List[Dict[str, Any]] = []
    for task in list(queryset):
        if getattr(task, "status", None) == "pending":
            _sync_task_heartbeat_from_worker_signal(task)
            task.refresh_from_db()
        status_before = str(task.status)
        has_success, has_failure = _task_has_terminal_signal_files(task)
        action = ""
        reason = ""
        kill_summary: Optional[Dict[str, Any]] = None

        if status_before == "pending" and has_failure:
            action = "mark_failed_from_failure_signal"
            reason = "Remote task directory already contains failure.txt."
        elif status_before == "pending" and has_success:
            action = "mark_success_from_success_signal"
            reason = "Remote task directory already contains success.txt."
        elif status_before == "queuing" and _is_stale_remote_task(task):
            action = "mark_failed_stale_queuing"
            reason = QUEUED_DISPATCHER_DISAPPEARED_MESSAGE
        elif status_before == "pending" and _is_stale_remote_task(task):
            action = "mark_failed_stale_pending"
            reason = PENDING_REMOTE_PROCESS_DISAPPEARED_MESSAGE
        elif status_before == "pending" and _is_remote_task_heartbeat_stale(task):
            action = "mark_failed_heartbeat_timeout"
            reason = PENDING_REMOTE_HEARTBEAT_TIMEOUT_MESSAGE

        if not action:
            continue

        if action == "mark_failed_heartbeat_timeout" and kill_stuck_pids and not dry_run:
            kill_summary = _kill_task_pid_tree(task)
            logger.warning(
                "Killed stale pending task PID tree: id=%s task_id=%s summary=%s",
                task.id,
                task.task_id,
                kill_summary,
            )

        if not dry_run:
            if action == "mark_success_from_success_signal" and task.task_type == "Markov_GDyNet_analysis":
                _finalize_markov_task_from_local_signals(task, _task_folder_path(task))
            elif action == "mark_success_from_success_signal":
                _mark_task_success(task)
            else:
                mark_task_failed(
                    task,
                    reason,
                    write_failure_file=action != "mark_failed_from_failure_signal",
                    create_failure_dir=False,
                    overwrite_failure_file=False,
                )

        reconciled.append(
            {
                "id": task.id,
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status_before": status_before,
                "action": action,
                "reason": reason,
                "folder_path": getattr(task, "folder_path", ""),
                "kill_summary": kill_summary,
            }
        )

    return reconciled


def _reap_stale_remote_queue_head() -> Optional[Dict[str, Any]]:

    top_task = (
        ComputeTask.objects.filter(status="queuing", remote_type="remote")
        .order_by("created_at", "id")
        .first()
    )
    if top_task is None or not _is_stale_remote_task(top_task):
        return None

    logger.warning(
        "Reaping stale remote queue head: id=%s, task_id=%s, task_type=%s, pid=%s",
        top_task.id,
        top_task.task_id,
        top_task.task_type,
        top_task.pid,
    )
    mark_task_failed(
        top_task,
        QUEUED_DISPATCHER_DISAPPEARED_MESSAGE,
        write_failure_file=True,
        create_failure_dir=False,
        overwrite_failure_file=False,
    )
    return {
        "id": top_task.id,
        "task_id": top_task.task_id,
        "task_type": top_task.task_type,
        "pid": top_task.pid,
    }


def _ensure_remote_task_queued(task: ComputeTask) -> None:

    update_fields: List[str] = []
    if getattr(task, "remote_type", None) != "remote":
        task.remote_type = "remote"
        update_fields.append("remote_type")
    if getattr(task, "status", None) not in {"success", "failed"}:
        if task.status != "queuing":
            task.status = "queuing"
            update_fields.append("status")
    if getattr(task, "server_name", None):
        task.server_name = None
        update_fields.append("server_name")
    if getattr(task, "last_heartbeat_at", None) is not None:
        task.last_heartbeat_at = None
        update_fields.append("last_heartbeat_at")
    if update_fields:
        save_task_with_sqlite_retry(
            task,
            update_fields=update_fields,
            operation_name="ensure_remote_task_queued",
        )


def _claim_remote_dispatch_slot(task: ComputeTask) -> Optional[Dict[str, Any]]:

    with transaction.atomic():
        task.refresh_from_db()

        if task.status in {"success", "failed"}:
            return None

        top_task = (
            ComputeTask.objects.filter(status="queuing", remote_type="remote")
            .order_by("-priority", "created_at")
            .first()
        )
        if top_task is not None and top_task.task_id != task.task_id:
            return None

        required_capability = get_required_capability(task.task_type)
        selected_server = select_least_utilized_remote_server(
            required_capability=required_capability,
            task_type=task.task_type,
            enable_health_checks=True,
        )
        if selected_server is None:
            if task.status != "queuing" or getattr(task, "server_name", None):
                task.status = "queuing"
                task.server_name = None
                task.save(update_fields=["status", "server_name"])
            return None

        heartbeat_now = timezone.now()
        updated = ComputeTask.objects.filter(
            task_id=task.task_id,
            remote_type="remote",
            status__in=["queuing", "created"],
        ).update(
            status="pending",
            server_name=selected_server["server_name"],
            last_heartbeat_at=heartbeat_now,
        )

        if updated:
            task.status = "pending"
            task.server_name = selected_server["server_name"]
            task.last_heartbeat_at = heartbeat_now
            return selected_server

        task.refresh_from_db()
        if task.status == "pending" and task.server_name:
            return _get_remote_server_by_name(task.server_name)

        return None


def _execute_remote_task_with_result_handling(
    task_func,
    source_dir: str,
    download_dir: str,
    task: ComputeTask,
    remote_target: str,
    remote_login: str,
):

    try:
        result = task_func(
            source_dir,
            download_dir,
            task,
            remote_target,
            remote_IP=remote_login,
        )

        if isinstance(result, JsonResponse):
            status_code = getattr(result, "status_code", 200)
            if status_code >= 400:
                try:
                    detail = result.content.decode("utf-8", errors="ignore")
                except Exception:
                    detail = "Remote task returned HTTP error"
                _mark_task_failed(task, f"HTTP {status_code}: {detail[:2000]}")
                return task
    except Exception as exc:
        _mark_task_failed(task, f"{type(exc).__name__}: {exc}")
        raise

    return task


def _dispatch_remote_task(
    task_func,
    source_dir: str,
    download_dir: str,
    task: ComputeTask,
    remote_target: str,
):

    if is_deprecated_remote_task_type(task.task_type):
        _mark_task_failed(
            task,
            f"Task type {task.task_type} has been deprecated and is no longer scheduled on remote capability pools.",
        )
        return task

    required_capability = get_required_capability(task.task_type)
    if required_capability is None:
        _mark_task_failed(
            task,
            f"No remote capability is registered for task type {task.task_type}.",
        )
        return task

    server_pool = _load_remote_server_pool()
    if not server_pool:
        _mark_task_failed(task, "No remote servers are configured.")
        return task

    compatible_servers = _filter_servers_by_capability(server_pool, required_capability)
    if not compatible_servers:
        _mark_task_failed(
            task,
            f"No enabled remote servers are registered for capability {required_capability}.",
        )
        return task

    remote_target_subpath = _normalize_remote_target_subpath(remote_target, server_pool)
    if not remote_target_subpath:
        _mark_task_failed(task, "Remote target path is empty and cannot be dispatched.")
        return task

    _ensure_remote_task_queued(task)

    while True:
        time.sleep(REMOTE_TASK_POLL_INTERVAL)

        reconciled_tasks = reconcile_remote_tasks(
            limit=REMOTE_RECONCILE_SCAN_LIMIT_PER_LOOP,
            dry_run=False,
            kill_stuck_pids=True,
        )
        if reconciled_tasks:
            logger.info(
                "Remote task reconciliation changed queue state before dispatch retry: actions=%s",
                [item["action"] for item in reconciled_tasks],
            )
            continue

        top_task = (
            ComputeTask.objects.filter(status="queuing", remote_type="remote")
            .order_by("-priority", "created_at")
            .first()
        )
        if top_task is not None and top_task.task_id != task.task_id:
            continue

        selected_server = None
        lock_error_message = ""
        for attempt, backoff_seconds in enumerate(
            CLAIM_REMOTE_SLOT_RETRY_DELAYS_SECONDS,
            start=1,
        ):
            try:
                selected_server = _claim_remote_dispatch_slot(task)
                lock_error_message = ""
                break
            except OperationalError as exc:
                error_text = str(exc)
                if SQLITE_LOCK_ERROR_MARKER not in error_text.lower():
                    raise
                lock_error_message = error_text
                logger.warning(
                    "Remote dispatch slot claim hit SQLite lock: task_id=%s, task_type=%s, attempt=%s, backoff_seconds=%s, error=%s",
                    task.task_id,
                    task.task_type,
                    attempt,
                    backoff_seconds,
                    error_text,
                )
                time.sleep(backoff_seconds)

        if lock_error_message and selected_server is None:
            logger.warning(
                "Remote dispatch slot claim exhausted SQLite lock retries: task_id=%s, task_type=%s, error=%s",
                task.task_id,
                task.task_type,
                lock_error_message,
            )
            continue

        if selected_server is None:
            continue

        _touch_remote_task_heartbeat(task)
        actual_remote_target = _build_remote_target_path(
            selected_server,
            remote_target_subpath,
        )
        logger.info(
            "Remote task dispatched: task_id=%s, server_name=%s, utilization=%.4f, pending_count=%s, remote_target=%s",
            task.task_id,
            selected_server["server_name"],
            selected_server.get("utilization", 0.0),
            selected_server.get("pending_count", 0),
            actual_remote_target,
        )
        return _execute_remote_task_with_result_handling(
            task_func=task_func,
            source_dir=source_dir,
            download_dir=download_dir,
            task=task,
            remote_target=actual_remote_target,
            remote_login=selected_server["IP"],
        )


def _pull_remote_to_local(remote_IP, remote_work_dir, abs_download_dir):

    remote_src_prefix, ssh_transport = _build_rsync_remote_prefix(remote_IP)
    remote_src = remote_src_prefix + remote_work_dir.rstrip("/")
    pull_cmd = [
        "rsync",
        "-avz",
        "--delete",
        "-I",
        "-e",
        ssh_transport,
        remote_src + "/",
        os.path.abspath(abs_download_dir).rstrip("/") + "/",
    ]
    subprocess.run(pull_cmd, check=True)


def _run_remote_notebook_sequence(
    source_dir: str,
    download_dir: str,
    task: ComputeTask,
    remote_target: str,
    remote_IP: str,
    notebooks_to_run: Sequence[str],
    *,
    after_remote_success=None,
    after_success_local=None,
    scheduler_managed: bool = False,
) -> Optional[Dict[str, Any]]:

    abs_download_dir = os.path.abspath(download_dir)

    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            shutil.copy(source_file, download_dir)
        elif os.path.isdir(source_file):
            shutil.copytree(source_file, os.path.join(download_dir, filename))

    _signal_remote_task_progress(
        task,
        scheduler_managed=scheduler_managed,
        task_dir=abs_download_dir,
        stage="copy_local_template",
    )
    copy_unique_folder(
        download_dir,
        remote_target=remote_target,
        remote_IP=remote_IP,
    )
    _signal_remote_task_progress(
        task,
        scheduler_managed=scheduler_managed,
        task_dir=abs_download_dir,
        stage="copy_remote_input",
    )

    remote_work_dir = posixpath.join(
        remote_target.rstrip("/"),
        os.path.basename(abs_download_dir),
    )
    remote_login = remote_IP[:-1] if remote_IP.endswith(":") else remote_IP
    error_info = None

    for notebook_name in notebooks_to_run:
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=abs_download_dir,
            stage="run_notebook_start",
            detail=notebook_name,
        )
        run_cmd = (
            f"cd {shlex.quote(remote_work_dir)} && "
            f"nb={shlex.quote(notebook_name)}; "
            f'log="${{nb}}.log"; '
            "export PYTHONUNBUFFERED=1; "
            "stdbuf -oL -eL "
            "jupyter nbconvert --to notebook --execute "
            "--ExecutePreprocessor.timeout=None "
            f"--output {shlex.quote(notebook_name)} {shlex.quote(notebook_name)} "
            '2>&1 | tee -a "${log}"'
        )

        try:
            _ssh_run(remote_login, run_cmd)
            _signal_remote_task_progress(
                task,
                scheduler_managed=scheduler_managed,
                task_dir=abs_download_dir,
                stage="run_notebook_done",
                detail=notebook_name,
            )
        except subprocess.CalledProcessError as e:
            failure_msg = f"Failed to run notebook {notebook_name}: {e.stderr or e.stdout or str(e)}"
            echo_fail = (
                f"cd {shlex.quote(remote_work_dir)} && "
                f"printf '%s\\n' {shlex.quote(failure_msg)} > failure.txt"
            )
            try:
                _ssh_run(remote_login, echo_fail)
                append_log_tail = (
                    f"cd {shlex.quote(remote_work_dir)} && "
                    f"printf '\\n===== TAIL of {shlex.quote(notebook_name)}.log (last 200 lines) =====\\n' >> failure.txt; "
                    f"test -s {shlex.quote(notebook_name + '.log')} && tail -n 200 {shlex.quote(notebook_name + '.log')} >> failure.txt || true"
                )
                try:
                    _ssh_run(remote_login, append_log_tail)
                except Exception:
                    pass
            except Exception:
                pass

            if scheduler_managed:
                _write_local_text_signal(
                    os.path.join(abs_download_dir, "failure.txt"),
                    failure_msg,
                )
            else:
                mark_task_failed(
                    task,
                    f"Failed to run notebook on remote: {str(e)}",
                    write_failure_file=True,
                    create_failure_dir=False,
                    overwrite_failure_file=False,
                )
                _touch_remote_task_heartbeat(task)
            error_info = {
                "error": f"Failed to run notebook on remote: {str(e)}",
                "traceback": traceback.format_exc(),
                "stdout": e.stdout,
                "stderr": e.stderr,
            }
            break
        except Exception as e:
            failure_msg = f"Local wrapper error before/after remote run: {str(e)}"
            echo_fail = (
                f"cd {shlex.quote(remote_work_dir)} && "
                f"printf '%s\\n' {shlex.quote(failure_msg)} > failure.txt"
            )
            try:
                _ssh_run(remote_login, echo_fail)
            except Exception:
                pass

            if scheduler_managed:
                _write_local_text_signal(
                    os.path.join(abs_download_dir, "failure.txt"),
                    failure_msg,
                )
            else:
                mark_task_failed(
                    task,
                    failure_msg,
                    write_failure_file=True,
                    create_failure_dir=False,
                    overwrite_failure_file=False,
                )
                _touch_remote_task_heartbeat(task)
            error_info = {
                "error": f"An error occurred in local wrapper: {str(e)}",
                "traceback": traceback.format_exc(),
            }
            break

    if error_info is None:
        if after_remote_success is not None:
            try:
                _signal_remote_task_progress(
                    task,
                    scheduler_managed=scheduler_managed,
                    task_dir=abs_download_dir,
                    stage="after_remote_success_start",
                )
                after_remote_success(remote_login, remote_work_dir, task)
                _signal_remote_task_progress(
                    task,
                    scheduler_managed=scheduler_managed,
                    task_dir=abs_download_dir,
                    stage="after_remote_success_done",
                )
            except Exception as e:
                failure_msg = f"Remote post-processing failed: {str(e)}"
                echo_fail = (
                    f"cd {shlex.quote(remote_work_dir)} && "
                    f"printf '%s\\n' {shlex.quote(failure_msg)} > failure.txt"
                )
                try:
                    _ssh_run(remote_login, echo_fail)
                except Exception:
                    pass

                if scheduler_managed:
                    _write_local_text_signal(
                        os.path.join(abs_download_dir, "failure.txt"),
                        failure_msg,
                    )
                else:
                    mark_task_failed(
                        task,
                        failure_msg,
                        write_failure_file=True,
                        create_failure_dir=False,
                        overwrite_failure_file=False,
                    )
                    _touch_remote_task_heartbeat(task)
                error_info = {
                    "error": failure_msg,
                    "traceback": traceback.format_exc(),
                }

    if error_info is None:
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=abs_download_dir,
            stage="write_remote_success_signal",
        )
        echo_success = (
            f"cd {shlex.quote(remote_work_dir)} && "
            f"printf '%s\\n' {shlex.quote('All notebooks executed successfully.')} > success.txt"
        )
        _ssh_run(remote_login, echo_success)
        if not scheduler_managed:
            _mark_task_success(task)

    _signal_remote_task_progress(
        task,
        scheduler_managed=scheduler_managed,
        task_dir=abs_download_dir,
        stage="pull_remote_results_start",
    )
    try:
        _pull_remote_to_local(remote_IP, remote_work_dir, abs_download_dir)
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=abs_download_dir,
            stage="pull_remote_results_done",
        )
    except Exception as e:
        if error_info is None:
            error_info = {
                "error": f"Rsync pull failed: {str(e)}",
                "traceback": traceback.format_exc(),
            }

    if (
        error_info is None
        and (scheduler_managed or getattr(task, "status", None) == "success")
        and after_success_local is not None
    ):
        after_success_local()
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=abs_download_dir,
            stage="after_success_local_done",
        )

    if scheduler_managed:
        if error_info is None:
            _write_worker_result_signal(
                abs_download_dir,
                status="success",
                message="Remote worker completed successfully.",
            )
        else:
            _write_worker_result_signal(
                abs_download_dir,
                status="failed",
                message=str(error_info.get("error") or "Remote worker failed."),
                extra={"traceback": str(error_info.get("traceback") or "")},
            )

    return error_info


def _run_remote_zip_package_steps(
    remote_login: str,
    remote_work_dir: str,
    task: ComputeTask,
    packages: Sequence[Tuple[str, Sequence[str]]],
    *,
    scheduler_managed: bool = False,
) -> None:

    task_dir = _task_folder_path(task)
    for zip_name, include_patterns in packages:
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=task_dir,
            stage="remote_zip_start",
            detail=zip_name,
        )
        include_expr = " ".join(shlex.quote(pattern) for pattern in include_patterns)
        zip_cmd = (
            f"cd {shlex.quote(remote_work_dir)} && "
            f"zip -q -r {shlex.quote(zip_name)} . -i {include_expr}"
        )
        try:
            _ssh_run(remote_login, zip_cmd)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"zip {zip_name} failed: {e.stderr or e.stdout or str(e)}"
            ) from e
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=task_dir,
            stage="remote_zip_done",
            detail=zip_name,
        )



def run_task_immediately_remote(
    task_func,
    source_dir,
    download_dir,
    task,
    remote_target,
    remote_IP=remote_IP,
):

    return _dispatch_remote_task(
        task_func=task_func,
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
    )


def check_and_execute_task_remote(
    task_func,
    source_dir,
    download_dir,
    task,
    remote_target,
    remote_IP=remote_IP,
    MAX_RUNNING_LENGTH=REMOTE_MAX_RUNNING_LENGTH,
):

    return _dispatch_remote_task(
        task_func=task_func,
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
    )


def _server_supports_task(server: Dict[str, Any], task: ComputeTask) -> bool:

    required_capability = get_required_capability(task.task_type)
    return bool(required_capability and required_capability in server.get("capabilities", []))


def _read_failure_file_message(task: ComputeTask, default_message: str) -> str:

    failure_path = os.path.join(_task_folder_path(task), "failure.txt")
    try:
        if os.path.exists(failure_path):
            content = Path(failure_path).read_text(encoding="utf-8").strip()
            if content:
                return content
    except Exception:
        logger.exception("Failed to read failure.txt for task_id=%s", task.task_id)
    return default_message


def _finalize_pending_remote_task(task: ComputeTask, *, kill_stuck_pids: bool = True) -> Optional[Dict[str, Any]]:

    _sync_task_heartbeat_from_worker_signal(task)
    task.refresh_from_db()

    has_success, has_failure = _task_has_terminal_signal_files(task)
    if has_failure:
        reason = _read_failure_file_message(task, "Remote task directory contains failure.txt.")
        mark_task_failed(
            task,
            reason,
            write_failure_file=False,
            create_failure_dir=False,
            overwrite_failure_file=False,
        )
        return {"task_id": task.task_id, "action": "failed_from_failure_signal", "reason": reason}

    if has_success:
        if task.task_type == "Markov_GDyNet_analysis":
            _finalize_markov_task_from_local_signals(task, _task_folder_path(task))
        else:
            _mark_task_success(task)
        return {"task_id": task.task_id, "action": "success_from_success_signal", "reason": "success.txt"}

    if getattr(task, "pid", None) and not _task_pid_is_alive(task):
        mark_task_failed(
            task,
            PENDING_REMOTE_PROCESS_DISAPPEARED_MESSAGE,
            write_failure_file=True,
            create_failure_dir=False,
            overwrite_failure_file=False,
        )
        return {
            "task_id": task.task_id,
            "action": "failed_process_disappeared",
            "reason": PENDING_REMOTE_PROCESS_DISAPPEARED_MESSAGE,
        }

    if _is_remote_task_heartbeat_stale(task):
        kill_summary = _kill_task_pid_tree(task) if kill_stuck_pids else None
        mark_task_failed(
            task,
            PENDING_REMOTE_HEARTBEAT_TIMEOUT_MESSAGE,
            write_failure_file=True,
            create_failure_dir=False,
            overwrite_failure_file=False,
        )
        return {
            "task_id": task.task_id,
            "action": "failed_heartbeat_timeout",
            "reason": PENDING_REMOTE_HEARTBEAT_TIMEOUT_MESSAGE,
            "kill_summary": kill_summary,
        }

    return None


def _start_remote_task_worker(task: ComputeTask, selected_server: Dict[str, Any]) -> subprocess.Popen:

    log_path = os.path.join(_task_folder_path(task), "remote_worker.log")
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        os.path.join(settings.BASE_DIR, "manage.py"),
        "run_remote_task_worker",
        str(task.task_id),
    ]
    log_file = open(log_path, "a", encoding="utf-8")
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=settings.BASE_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        log_file.close()
    _write_worker_started_signal(
        _task_folder_path(task),
        pid=proc.pid,
        server_name=selected_server["server_name"],
        remote_target=_build_remote_target_path(
            selected_server,
            _load_remote_dispatch_request(task)["remote_target_subpath"],
        ),
    )
    return proc


def _dispatch_one_remote_task_from_queue() -> Optional[Dict[str, Any]]:

    servers = [server for server in _load_remote_server_pool() if server.get("enabled", True)]
    if not servers:
        return None

    pending_counts = {
        item["server_name"]: item["count"]
        for item in ComputeTask.objects.filter(
            remote_type="remote",
            status="pending",
            server_name__isnull=False,
        )
        .values("server_name")
        .annotate(count=Count("id"))
    }
    available_servers = [
        server
        for server in servers
        if pending_counts.get(server["server_name"], 0) < int(server["task_limit"])
    ]
    if not available_servers:
        return None

    queued_tasks = list(
        ComputeTask.objects.filter(remote_type="remote", status="queuing").order_by("created_at", "id")
    )
    for task in queued_tasks:
        if is_deprecated_remote_task_type(task.task_type):
            reason = f"Remote task type {task.task_type} has been deprecated."
            mark_task_failed(task, reason, write_failure_file=True, create_failure_dir=False)
            return {"task_id": task.task_id, "action": "failed_deprecated_task_type", "reason": reason}

        try:
            request_payload = _load_remote_dispatch_request(task)
        except Exception as exc:
            reason = f"Remote dispatch request is invalid: {type(exc).__name__}: {exc}"
            mark_task_failed(task, reason, write_failure_file=True, create_failure_dir=False)
            return {"task_id": task.task_id, "action": "failed_invalid_dispatch_request", "reason": reason}

        matching_servers = [server for server in available_servers if _server_supports_task(server, task)]
        if not matching_servers:
            continue
        matching_servers.sort(
            key=lambda server: (
                pending_counts.get(server["server_name"], 0) / max(int(server["task_limit"]), 1),
                server["order"],
            )
        )
        selected_server = matching_servers[0]
        remote_target = _build_remote_target_path(
            selected_server,
            str(request_payload["remote_target_subpath"]),
        )

        with transaction.atomic():
            locked_task = ComputeTask.objects.select_for_update().get(pk=task.pk)
            if locked_task.status != "queuing" or locked_task.remote_type != "remote":
                return None
            locked_task.status = "pending"
            locked_task.server_name = selected_server["server_name"]
            locked_task.last_heartbeat_at = timezone.now()
            locked_task.pid = None
            locked_task.save(update_fields=["status", "server_name", "last_heartbeat_at", "pid"])
            task = locked_task

        try:
            proc = _start_remote_task_worker(task, selected_server)
            task.pid = proc.pid
            task.save(update_fields=["pid"])
            return {
                "task_id": task.task_id,
                "action": "dispatched",
                "server_name": selected_server["server_name"],
                "pid": proc.pid,
                "remote_target": remote_target,
            }
        except Exception as exc:
            reason = f"Failed to start remote task worker: {type(exc).__name__}: {exc}"
            mark_task_failed(task, reason, write_failure_file=True, create_failure_dir=False)
            return {"task_id": task.task_id, "action": "failed_worker_start", "reason": reason}

    return None


def run_remote_queue_scheduler_loop(*, once: bool = False, sleep_seconds: int = 5) -> None:

    lock_dir = os.path.join(settings.BASE_DIR, "tmp")
    os.makedirs(lock_dir, exist_ok=True)
    lock_path = os.path.join(lock_dir, REMOTE_QUEUE_SCHEDULER_LOCK_FILENAME)
    with open(lock_path, "w", encoding="utf-8") as lock_handle:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another run_remote_queue_scheduler instance is already running.") from exc

        while True:
            for task in list(
                ComputeTask.objects.filter(remote_type="remote", status="pending").order_by("created_at", "id")
            ):
                _finalize_pending_remote_task(task)

            while True:
                dispatched = _dispatch_one_remote_task_from_queue()
                if dispatched is None:
                    break
                logger.info("Remote queue scheduler action: %s", dispatched)

            if once:
                break
            time.sleep(max(1, int(sleep_seconds)))


def run_remote_task_worker(task_id: str) -> None:

    task = ComputeTask.objects.get(task_id=task_id)
    task_dir = _task_folder_path(task)
    try:
        request_payload = _load_remote_dispatch_request(task)
        selected_server = _get_remote_server_by_name(str(task.server_name or ""))
        if selected_server is None:
            raise RuntimeError(f"Task has no valid server_name binding: {task.server_name}")
        remote_target = _build_remote_target_path(
            selected_server,
            str(request_payload["remote_target_subpath"]),
        )
        module_name, func_name = str(request_payload["func_path"]).rsplit(".", 1)
        task_func = getattr(importlib.import_module(module_name), func_name)
        _write_worker_started_signal(
            task_dir,
            pid=os.getpid(),
            server_name=selected_server["server_name"],
            remote_target=remote_target,
        )
        _write_worker_heartbeat_signal(task_dir, stage="worker_start")
        task_func(
            str(request_payload["source_dir"]),
            str(request_payload["download_dir"]),
            task,
            remote_target,
            remote_IP=selected_server["IP"],
            scheduler_managed=True,
        )
        _write_worker_heartbeat_signal(task_dir, stage="worker_exit")
        if os.path.exists(os.path.join(task_dir, "failure.txt")):
            message = _read_failure_file_message(task, "Remote worker finished with failure.txt.")
            _write_worker_result_signal(task_dir, status="failed", message=message)
        elif os.path.exists(os.path.join(task_dir, "success.txt")):
            _write_worker_result_signal(
                task_dir,
                status="success",
                message="Remote worker finished with success.txt.",
            )
        else:
            message = "Remote worker finished without success.txt or failure.txt."
            _write_local_text_signal(os.path.join(task_dir, "failure.txt"), message)
            _write_worker_result_signal(task_dir, status="failed", message=message)
    except Exception as exc:
        message = f"Remote worker error: {type(exc).__name__}: {exc}"
        try:
            _write_local_text_signal(os.path.join(task_dir, "failure.txt"), message)
            _write_worker_result_signal(
                task_dir,
                status="failed",
                message=message,
                extra={"traceback": traceback.format_exc()},
            )
        except Exception:
            logger.exception("Failed to write worker failure signal for task_id=%s", task_id)
        raise

def _ssh_run(
    remote_login: str,
    cmd: str,
    timeout=None,
    *,
    ssh_port: Optional[int] = None,
    server_info_file_path: Optional[str] = None,
):
    
    script = "set -euo pipefail\n"  
    script += (cmd.rstrip() + "\n") 
    script += "exit\n"              

    
    ssh_cmd = _build_ssh_command(
        remote_login,
        batch_mode=True,
        allocate_tty=True,
        ssh_port=ssh_port,
        server_info_file_path=server_info_file_path,
    )

    
    return subprocess.run(
        ssh_cmd,
        input=script,               
        text=True,                  
        capture_output=True,        
        check=True,                 
        timeout=timeout             
    )


def _ssh_run_batch(
    remote_login: str,
    cmd: str,
    timeout=None,
    *,
    ssh_port: Optional[int] = None,
    server_info_file_path: Optional[str] = None,
):

    ssh_cmd = _build_ssh_command(
        remote_login,
        batch_mode=True,
        allocate_tty=False,
        ssh_port=ssh_port,
        server_info_file_path=server_info_file_path,
    )
    bash_cmd = f"set -euo pipefail; {cmd}"
    return subprocess.run(
        ssh_cmd + ["bash", "-lc", bash_cmd],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _ssh_run_command(
    remote_login: str,
    remote_command: Sequence[str],
    timeout=None,
    *,
    ssh_port: Optional[int] = None,
    server_info_file_path: Optional[str] = None,
):

    ssh_cmd = _build_ssh_command(
        remote_login,
        batch_mode=True,
        allocate_tty=False,
        ssh_port=ssh_port,
        server_info_file_path=server_info_file_path,
    )
    return subprocess.run(
        ssh_cmd + [shlex.join(list(remote_command))],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def copy_unique_folder(download_dir: str,
                       remote_target: str, 
                       remote_IP=remote_IP):

    
    abs_download_dir = os.path.abspath(download_dir)  

    
    if not os.path.exists(abs_download_dir):          
        os.makedirs(abs_download_dir)                 

    
    remote_login, _, _ = _resolve_remote_connection_info(remote_IP)
    remote_ip, ssh_transport = _build_rsync_remote_prefix(remote_IP)

    
    
    mkdir_cmd = _build_ssh_command(
        remote_login,
        batch_mode=True,
        allocate_tty=False,
    ) + [f"mkdir -p {shlex.quote(remote_target)}"]

    
    try:
        subprocess.run(mkdir_cmd, check=True)         
    except subprocess.CalledProcessError as e:        
        print(f"❌ 远程目录创建失败：{e}")             
        return                                        

    
    
    rsync_cmd = [
        "rsync", "-avz",                              
        "-e", ssh_transport,                          
        abs_download_dir,                             
        remote_ip + remote_target                     
    ]

    
    try:
        subprocess.run(rsync_cmd, check=True)         
        print(f"✅ Successfully copied {abs_download_dir} to {remote_login}:{remote_target}")  
    except subprocess.CalledProcessError as e:        
        print(f"❌ rsync failed: {e}")                


def run_draw_ESP_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    def _after_remote_success(remote_login: str, remote_work_dir: str, task: ComputeTask) -> None:
        _run_remote_zip_package_steps(
            remote_login,
            remote_work_dir,
            task,
            packages=[
                ("original_draw_file.zip", ("*.fchk", "*.cub", "*.vmd")),
                ("ESP_fig_file.zip", ("*.tga",)),
            ],
            scheduler_managed=scheduler_managed,
        )

    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=["auto_draw_ESP.ipynb"],
        after_remote_success=_after_remote_success,
        scheduler_managed=scheduler_managed,
    )



def run_draw_ESP_notebook_tasks_gbw_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    def _after_remote_success(remote_login: str, remote_work_dir: str, task: ComputeTask) -> None:
        _run_remote_zip_package_steps(
            remote_login,
            remote_work_dir,
            task,
            packages=[
                ("original_draw_file.zip", ("*.fchk", "*.cub", "*.vmd")),
                ("ESP_fig_file.zip", ("*.tga",)),
            ],
            scheduler_managed=scheduler_managed,
        )

    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=["auto_draw_ESP_gbw.ipynb"],
        after_remote_success=_after_remote_success,
        scheduler_managed=scheduler_managed,
    )


def run_draw_HOMO_LUMO_orb_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    def _after_remote_success(remote_login, remote_work_dir, task):

        _run_remote_zip_package_steps(
            remote_login=remote_login,
            remote_work_dir=remote_work_dir,
            task=task,
            packages=[
                ("original_draw_file.zip", ("*.fchk", "*.cub", "*.vmd", "*.molden")),
                ("HOMO_LUMO_orb_fig_file.zip", ("*.tga",)),
            ],
            scheduler_managed=scheduler_managed,
        )

    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=["draw_HOMO_LUMO_orb.ipynb"],
        after_remote_success=_after_remote_success,
        scheduler_managed=scheduler_managed,
    )



def run_NCI_SCF_analysis_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    def _after_remote_success(remote_login, remote_work_dir, task):

        _run_remote_zip_package_steps(
            remote_login=remote_login,
            remote_work_dir=remote_work_dir,
            task=task,
            packages=[
                ("original_draw_file.zip", ("*.fchk", "*.cub", "*.vmd", "*.molden", "*.csv")),
                ("nci_fig_file.zip", ("*.tga",)),
            ],
            scheduler_managed=scheduler_managed,
        )

    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=["NCI_analysis.ipynb"],
        after_remote_success=_after_remote_success,
        scheduler_managed=scheduler_managed,
    )




def run_NCI_promolecular_analysis_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    def _after_remote_success(remote_login, remote_work_dir, task):

        _run_remote_zip_package_steps(
            remote_login=remote_login,
            remote_work_dir=remote_work_dir,
            task=task,
            packages=[
                (
                    "original_draw_file.zip",
                    ("*.fchk", "*.cub", "*.vmd", "*.molden", "*.csv", "*.pdb", "*.xyz", "*.mol", "*.mol2"),
                ),
                ("nci_fig_file.zip", ("*.tga", "*.png")),
            ],
            scheduler_managed=scheduler_managed,
        )

    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=["NCI_analysis_promolecular.ipynb"],
        after_remote_success=_after_remote_success,
        scheduler_managed=scheduler_managed,
    )
    

def run_ORCA_manual_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    notebooks_to_run = [
        'ORCA_Gas_2_opt+freq_calculation.ipynb',
        'ORCA_Gas_3_opt+freq_imaginary_frequencies.ipynb',
        'ORCA_Gas_4_energy_calculation.ipynb',
        'ORCA_Gas_5_Extracting_energy_and_free_energy_corrections.ipynb',
    ]
    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )


def run_ORCA_manual_notebook_tasks_remote_energy(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    notebooks_to_run = [
        'ORCA_Gas_1_energy_calculation.ipynb',
        'ORCA_Gas_2_Extracting_energy.ipynb',
    ]
    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )


def run_Gaussian_binding_energy_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    notebooks_to_run = [
        'Gas_component_1_generate_Gaussian_inputfile.ipynb',
        'Gas_component_2_opt+freq_calculation.ipynb',
        'Gas_component_3_opt+freq_failure_correction.ipynb',
        'Gas_component_4_opt+freq_imaginary_frequencies.ipynb',
        'Gas_component_5_energy_calculation.ipynb',
        'Gas_component_6_energy_failure_correction.ipynb',
        'Gas_component_7_Extracting_energy_and_free_energy_corrections.ipynb',
        'Gas_dimer_1_generate_Gaussian_inputfile.ipynb',
        'Gas_dimer_2_opt+freq_calculation.ipynb',
        'Gas_dimer_3_opt+freq_failure_correction.ipynb',
        'Gas_dimer_4_opt+freq_imaginary_frequencies.ipynb',
        'Gas_dimer_5_energy_calculation.ipynb',
        'Gas_dimer_6_energy_failure_correction.ipynb',
        'Gas_dimer_7_Extracting_energy_and_free_energy_corrections.ipynb',
        'Data_processing .ipynb',
    ]
    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )



def run_Gaussian_single_point_energy_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    notebooks_to_run = [
        'Gas_component_1_generate_Gaussian_inputfile.ipynb',
        'Gas_component_2_opt+freq_calculation.ipynb',
        'Gas_component_3_opt+freq_failure_correction.ipynb',
        'Gas_component_4_opt+freq_imaginary_frequencies.ipynb',
        'Gas_component_5_energy_calculation.ipynb',
        'Gas_component_6_energy_failure_correction.ipynb',
        'Gas_component_7_Extracting_energy_and_free_energy_corrections.ipynb',
    ]
    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )



def run_Gromacs_MD_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    notebooks_to_run = [
        '1_Polymer_RESP_repeat_unit.ipynb',
        '2_Polymer_chg_and_Polymer_creation_ Linear_polymer.ipynb',
        '3_create_Polymer_itp_top.ipynb',
        '4_generate_Gaussian_inputfile.ipynb',
        '5_opt+freq_calculation.ipynb',
        '6_opt+freq_failure_correction.ipynb',
        '7_opt+freq_imaginary_frequencies.ipynb',
        '8_MD_process.ipynb',
        '9_post_analysis.ipynb',
        '11_component_energy_calculation.ipynb',
        '12_calculate_solvent_cage_escape_energy.ipynb',
        '13_coordination_environment_distribution.ipynb'
    ]
    def _after_success_local() -> None:

        try:
            build_md_preview_manifest(download_dir=download_dir, force_rebuild=True)
        except Exception as exc:
            logger.warning("Failed to build MD query previews for remote task %s: %s", download_dir, exc)

    _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=notebooks_to_run,
        after_success_local=_after_success_local,
        scheduler_managed=scheduler_managed,
    )



def _load_markov_request(download_dir: str) -> Dict[str, Any]:

    request_path = os.path.join(download_dir, "markov_request.json")
    with open(request_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("markov_request.json must contain a JSON object.")
    return payload


def _resolve_markov_source_md_dir(request_payload: Dict[str, Any]) -> str:

    raw_path = str(request_payload.get("source_md_dir") or "").strip()
    if raw_path and os.path.isdir(raw_path):
        return raw_path
    marker = "/media/"
    normalized = raw_path.replace("\\", "/")
    if marker in normalized:
        relative = normalized.split(marker, 1)[1].lstrip("/")
        candidate = os.path.join(settings.MEDIA_ROOT, relative)
        if os.path.isdir(candidate):
            return candidate
    raise FileNotFoundError(f"Source MD directory does not exist: {raw_path}")


def _copy_markov_input_file(src: str, dst: str, label: str) -> None:

    if not os.path.isfile(src):
        raise FileNotFoundError(f"Missing required Markov input file {label}: {src}")
    shutil.copy2(src, dst)


def _prepare_markov_work_dir(
    download_dir: str,
    request_payload: Dict[str, Any],
    *,
    task: ComputeTask,
    remote_login: str,
    remote_work_dir: str,
    gdynet_package_dir: str,
) -> None:

    source_md_dir = _resolve_markov_source_md_dir(request_payload)
    input_md_dir = os.path.join(download_dir, "input_md")
    os.makedirs(input_md_dir, exist_ok=True)
    _copy_markov_input_file(os.path.join(source_md_dir, "System.xlsx"), os.path.join(input_md_dir, "System.xlsx"), "System.xlsx")
    _copy_markov_input_file(os.path.join(source_md_dir, "prod_NVT.tpr"), os.path.join(input_md_dir, "prod_NVT.tpr"), "prod_NVT.tpr")
    _copy_markov_input_file(os.path.join(source_md_dir, "prod_NVT.xtc"), os.path.join(input_md_dir, "prod_NVT.xtc"), "prod_NVT.xtc")

    rdf_candidates = [
        os.path.join(source_md_dir, "rdf_radius.json"),
        os.path.join(source_md_dir, "all_results", "rdf_radius.json"),
    ]
    rdf_source = next((candidate for candidate in rdf_candidates if os.path.isfile(candidate)), "")
    if not rdf_source:
        raise FileNotFoundError("Missing rdf_radius.json in source MD directory or all_results/.")
    _copy_markov_input_file(rdf_source, os.path.join(input_md_dir, "rdf_radius.json"), "rdf_radius.json")

    request_payload["resolved_source_md_dir"] = source_md_dir
    with open(os.path.join(download_dir, "markov_request_resolved.json"), "w", encoding="utf-8") as handle:
        json.dump(request_payload, handle, ensure_ascii=False, indent=2)

    remote_input_md_dir = posixpath.join(remote_work_dir, "input_md")
    remote_output_dir = posixpath.join(remote_work_dir, "markov_results")
    expected_artifacts = {
        "success_txt": posixpath.join(remote_work_dir, "success.txt"),
        "failure_txt": posixpath.join(remote_work_dir, "failure.txt"),
        "summary_xlsx": posixpath.join(remote_work_dir, "markov_summary.xlsx"),
        "zip_path": posixpath.join(remote_work_dir, "all_results.zip"),
    }
    context_payload = {
        "cemp_task_id": task.task_id,
        "source_md_task_id": request_payload.get("source_md_task_id", ""),
        "source_md_task_type": request_payload.get("source_md_task_type", ""),
        "source_md_status": request_payload.get("source_md_status", ""),
        "server_name": task.server_name or "",
        "remote_login": remote_login,
        "remote_work_dir": remote_work_dir,
        "gdynet_package_dir": gdynet_package_dir,
        "md_input_dir": remote_input_md_dir,
        "output_dir": remote_output_dir,
        "expected_artifacts": expected_artifacts,
        "notes": [
            "CEMP only prepared inputs and scheduling context.",
            "Agent/Codex must inspect System.xlsx and decide GDyNet workflow parameters.",
            "Do not write production outputs outside remote_work_dir.",
        ],
    }
    with open(os.path.join(download_dir, "markov_context.json"), "w", encoding="utf-8") as handle:
        json.dump(context_payload, handle, ensure_ascii=False, indent=2)


def _http_json_request(url: str, payload: Optional[Dict[str, Any]], method: str = "POST", timeout: int = 60) -> Dict[str, Any]:

    headers = {"Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Agent controller HTTP {exc.code}: {detail}") from exc
    if not response_body:
        return {}
    parsed = json.loads(response_body)
    if not isinstance(parsed, dict):
        raise ValueError(f"Agent controller response must be a JSON object: {response_body[:500]}")
    return parsed


def _start_markov_controller_job(remote_login: str, task: ComputeTask, remote_work_dir: str, gdynet_package_dir: str) -> str:

    controller_url = str(getattr(settings, "CEMP_AGENT_MARKOV_CONTROLLER_URL", "") or "").strip().rstrip("/")
    if not controller_url:
        raise RuntimeError("CEMP_AGENT_MARKOV_CONTROLLER_URL is not configured.")

    payload = {
        "cemp_task_id": task.task_id,
        "server_name": task.server_name or "",
        "remote_login": remote_login,
        "remote_work_dir": remote_work_dir,
        "gdynet_package_dir": gdynet_package_dir,
        "md_input_dir": posixpath.join(remote_work_dir, "input_md"),
        "output_dir": posixpath.join(remote_work_dir, "markov_results"),
        "markov_context_path": posixpath.join(remote_work_dir, "markov_context.json"),
        "expected_artifacts": {
            "success_txt": posixpath.join(remote_work_dir, "success.txt"),
            "failure_txt": posixpath.join(remote_work_dir, "failure.txt"),
            "summary_xlsx": posixpath.join(remote_work_dir, "markov_summary.xlsx"),
            "zip_path": posixpath.join(remote_work_dir, "all_results.zip"),
            "representative_summary_csv": posixpath.join(
                remote_work_dir,
                "markov_results",
                "analysis",
                "representatives",
                "representative_summary.csv",
            ),
        },
    }
    response = _http_json_request(controller_url, payload, method="POST", timeout=60)
    job_id = str(response.get("job_id") or "").strip()
    if not job_id:
        raise RuntimeError(f"Agent controller did not return job_id: {response}")
    return job_id


def _poll_markov_controller_job(job_id: str) -> Dict[str, Any]:

    controller_url = str(getattr(settings, "CEMP_AGENT_MARKOV_CONTROLLER_URL", "") or "").strip().rstrip("/")
    poll_url = f"{controller_url}/{job_id}"
    poll_interval = int(getattr(settings, "MARKOV_AGENT_POLL_INTERVAL_SECONDS", 20))
    timeout_seconds = int(getattr(settings, "MARKOV_AGENT_TIMEOUT_SECONDS", 7 * 24 * 60 * 60))
    started_at = time.monotonic()
    while True:
        response = _http_json_request(poll_url, None, method="GET", timeout=60)
        current_status = str(response.get("status") or "").lower()
        if current_status in {"completed", "failed"}:
            return response
        if time.monotonic() - started_at > timeout_seconds:
            raise TimeoutError(f"Agent Markov controller job timed out: {job_id}")
        time.sleep(max(1, poll_interval))


def _write_remote_markov_failure(remote_login: str, remote_work_dir: str, message: str) -> None:

    failure_cmd = (
        f"mkdir -p {shlex.quote(remote_work_dir)} && "
        f"cd {shlex.quote(remote_work_dir)} && "
        f"printf '%s\\n' {shlex.quote(message)} > failure.txt"
    )
    try:
        _ssh_run(remote_login, failure_cmd)
    except Exception:
        logger.exception("Failed to write remote Markov failure.txt for %s", remote_work_dir)


def _finalize_markov_task_from_local_signals(task: ComputeTask, download_dir: str) -> None:

    representative_summary_path = os.path.join(
        download_dir,
        "markov_results",
        "analysis",
        "representatives",
        "representative_summary.csv",
    )

    if os.path.exists(os.path.join(download_dir, "success.txt")):
        if not os.path.exists(representative_summary_path):
            mark_task_failed(
                task,
                "Markov task finished with success.txt but missing required artifact: "
                "markov_results/analysis/representatives/representative_summary.csv",
                write_failure_file=False,
                create_failure_dir=False,
                overwrite_failure_file=False,
            )
            return
        _mark_task_success(task)
        return

    failure_message = "Markov task finished without success.txt."
    failure_file = os.path.join(download_dir, "failure.txt")
    if os.path.exists(failure_file):
        try:
            failure_message = Path(failure_file).read_text(encoding="utf-8").strip() or failure_message
        except Exception:
            logger.exception("Failed to read local Markov failure.txt: %s", failure_file)

    mark_task_failed(
        task,
        failure_message,
        write_failure_file=False,
        create_failure_dir=False,
        overwrite_failure_file=False,
    )


def run_markov_gdynet_analysis_remote(source_dir, download_dir, task, remote_target, remote_IP=remote_IP, scheduler_managed: bool = False):

    abs_download_dir = os.path.abspath(download_dir)
    remote_work_dir = posixpath.join(remote_target.rstrip("/"), os.path.basename(abs_download_dir))
    remote_login = remote_IP[:-1] if remote_IP.endswith(":") else remote_IP
    gdynet_package_dir = str(source_dir).rstrip("/")
    error_message = ""
    controller_result: Dict[str, Any] = {}

    try:
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=abs_download_dir,
            stage="markov_prepare_start",
        )
        request_payload = _load_markov_request(download_dir)
        _prepare_markov_work_dir(
            download_dir,
            request_payload,
            task=task,
            remote_login=remote_login,
            remote_work_dir=remote_work_dir,
            gdynet_package_dir=gdynet_package_dir,
        )
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=abs_download_dir,
            stage="markov_prepare_done",
        )
        copy_unique_folder(download_dir, remote_target=remote_target, remote_IP=remote_IP)
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=abs_download_dir,
            stage="markov_copy_remote_input",
        )
        _ssh_run(remote_login, f"test -d {shlex.quote(remote_work_dir)}")
        _ssh_run(remote_login, f"test -d {shlex.quote(gdynet_package_dir)}")
        _ssh_run(remote_login, f"test -f {shlex.quote(posixpath.join(remote_work_dir, 'markov_context.json'))}")
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=abs_download_dir,
            stage="markov_remote_context_ready",
        )
        job_id = _start_markov_controller_job(remote_login, task, remote_work_dir, gdynet_package_dir)
        with open(os.path.join(download_dir, "markov_controller_job.json"), "w", encoding="utf-8") as handle:
            json.dump({"job_id": job_id, "server_name": task.server_name, "remote_work_dir": remote_work_dir}, handle, ensure_ascii=False, indent=2)
        controller_result = _poll_markov_controller_job(job_id)
        _signal_remote_task_progress(
            task,
            scheduler_managed=scheduler_managed,
            task_dir=abs_download_dir,
            stage="markov_controller_completed",
        )
        if str(controller_result.get("status") or "").lower() == "failed":
            error_message = str(controller_result.get("error") or controller_result.get("message") or "Agent Markov controller failed.")
            _write_remote_markov_failure(remote_login, remote_work_dir, error_message)
    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"
        _write_remote_markov_failure(remote_login, remote_work_dir, error_message)
    finally:
        try:
            _signal_remote_task_progress(
                task,
                scheduler_managed=scheduler_managed,
                task_dir=abs_download_dir,
                stage="markov_pull_remote_results_start",
            )
            _pull_remote_to_local(remote_IP, remote_work_dir, abs_download_dir)
            _signal_remote_task_progress(
                task,
                scheduler_managed=scheduler_managed,
                task_dir=abs_download_dir,
                stage="markov_pull_remote_results_done",
            )
        except Exception as pull_exc:
            error_message = error_message or f"Rsync pull failed: {pull_exc}"
        if controller_result:
            with open(os.path.join(abs_download_dir, "markov_controller_result.json"), "w", encoding="utf-8") as handle:
                json.dump(controller_result, handle, ensure_ascii=False, indent=2)
        if error_message and not os.path.exists(os.path.join(abs_download_dir, "failure.txt")):
            with open(os.path.join(abs_download_dir, "failure.txt"), "w", encoding="utf-8") as handle:
                handle.write(error_message)
        if scheduler_managed:
            if error_message:
                _write_worker_result_signal(
                    abs_download_dir,
                    status="failed",
                    message=error_message,
                )
            else:
                _write_worker_result_signal(
                    abs_download_dir,
                    status="success",
                    message="Markov worker finished and handed results back to scheduler.",
                )
        else:
            _touch_remote_task_heartbeat(task)
            _finalize_markov_task_from_local_signals(task, abs_download_dir)



def run_ORCA_single_point_energy_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    notebooks_to_run = [
        'ORCA_Gas_1_generate_ORCA_inputfile.ipynb',
        'ORCA_Gas_2_opt+freq_calculation.ipynb',
        'ORCA_Gas_3_opt+freq_imaginary_frequencies.ipynb',
        'ORCA_Gas_4_energy_calculation.ipynb',
        'ORCA_Gas_5_Extracting_energy_and_free_energy_corrections.ipynb',
    ]
    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )


def run_ORCA_binding_energy_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    notebooks_to_run = [
        'ORCA_Gas_component_1_generate_ORCA_inputfile.ipynb',
        'ORCA_Gas_component_2_opt+freq_calculation.ipynb',
        'ORCA_Gas_component_3_opt+freq_imaginary_frequencies.ipynb',
        'ORCA_Gas_component_4_energy_calculation.ipynb',
        'ORCA_Gas_component_5_Extracting_energy_and_free_energy_corrections.ipynb',
        'ORCA_Gas_dimer_1_generate_ORCA_inputfile.ipynb',
        'ORCA_Gas_dimer_2_opt+freq_calculation.ipynb',
        'ORCA_Gas_dimer_3_opt+freq_imaginary_frequencies.ipynb',
        'ORCA_Gas_dimer_4_energy_calculation.ipynb',
        'ORCA_Gas_dimer_5_Extracting_energy_and_free_energy_corrections.ipynb',
    ]
    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )



def run_ORCA_ox_red_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    notebooks_to_run = [
        'ORCA_ox_red_1_generate_ORCA_inputfile.ipynb',
        'ORCA_ox_red_2_opt+freq_calculation.ipynb',
        'ORCA_ox_red_3_opt+freq_imaginary_frequencies.ipynb',
        'ORCA_ox_red_4_energy_calculation.ipynb',
        'ORCA_ox_red_5_Extracting_energy_and_free_energy_corrections.ipynb',
    ]
    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )



def run_Gaussian_ox_red_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP = remote_IP, scheduler_managed: bool = False):
    notebooks_to_run = [
        'ox_red_1_generate_Gaussian_inputfile.ipynb',
        'ox_red_2_opt+freq_calculation.ipynb',
        'ox_red_3_opt+freq_failure_correction.ipynb',
        'ox_red_4_opt+freq_imaginary_frequencies.ipynb',
        'ox_red_5_energy_calculation.ipynb',
        'ox_red_6_energy_failure_correction.ipynb',
        'ox_red_7_Extracting_energy_and_free_energy_corrections.ipynb',
    ]
    return _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )


def _run_remote_gaussian_notebook_sequence(source_dir, download_dir, task, remote_target, remote_IP, notebooks_to_run, *, scheduler_managed: bool = False):

    _run_remote_notebook_sequence(
        source_dir=source_dir,
        download_dir=download_dir,
        task=task,
        remote_target=remote_target,
        remote_IP=remote_IP,
        notebooks_to_run=notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )


def run_Gaussian_pka_pkb_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP=remote_IP, scheduler_managed: bool = False):

    notebooks_to_run = [
        'pkb_DFT_1_generate_Gaussian_inputfile.ipynb',
        'pkb_DFT_2_opt+freq_calculation.ipynb',
        'pkb_DFT_3_opt+freq_failure_correction.ipynb',
        'pkb_DFT_4_opt+freq_imaginary_frequencies.ipynb',
        'pkb_DFT_5_energy_calculation.ipynb',
        'pkb_DFT_6_energy_failure_correction.ipynb',
        'pkb_DFT_7_Extracting_energy_and_free_energy_corrections.ipynb',
    ]
    _run_remote_gaussian_notebook_sequence(
        source_dir,
        download_dir,
        task,
        remote_target,
        remote_IP,
        notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )


def run_Gaussian_reaction_thermo_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP=remote_IP, scheduler_managed: bool = False):

    notebooks_to_run = [
        'reaction_thermo_1_generate_Gaussian_inputfile.ipynb',
        'reaction_thermo_2_opt+freq_calculation.ipynb',
        'reaction_thermo_3_opt+freq_failure_correction.ipynb',
        'reaction_thermo_4_opt+freq_imaginary_frequencies.ipynb',
        'reaction_thermo_5_energy_calculation.ipynb',
        'reaction_thermo_6_Extracting_energy_and_free_energy_corrections.ipynb',
    ]
    _run_remote_gaussian_notebook_sequence(
        source_dir,
        download_dir,
        task,
        remote_target,
        remote_IP,
        notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )


def run_Gaussian_global_reaction_properties_notebook_tasks_remote(source_dir, download_dir, task, remote_target, remote_IP=remote_IP, scheduler_managed: bool = False):

    notebooks_to_run = [
        'reaction_1_generate_Gaussian_inputfile.ipynb',
        'reaction_2_opt+freq_calculation.ipynb',
        'reaction_3_opt+freq_failure_correction.ipynb',
        'reaction_4_opt+freq_imaginary_frequencies.ipynb',
        'reaction_5_energy_calculation.ipynb',
        'reaction_6_Extracting_energy_and_free_energy_corrections.ipynb',
    ]
    _run_remote_gaussian_notebook_sequence(
        source_dir,
        download_dir,
        task,
        remote_target,
        remote_IP,
        notebooks_to_run,
        scheduler_managed=scheduler_managed,
    )
