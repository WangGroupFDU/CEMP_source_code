from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from cryptography.fernet import Fernet  
from django.http import JsonResponse
import json, os, re
import logging
import subprocess
from time import monotonic
from django.conf import settings 
from django.views.decorators.csrf import csrf_exempt  
from django.contrib.auth.decorators import login_required
import ast
from autocompute.models import ComputeTask  
from django.utils import timezone
from django.contrib.auth.models import User  
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.forms import modelformset_factory

from register.forms import UserProfileFormSet
from register.models import UserProfile
from register.decorators import hybrid_login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from autocompute.models import ComputeTask

import math  
from datetime import datetime  
from pathlib import Path  
from typing import List, Tuple  

from dateutil.relativedelta import relativedelta  
from django.http import JsonResponse  
from django.views.decorators.http import require_GET  
import itertools                     
from django.db.models import Count, F
from django.db.utils import OperationalError
from django.core.paginator import Paginator





NODE_DEBUG_TASK_ID_PREFIX = "node_debug__"
logger = logging.getLogger(__name__)




QUERY_STATUS_COUNT_CACHE_TTL_SECONDS = 60
_QUERY_STATUS_COUNT_CACHE = {
    "expires_at": 0.0,
    "pending": None,
    "queuing": None,
}


def _production_compute_tasks():

    return ComputeTask.objects.exclude(task_id__startswith=NODE_DEBUG_TASK_ID_PREFIX)


def _get_query_status_counts():

    now = monotonic()
    cached_pending = _QUERY_STATUS_COUNT_CACHE["pending"]
    cached_queuing = _QUERY_STATUS_COUNT_CACHE["queuing"]

    if _QUERY_STATUS_COUNT_CACHE["expires_at"] > now:
        return cached_pending, cached_queuing

    try:
        pending_tasks_count = _production_compute_tasks().filter(status='pending').count()
        queuing_tasks_count = _production_compute_tasks().filter(status='queuing').count()
    except OperationalError:
        logger.warning(
            "Failed to load /query/ status counts from SQLite; using cached values or N/A.",
            exc_info=True,
        )
        return cached_pending, cached_queuing

    _QUERY_STATUS_COUNT_CACHE.update(
        {
            "expires_at": now + QUERY_STATUS_COUNT_CACHE_TTL_SECONDS,
            "pending": pending_tasks_count,
            "queuing": queuing_tasks_count,
        }
    )
    return pending_tasks_count, queuing_tasks_count

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
import pandas as pd                       
from dateutil.relativedelta import relativedelta
from django.contrib.staticfiles.storage import staticfiles_storage
import mimetypes
from django.http import StreamingHttpResponse, FileResponse, Http404
from django.urls import reverse
from home.md_previews import build_legacy_figure_dict, build_md_preview_manifest, is_md_task_type
from autocompute.failure_utils import (
    DEFAULT_FAILURE_CONTENT,
    format_status_message_for_query,
)
from autocompute.remote_utils import _load_remote_server_pool, _ssh_run_command




GAUSS_DIR = Path("/data/Gaussian_database/opt+freq")
ORCA_DIR = Path("/data/ORCA_database/opt+freq")



cipher_suite = Fernet(settings.FERNET_SECRET_KEY)

import logging
logger = logging.getLogger('django')



User = get_user_model()

ALLOWED_ADMINS = {
    'jifengwang': 'user@example.com',
    'ywang':       'user@example.com',
}

ADMIN_CAPABILITY_LABELS = {
    "gaussian_htqc": "Gaussian 16 HTQC",
    "orca_htqc": "ORCA HTQC",
    "md_gromacs_gaussian": "Gromacs + Gaussian MD",
    "visualization_analysis": "Visualization Analysis",
    "markov_analysis": "Markov Analysis",
    "polymer_generation": "Polymer Generation",
}


def _get_admin_remote_server_config_path() -> str:

    return os.path.join(
        settings.BASE_DIR,
        "static",
        "remote_server_info",
        "remote_server_info.json",
    )


