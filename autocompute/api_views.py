
import json  
import os
import subprocess
import uuid
from datetime import datetime

from django.conf import settings
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes  
from rest_framework.authentication import TokenAuthentication  
from rest_framework.permissions import IsAuthenticated  
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser  
from rest_framework.response import Response  
from rest_framework import status  

from autocompute.models import ComputeTask
from autocompute.molecule_lookup import lookup_molecule_property_similarity
from autocompute.material_recommendation import search_material_recommendation_candidates
from autocompute.views import (process_excel_MDCoumpute_byurl,
                               process_excel_QcCoumpute_HTQC_single_point_energy_byurl,
                                process_excel_QcCoumpute_HTQC_binding_energy_byurl,
                                process_excel_QcCoumpute_HTQC_pka_pkb,
                                process_excel_QcCoumpute_HTQC_ox_red,
                                process_excel_HTQC_reaction_thermo,
                                process_excel_HTQC_global_reaction_properties,
                                process_excel_QcCoumpute_HTQC_single_point_energy_byurl_orca,
                                process_excel_QcCoumpute_HTQC_binding_energy_byurl_orca,
                                process_excel_QcCoumpute_HTQC_ox_red_orca, 
                                process_excel_smiles_query_byurl,
                                draw_ESP_view,
                                draw_ESP_view_gbw,
                                draw_HOMO_LUMO_orb_remote_view,
                                NCI_analysis_view,
                                NCI_promolecular_analysis_view,
                                REMOTE_MARKOV_DOWNLOADS_TARGET,
                                _enqueue_remote_task_for_scheduler,
                                encrypt_download_url_list,
                                )

def convert_legacy_json_response(legacy_response):
    try:
        data = json.loads(legacy_response.content.decode("utf-8"))
        return Response(data, status=legacy_response.status_code)
    except Exception:
        return Response(
            {"error": "Legacy view did not return valid JSON"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _permission_denied_response(required_permission):
    permission_name = str(required_permission).strip()
    if permission_name == "auto_compute_permission":
        message = "You do not have permission to submit autocompute tasks. Please contact user@example.com to request access."
    elif permission_name == "gaussian_permission":
        message = "You do not have permission to access Gaussian related task. Please contact user@example.com to request access."
    else:
        message = "You do not have permission to access this CEMP task. Please contact user@example.com to request access."
    return Response(
        {
            "error": message,
            "error_code": "permission_denied",
            "required_permission": permission_name,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _has_required_permission(request, required_permission):
    profile = getattr(request.user, "userprofile", None)
    if profile is None:
        return False
    return bool(getattr(profile, str(required_permission).strip(), False))


def make_api_excel_upload_return_ID(legacy_view, *, required_permission=""):

    
    @api_view(["POST"])
    @authentication_classes([TokenAuthentication])
    @permission_classes([IsAuthenticated])
    @parser_classes([MultiPartParser, FormParser])
    def api_view_func(request):
        
        if "excel_file" not in request.FILES:
            return Response(
                {"error": "Missing file field: excel_file"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        if required_permission and not _has_required_permission(request, required_permission):
            return _permission_denied_response(required_permission)

        
        legacy_response = legacy_view(request)

        
        return convert_legacy_json_response(legacy_response)

    return api_view_func


def make_api_multifile_upload_return_ID(legacy_view):

    @api_view(["POST"])
    @authentication_classes([TokenAuthentication])
    @permission_classes([IsAuthenticated])
    @parser_classes([MultiPartParser, FormParser])
    def api_view_func(request):
        
        if "files" not in request.FILES:
            return Response(
                {"error": "Missing file field: files"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        if not request.FILES.getlist("files"):
            return Response(
                {"error": "No files uploaded in field: files"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        legacy_response = legacy_view(request)
        return convert_legacy_json_response(legacy_response)

    return api_view_func


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def current_user_permissions_api(request):

    profile = getattr(request.user, "userprofile", None)
    return Response(
        {
            "permissions": {
                "auto_compute_permission": bool(getattr(profile, "auto_compute_permission", False)),
                "gaussian_permission": bool(getattr(profile, "gaussian_permission", False)),
                "ml_prediction_permission": bool(getattr(profile, "ml_prediction_permission", False)),
                "database_permission": bool(getattr(profile, "database_permission", False)),
            }
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def molecule_property_similarity_search_api(request):

    if not _has_required_permission(request, "database_permission"):
        return _permission_denied_response("database_permission")

    smiles = str(request.data.get("smiles", "") or "").strip()
    if not smiles:
        return Response(
            {"error": "Missing required field: smiles", "error_code": "missing_smiles"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = lookup_molecule_property_similarity(
            smiles,
            topk=request.data.get("topk", 3),
            method=request.data.get("method", "tanimoto"),
            radius=request.data.get("radius", 2),
            n_bits=request.data.get("n_bits", 2048),
        )
    except ValueError as exc:
        return Response(
            {"error": str(exc), "error_code": "invalid_request"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        return Response(
            {"error": str(exc), "error_code": "molecule_lookup_failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(result, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def material_recommendation_search_api(request):

    if not _has_required_permission(request, "database_permission"):
        return _permission_denied_response("database_permission")

    try:
        result = search_material_recommendation_candidates(
            str(request.data.get("query", "") or ""),
            domains=request.data.get("domains") or ["auto"],
            topk_pool=request.data.get("topk_pool", 40),
            seed_molecules=request.data.get("seed_molecules") or [],
        )
    except ValueError as exc:
        return Response(
            {"error": str(exc), "error_code": "invalid_request"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        return Response(
            {"error": str(exc), "error_code": "material_recommendation_failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(result, status=status.HTTP_200_OK)


MARKOV_MD_TASK_TYPES = {"MDCoumpute", "MDCoumpute_ORCA"}
MARKOV_TASK_TYPE = "Markov_GDyNet_analysis"


def _resolve_task_directory_from_folder_path(folder_path: str) -> str:

    raw_path = str(folder_path or "").strip()
    if not raw_path:
        return raw_path
    if os.path.exists(raw_path):
        return raw_path
    marker = "/media/"
    normalized = raw_path.replace("\\", "/")
    if marker in normalized:
        relative = normalized.split(marker, 1)[1].lstrip("/")
        candidate = os.path.join(settings.MEDIA_ROOT, relative)
        if os.path.exists(candidate):
            return candidate
    return raw_path


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def submit_markov_gdynet_analysis_api(request):

    if not _has_required_permission(request, "auto_compute_permission"):
        return _permission_denied_response("auto_compute_permission")

    md_task_id = str(request.data.get("md_task_id", "")).strip()
    if not md_task_id:
        return Response(
            {"error": "Missing required field: md_task_id", "error_code": "missing_md_task_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        source_task = ComputeTask.objects.get(task_id=md_task_id)
    except ComputeTask.DoesNotExist:
        return Response(
            {"error": "MD task was not found.", "error_code": "md_task_not_found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if str(source_task.task_type or "") not in MARKOV_MD_TASK_TYPES:
        return Response(
            {
                "error": "Markov/GDyNet analysis can only be launched from a MD task.",
                "error_code": "not_md_task",
                "task_type": source_task.task_type,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if str(source_task.status or "").lower() != "success":
        return Response(
            {
                "error": "Markov/GDyNet analysis requires a completed successful MD task.",
                "error_code": "md_task_not_success",
                "status": source_task.status,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_folder = f"{current_time}_{str(uuid.uuid4())[:6]}"
    download_dir = os.path.join(
        settings.MEDIA_ROOT,
        "AutoCompute",
        "MarkovAnalysis",
        "Downloads",
        unique_folder,
    )
    os.makedirs(download_dir, exist_ok=True)

    all_results_url = os.path.join(
        settings.MEDIA_URL,
        "AutoCompute",
        "MarkovAnalysis",
        "Downloads",
        unique_folder,
        "all_results.zip",
    )
    summary_url = os.path.join(
        settings.MEDIA_URL,
        "AutoCompute",
        "MarkovAnalysis",
        "Downloads",
        unique_folder,
        "markov_summary.xlsx",
    )
    encrypted_id = encrypt_download_url_list([download_dir, all_results_url, summary_url])

    source_md_dir = _resolve_task_directory_from_folder_path(source_task.folder_path)
    request_payload = {
        "source_md_task_id": source_task.task_id,
        "source_md_task_type": source_task.task_type,
        "source_md_status": source_task.status,
        "source_md_dir": source_md_dir,
        "source_md_folder_path": source_task.folder_path,
        "submitted_by_user_id": request.user.id,
    }
    with open(os.path.join(download_dir, "markov_request.json"), "w", encoding="utf-8") as handle:
        json.dump(request_payload, handle, ensure_ascii=False, indent=2)

    task = ComputeTask.objects.create(
        user=request.user,
        task_type=MARKOV_TASK_TYPE,
        task_id=encrypted_id,
        folder_path=download_dir,
        status="pending",
    )
    gdynet_package_dir = str(getattr(settings, "MARKOV_GDYNET_PACKAGE_DIR"))
    _enqueue_remote_task_for_scheduler(
        task,
        source_dir=gdynet_package_dir,
        download_dir=download_dir,
        func_path="autocompute.remote_utils.run_markov_gdynet_analysis_remote",
        remote_target_subpath=REMOTE_MARKOV_DOWNLOADS_TARGET,
    )

    return Response({"encrypted_id": encrypted_id}, status=status.HTTP_200_OK)


process_excel_MDCoumpute_byurl_api = make_api_excel_upload_return_ID(process_excel_MDCoumpute_byurl)

process_excel_QcCoumpute_HTQC_single_point_energy_byurl_api = make_api_excel_upload_return_ID(
    process_excel_QcCoumpute_HTQC_single_point_energy_byurl,
    required_permission="gaussian_permission",
)
process_excel_QcCoumpute_HTQC_binding_energy_byurl_api = make_api_excel_upload_return_ID(
    process_excel_QcCoumpute_HTQC_binding_energy_byurl,
    required_permission="gaussian_permission",
)
process_excel_QcCoumpute_HTQC_pka_pkb_api = make_api_excel_upload_return_ID(
    process_excel_QcCoumpute_HTQC_pka_pkb,
    required_permission="gaussian_permission",
)
process_excel_QcCoumpute_HTQC_ox_red_api = make_api_excel_upload_return_ID(
    process_excel_QcCoumpute_HTQC_ox_red,
    required_permission="gaussian_permission",
)
process_excel_HTQC_reaction_thermo_api = make_api_excel_upload_return_ID(
    process_excel_HTQC_reaction_thermo,
    required_permission="gaussian_permission",
)
process_excel_HTQC_global_reaction_properties_api = make_api_excel_upload_return_ID(
    process_excel_HTQC_global_reaction_properties,
    required_permission="gaussian_permission",
)

process_excel_QcCoumpute_HTQC_single_point_energy_byurl_orca_api = make_api_excel_upload_return_ID(process_excel_QcCoumpute_HTQC_single_point_energy_byurl_orca)
process_excel_QcCoumpute_HTQC_binding_energy_byurl_orca_api = make_api_excel_upload_return_ID(process_excel_QcCoumpute_HTQC_binding_energy_byurl_orca)
process_excel_QcCoumpute_HTQC_ox_red_orca_api = make_api_excel_upload_return_ID(process_excel_QcCoumpute_HTQC_ox_red_orca)

process_excel_smiles_query_byurl_api = make_api_excel_upload_return_ID(process_excel_smiles_query_byurl) 


draw_ESP_api = make_api_multifile_upload_return_ID(draw_ESP_view)
draw_ESP_gbw_api = make_api_multifile_upload_return_ID(draw_ESP_view_gbw)
draw_HOMO_LUMO_orb_api = make_api_multifile_upload_return_ID(draw_HOMO_LUMO_orb_remote_view)
NCI_analysis_api = make_api_multifile_upload_return_ID(NCI_analysis_view)
NCI_promolecular_analysis_api = make_api_multifile_upload_return_ID(NCI_promolecular_analysis_view)