def _set_admin_server_enabled_state(server_name: str, enabled: bool) -> dict:

    config_path = _get_admin_remote_server_config_path()
    with open(config_path, "r", encoding="utf-8") as handle:
        raw_servers = json.load(handle)

    if not isinstance(raw_servers, list):
        raise ValueError("remote_server_info.json must be a JSON list.")

    updated_server = None
    for item in raw_servers:
        if isinstance(item, dict) and item.get("server_name") == server_name:
            item["enabled"] = bool(enabled)
            updated_server = item
            break

    if updated_server is None:
        raise KeyError(f"Server {server_name!r} was not found in remote_server_info.json.")

    temp_path = f"{config_path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(raw_servers, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temp_path, config_path)
    return updated_server


def _get_admin_server_runtime_snapshot(server: dict) -> dict:

    remote_login = str(server.get("remote_login", "")).strip()
    ssh_port = int(server.get("ssh_port", 22))
    remote_target_dir = str(server.get("remote_target_dir", "")).strip()
    python_code = (
        "import json, os, sys; "
        f"target_dir = {remote_target_dir!r}; "
        "payload = {"
        "'remote_target_exists': os.path.isdir(target_dir), "
        "'cpu_count': int(os.cpu_count() or 0), "
        "'load_avg': list(os.getloadavg()) if hasattr(os, 'getloadavg') else []"
        "}; "
        "sys.stdout.write(json.dumps(payload))"
    )

    try:
        completed = _ssh_run_command(
            remote_login,
            ["python3", "-c", python_code],
            timeout=8,
            ssh_port=ssh_port,
        )
        payload = json.loads((completed.stdout or "").strip() or "{}")
        remote_target_exists = bool(payload.get("remote_target_exists"))
        load_avg = payload.get("load_avg") or []
        cpu_count = int(payload.get("cpu_count") or 0)
        if remote_target_exists:
            return {
                "status": "online",
                "status_label": "Online",
                "detail": "SSH reachable and remote target directory is ready.",
                "load_avg": load_avg,
                "cpu_count": cpu_count,
                "remote_target_exists": True,
            }
        return {
            "status": "warning",
            "status_label": "Target Missing",
            "detail": f"SSH reachable, but remote target directory is missing: {remote_target_dir}",
            "load_avg": load_avg,
            "cpu_count": cpu_count,
            "remote_target_exists": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "offline",
            "status_label": "SSH Timeout",
            "detail": "The node did not respond within the admin page timeout window.",
            "load_avg": [],
            "cpu_count": 0,
            "remote_target_exists": False,
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        stderr_text = getattr(exc, "stderr", "") or ""
        stdout_text = getattr(exc, "stdout", "") or ""
        detail = (stderr_text.strip() or stdout_text.strip() or str(exc)).strip()
        return {
            "status": "offline",
            "status_label": "Offline",
            "detail": detail[:240],
            "load_avg": [],
            "cpu_count": 0,
            "remote_target_exists": False,
        }


def _build_admin_server_overview() -> dict:

    server_pool = _load_remote_server_pool()
    pending_by_server = {
        item["server_name"]: item["pending_count"]
        for item in (
            _production_compute_tasks()
            .filter(status="pending")
            .values("server_name")
            .annotate(pending_count=Count("id"))
        )
        if item["server_name"]
    }

    server_cards = []
    online_count = 0
    enabled_count = 0
    total_capacity = 0
    total_pending_load = 0

    for server in server_pool:
        runtime = _get_admin_server_runtime_snapshot(server)
        task_limit = int(server.get("task_limit", 0) or 0)
        pending_count = int(pending_by_server.get(server["server_name"], 0))
        utilization_ratio = (pending_count / task_limit) if task_limit > 0 else 0.0
        utilization_percent = int(round(utilization_ratio * 100))
        available_slots = max(task_limit - pending_count, 0)
        capability_labels = [
            ADMIN_CAPABILITY_LABELS.get(capability, capability)
            for capability in server.get("capabilities", [])
        ]

        if server.get("enabled", True):
            enabled_count += 1
        if runtime["status"] == "online":
            online_count += 1
            total_capacity += task_limit
            total_pending_load += pending_count

        server_cards.append(
            {
                "server_name": server["server_name"],
                "remote_login": server["remote_login"],
                "ssh_port": server.get("ssh_port", 22),
                "remote_target_dir": server.get("remote_target_dir", ""),
                "scheduler_enabled": bool(server.get("enabled", True)),
                "task_limit": task_limit,
                "pending_count": pending_count,
                "available_slots": available_slots,
                "utilization_ratio": utilization_ratio,
                "utilization_percent": utilization_percent,
                "status": runtime["status"],
                "status_label": runtime["status_label"],
                "status_detail": runtime["detail"],
                "capability_labels": capability_labels,
                "load_avg": runtime["load_avg"],
                "cpu_count": runtime["cpu_count"],
            }
        )

    summary = {
        "configured_count": len(server_pool),
        "enabled_count": enabled_count,
        "online_count": online_count,
        "total_capacity": total_capacity,
        "total_pending_load": total_pending_load,
        "free_slots": max(total_capacity - total_pending_load, 0),
    }
    return {"servers": server_cards, "summary": summary}


@csrf_exempt
@require_POST
@login_required(login_url='/register/login/')
def toggle_server_enabled(request):

    if request.user.username not in ALLOWED_ADMINS:
        return HttpResponseForbidden("您无权访问此页面。")

    try:
        payload = json.loads(request.body.decode("utf-8"))
        server_name = str(payload.get("server_name", "")).strip()
        enabled = payload.get("enabled")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponseBadRequest("Invalid JSON payload.")

    if not server_name or not isinstance(enabled, bool):
        return HttpResponseBadRequest("Both server_name and boolean enabled are required.")

    try:
        updated_server = _set_admin_server_enabled_state(server_name, enabled)
    except KeyError as exc:
        return HttpResponseBadRequest(str(exc))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return HttpResponseBadRequest(f"Failed to update server state: {exc}")

    action_text = "enabled for future scheduling" if enabled else "removed from future scheduling"
    return JsonResponse(
        {
            "success": True,
            "server_name": updated_server.get("server_name"),
            "enabled": bool(updated_server.get("enabled", False)),
            "message": (
                f"{updated_server.get('server_name')} has been {action_text}. "
                "Tasks that are already running on this node will continue to completion."
            ),
        }
    )


@csrf_exempt
def gsc_verify_view(request):
    return render(request, 'googlea23ddb018d244e67.html')

def home(request):
    
    task_count = ComputeTask.objects.count()
    user_count = User.objects.count()

    
    expected = ALLOWED_ADMINS.get(request.user.username, '').lower()
    show_admin = expected and (request.user.email.lower() == expected)

    
    return render(request, 'base.html', {
        'task_count': task_count,
        'user_count': user_count,
        'show_admin': show_admin,
    })
@csrf_exempt
@login_required(login_url='/register/login/')
def admin_view(request):

    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("您无权访问此页面。")

    return redirect("register:user_profile_admin")


@csrf_exempt
@login_required(login_url='/register/login/')  
def API_introduction_view(request):
    return render(request, 'API.html')

@csrf_exempt
@api_view(['POST'])
@authentication_classes([SessionAuthentication])  
@permission_classes([IsAuthenticated])          
def generate_api_key(request):
    
    token, created = Token.objects.get_or_create(user=request.user)
    
    return Response({'token': token.key})


@csrf_exempt
def how_to_cite_view(request):
    return render(request, 'how_to_cite.html')


@csrf_exempt
@require_POST
def cancel_task(request):
    try:
        
        payload = json.loads(request.body.decode('utf-8'))
        task_id = payload.get('task_id')
        if not task_id:
            return HttpResponseBadRequest('Missing task_id')
        
        

        
        download_url_list = decrypt_download_url_list(task_id)
        directory = download_url_list[0]

        

        
        stop_path    = os.path.join(directory, 'stop.txt')
        failure_path= os.path.join(directory, 'failure.txt')
        with open(stop_path,   'w', encoding='utf-8') as f:
            f.write('Task manually terminated')
        with open(failure_path,'w', encoding='utf-8') as f:
            f.write('Task manually terminated')

        

        
        for fname in os.listdir(directory):
            if fname not in ('stop.txt', 'failure.txt'):
                path = os.path.join(directory, fname)
                if os.path.isfile(path):
                    os.remove(path)

        
        with open(os.path.join(directory, 'have_stopped.txt'),
                  'w', encoding='utf-8') as f:
            f.write('')

        
        try:
            task = ComputeTask.objects.get(task_id=task_id)
            task.status = 'failed'
            task.save(update_fields=['status'])
        except ComputeTask.DoesNotExist:
            return HttpResponseBadRequest('ComputeTask not found')

        
        return JsonResponse({'success': True, 'message': 'Task has been terminated'})

    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')


@csrf_exempt  
@require_POST
@login_required
def update_task_priority(request):
    try:
        payload = json.loads(request.body) 
        task_id  = payload['task_id'] 
        priority = int(payload['priority']) 
        
        logger.info(f"pass1: task_id:{task_id}")
        logger.info(f"pass2: priority:{priority}")

    except (ValueError, KeyError, json.JSONDecodeError) as e:
        return HttpResponseBadRequest("Parameter error")

    
    try:
        task = ComputeTask.objects.get(task_id=task_id)
    except ComputeTask.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task does not exist'})

    
    if request.user.username not in ALLOWED_ADMINS:
        return JsonResponse({'success': False, 'error': 'No permission'})

    
    task.priority = priority 
    task.save(update_fields=['priority'])
    return JsonResponse({'success': True})

@csrf_exempt
@login_required(login_url='/register/login/')  
def query_view(request):
    
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

    
    user_tasks = ComputeTask.objects.filter(user=request.user, created_at__gte=thirty_days_ago).order_by('-created_at')

    
    
    pending_tasks_count, queuing_tasks_count = _get_query_status_counts()

    
    return render(request, 'query.html', {'tasks': user_tasks, 'pending_tasks_count': pending_tasks_count, 'queuing_tasks_count': queuing_tasks_count})


@csrf_exempt
@login_required(login_url='/register/login/')  
def admin_query_view(request):

    
    if request.user.username not in ALLOWED_ADMINS:
        return HttpResponseForbidden("您无权访问此页面。")

    
    
    admin_query_days = 60
    admin_page_size = 20
    cutoff_time = timezone.now() - timezone.timedelta(days=admin_query_days)
    task_queryset = (
        ComputeTask.objects
        .filter(created_at__gte=cutoff_time)
        .select_related('user')
        .order_by('-created_at')
    )
    paginator = Paginator(task_queryset, admin_page_size)
    page_obj = paginator.get_page(request.GET.get('page'))
    user_tasks = page_obj.object_list

    
    pending_tasks_count = ComputeTask.objects.filter(status='pending').count()

    
    queuing_tasks_count = ComputeTask.objects.filter(status='queuing').count()
    server_overview = _build_admin_server_overview()

    
    return render(
        request,
        'admin_query.html',
        {
            'tasks': user_tasks,
            'page_obj': page_obj,
            'paginator': paginator,
            'admin_query_days': admin_query_days,
            'admin_page_size': admin_page_size,
            'admin_task_total': paginator.count,
            'pending_tasks_count': pending_tasks_count,
            'queuing_tasks_count': queuing_tasks_count,
            'server_cards': server_overview['servers'],
            'server_summary': server_overview['summary'],
        },
    )


def decrypt_download_url_list(encrypted_id):
    try:
        
        decrypted = cipher_suite.decrypt(encrypted_id.encode('utf-8'))

        
        download_url_list = json.loads(decrypted.decode('utf-8'))

        return download_url_list
    except Exception as e:
        
        print(f"解密失败: {str(e)}")
        return None


@csrf_exempt  
@require_POST  
def get_task_directory(request):
    data = json.loads(request.body)
    encrypted_id = data.get("encrypted_id", None)  
    download_url_list = decrypt_download_url_list(encrypted_id)
    directory = download_url_list[0]
    return JsonResponse({"success": True, "directory": directory})
    

@hybrid_login_required  
@csrf_exempt
def check_task_status(request):
    
    if request.method != 'POST':
        
        return JsonResponse(
            {'status': 'failed', 'message': 'Task failed', 'download_urls': []},
            status=400
        )

    data = json.loads(request.body)
    encrypted_id = data.get('encrypted_id')
    if not encrypted_id:
        return JsonResponse({'status': 'error', 'message': 'Invalid encrypted ID'})

    
    download_url_list = decrypt_download_url_list(encrypted_id)     
    directory = download_url_list[0]                                
    success_signal_path = os.path.join(directory, 'success.txt')    
    failure_signal_path = os.path.join(directory, 'failure.txt')

    
    task_obj = None
    try:
        task_obj = ComputeTask.objects.get(task_id=encrypted_id)    
        task_type = task_obj.task_type or 'unknown'
    except ComputeTask.DoesNotExist:
        task_type = 'unknown'

    
    if os.path.exists(failure_signal_path):
        with open(failure_signal_path, 'r') as f:
            failure_content = f.read()
        return JsonResponse({'status': 'failed',
                             'failure_content': failure_content,
                             'task_type': task_type})   

    
    
    
    
    if task_obj is not None and task_obj.status == 'failed':
        failure_content = format_status_message_for_query(task_obj.status_message)
        if not failure_content:
            failure_content = DEFAULT_FAILURE_CONTENT
        return JsonResponse({
            'status': 'failed',
            'failure_content': failure_content,
            'task_type': task_type,
        })

    
    if os.path.exists(success_signal_path):
        
        download_links = download_url_list[1:]

        
        if is_md_task_type(task_type):
            
            table_data_url = download_url_list[1]
        else:
            
            table_data_url = download_url_list[2] if len(download_url_list) > 2 else None

        
        
        
        
        
        figure_previews = []
        figure_data_url_dict = {}
        if is_md_task_type(task_type):
            figure_previews = build_md_preview_manifest(
                download_dir=directory,
                table_data_url=table_data_url,
                force_rebuild=False,
            )
            figure_data_url_dict = build_legacy_figure_dict(figure_previews)

        
        response_data = {
            'status': 'success',
            'task_type': task_type,
            'download_urls': download_links,
            'table_data_url': table_data_url
        }
        if figure_previews:
            response_data['figure_previews'] = figure_previews
        if figure_data_url_dict:                 
            response_data['figure_data_url_dict'] = figure_data_url_dict

        return JsonResponse(response_data)

    
    return JsonResponse({'status': 'not_finished', 'task_type': task_type})


def news_and_updates_view(request):
    json_path = os.path.join(settings.BASE_DIR, 'news_items.json')
    with open(json_path, 'r') as f:
        news_items = json.load(f)
    return render(request, 'news_and_updates.html', {'news_items': news_items})


@require_GET  
def quarterly_counts(request):
    
    cache_dir  = Path(settings.BASE_DIR) / "home" / "static" / "QC_data_number"
    cache_dir.mkdir(parents=True, exist_ok=True)          
    cache_file = cache_dir / "QC_data_number.xlsx"

    now = datetime.now()

    
    quarter_ago = now - relativedelta(months=3)

    if cache_file.exists():
        ctime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        
        if ctime >= quarter_ago:
            df_cache = pd.read_excel(cache_file)
            return JsonResponse({
                "labels": df_cache["labels"].tolist(),
                "counts": df_cache["counts"].tolist()
            })
        
    
    timestamps: List[float] = []  

    
    for base_dir in (GAUSS_DIR, ORCA_DIR):
        for fp in base_dir.rglob("*"):    
            if fp.is_file():               
                stat = fp.stat()           
                
                ts = getattr(stat, "st_birthtime", stat.st_mtime)
                timestamps.append(ts)      

    
    if not timestamps:
        return JsonResponse({"labels": [], "counts": []})

    
    dt_start = datetime.fromtimestamp(min(timestamps)).replace(day=1)  
    dt_end = datetime.fromtimestamp(max(timestamps))                   
    
    n_quarters = math.ceil((dt_end.year * 12 + dt_end.month -
                            dt_start.year * 12 - dt_start.month + 1) / 3)

    
    quarter_starts: List[datetime] = [
        dt_start + relativedelta(months=+3 * i) for i in range(n_quarters)
    ]

    
    counts = [0] * n_quarters

    
    for ts in timestamps:
        dt = datetime.fromtimestamp(ts)
        
        idx = ((dt.year - dt_start.year) * 12 + dt.month - dt_start.month) // 3
        counts[idx] += 1

    
    labels = [dt.strftime("%Y‑%m") for dt in quarter_starts]  

    
    cumulative_counts = list(itertools.accumulate(counts))   
    
    
    df_out = pd.DataFrame({"labels": labels, "counts": cumulative_counts})
    cache_dir.mkdir(parents=True, exist_ok=True)          
    df_out.to_excel(cache_file, index=False)
    
    
    return JsonResponse({"labels": labels, "counts": cumulative_counts})


def calculate_task_quarterly_counts(request):
    
    cache_dir  = Path(settings.BASE_DIR) / "home" / "static" / "QC_data_number"
    cache_file = cache_dir / "calculate_task_number.xlsx"      
    quarter_ago = timezone.now() - relativedelta(months=3)     

    if cache_file.exists():
        ctime = datetime.fromtimestamp(cache_file.stat().st_mtime,
                                       tz=timezone.get_current_timezone())
        if ctime >= quarter_ago:                               
            df = pd.read_excel(cache_file)
            return JsonResponse({
                "labels": df["labels"].tolist(),
                "counts": df["counts"].tolist()
            })
        
    
    dates_qs = ComputeTask.objects.values_list('created_at', flat=True)

    if not dates_qs.exists():                           
        return JsonResponse({"labels": [], "counts": []})

    
    
    
    datetimes: List[datetime] = list(dates_qs)
    dt_start = min(datetimes).astimezone(timezone.get_current_timezone())
    dt_end   = max(datetimes).astimezone(timezone.get_current_timezone())

    
    dt_start = dt_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    
    months_diff = (dt_end.year * 12 + dt_end.month) - (dt_start.year * 12 + dt_start.month) + 1
    n_quarters  = math.ceil(months_diff / 3)

    
    counts = [0] * n_quarters

    
    for dt in datetimes:
        
        idx = ((dt.year - dt_start.year) * 12 + dt.month - dt_start.month) // 3
        counts[idx] += 1

    
    labels = [
        (dt_start + relativedelta(months=3 * i)).strftime("%Y-%m") for i in range(n_quarters)
    ]
    
    cumulative_counts = list(itertools.accumulate(counts))   

    
    cache_dir.mkdir(parents=True, exist_ok=True)          
    pd.DataFrame({"labels": labels,
                  "counts": cumulative_counts}).to_excel(cache_file, index=False)

    return JsonResponse({"labels": labels, "counts": cumulative_counts})




def file_iterator(path, offset=0, length=None, chunk_size=65536):
    with open(path, 'rb') as f:
        f.seek(offset)
        remaining = length
        while True:
            bytes_to_read = chunk_size if remaining is None else min(remaining, chunk_size)
            data = f.read(bytes_to_read)
            if not data:
                break
            if remaining is not None:
                remaining -= len(data)
            yield data


def stream_video(request, app, filename):
    
    base_dir = os.path.join(settings.BASE_DIR, 'home', 'static', 'tutorial_vedio', app)
    file_path = os.path.normpath(os.path.join(base_dir, filename))
    if not file_path.startswith(base_dir) or not os.path.exists(file_path):
        raise Http404("Video not found")

    file_size = os.path.getsize(file_path)
    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or 'application/octet-stream'

    
    range_header = request.headers.get('Range', '').strip()
    range_match = re.match(r'bytes=(\d*)-(\d*)', range_header)
    if range_match:
        
        start = int(range_match.group(1)) if range_match.group(1) else 0
        
        end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
        end = min(end, file_size - 1)           
        length = end - start + 1

        response = StreamingHttpResponse(
            file_iterator(file_path, offset=start, length=length),
            status=206,                         
            content_type=content_type
        )
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
    else:
        
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Length'] = str(file_size)

    
    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = 'public, max-age=86400'   
    return response
def tutorial_list(request):
    base_dir = os.path.join(            
        settings.BASE_DIR, 'home', 'static', 'tutorial_vedio')

    app_dict = {}                       
    if os.path.isdir(base_dir):         
        for app_name in sorted(os.listdir(base_dir)):    
            app_path = os.path.join(base_dir, app_name)  
            if os.path.isdir(app_path):                  
                videos = []                              
                for file in sorted(os.listdir(app_path)):    
                    if file.lower().endswith(            
                        ('.mp4', '.webm', '.ogg')):
                        stream_url = reverse('home:video_stream', kwargs={'app': app_name, 'filename': file}) 
                        videos.append({'title': os.path.splitext(file)[0], 'url': stream_url})

                if videos:                               
                    app_dict[app_name] = videos          

    context = {'apps': app_dict}         
    return render(request,               
                  'tutorials/tutorial_list.html',
                  context)

