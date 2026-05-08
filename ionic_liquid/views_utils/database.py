"""
Database API Views for Ionic Liquid Platform
Provides JSON API endpoints for database access
"""

import logging
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from register.decorators import hybrid_login_required
from ionic_liquid.models import (
    IL_ML_data,
    Cation_QC_data,
    Anion_QC_data,
    IL_Tm_conductivity_ECW_data
)


logger = logging.getLogger(__name__)


@hybrid_login_required
@require_http_methods(["GET"])
def api_cation_qc_data(request):
    """
    API endpoint for Cation QC Database with pagination, search and sorting

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Number of records per page (default: 20, max: 500)
    - search: Search term for Name and SMILES fields
    - sort_field: Field to sort by (default: 'id')
    - sort_order: 'asc' or 'desc' (default: 'asc')

    Example:
    GET /ionic_liquid/api/Cation_QC_data?page=1&page_size=50&search=methyl&sort_field=Name&sort_order=asc
    """
    try:
        
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 500)  
        search = request.GET.get('search', '').strip()
        sort_field = request.GET.get('sort_field', 'id')
        sort_order = request.GET.get('sort_order', 'asc')

        
        queryset = Cation_QC_data.objects.all()

        
        if search:
            queryset = queryset.filter(
                Q(Name__icontains=search) |
                Q(SMILES__icontains=search)
            )

        
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'

        
        valid_fields = [f.name for f in Cation_QC_data._meta.get_fields()]
        if sort_field.lstrip('-') in valid_fields:
            queryset = queryset.order_by(sort_field)

        
        total_count = queryset.count()

        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        
        fields = Cation_QC_data._meta.get_fields()
        field_names = [f.name for f in fields]

        
        data = []
        for obj in page_obj:
            item = {}
            for field_name in field_names:
                value = getattr(obj, field_name)
                
                item[field_name] = value if value is not None else ''
            data.append(item)

        response_dict = {
            'success': True,
            'data': data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'meta': {
                'field_names': field_names,
                'searchable_fields': ['Name', 'SMILES'],
                'sortable_fields': field_names,
                'source': 'QC',
                'type': 'Cation'
            }
        }

        return JsonResponse(response_dict)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch Cation QC data'
        }, status=500)


@hybrid_login_required
@require_http_methods(["GET"])
def api_anion_qc_data(request):
    """
    API endpoint for Anion QC Database with pagination, search and sorting

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Number of records per page (default: 20, max: 500)
    - search: Search term for Name and SMILES fields
    - sort_field: Field to sort by (default: 'id')
    - sort_order: 'asc' or 'desc' (default: 'asc')

    Example:
    GET /ionic_liquid/api/Anion_QC_data?page=1&page_size=50&search=chloride&sort_field=Name&sort_order=asc
    """
    try:
        
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 500)  
        search = request.GET.get('search', '').strip()
        sort_field = request.GET.get('sort_field', 'id')
        sort_order = request.GET.get('sort_order', 'asc')

        
        queryset = Anion_QC_data.objects.all()

        
        if search:
            queryset = queryset.filter(
                Q(Name__icontains=search) |
                Q(SMILES__icontains=search)
            )

        
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'

        
        valid_fields = [f.name for f in Anion_QC_data._meta.get_fields()]
        if sort_field.lstrip('-') in valid_fields:
            queryset = queryset.order_by(sort_field)

        
        total_count = queryset.count()

        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        
        fields = Anion_QC_data._meta.get_fields()
        field_names = [f.name for f in fields]

        
        data = []
        for obj in page_obj:
            item = {}
            for field_name in field_names:
                value = getattr(obj, field_name)
                
                item[field_name] = value if value is not None else ''
            data.append(item)

        response_dict = {
            'success': True,
            'data': data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'meta': {
                'field_names': field_names,
                'searchable_fields': ['Name', 'SMILES'],
                'sortable_fields': field_names,
                'source': 'QC',
                'type': 'Anion'
            }
        }

        return JsonResponse(response_dict)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch Anion QC data'
        }, status=500)


@hybrid_login_required
@require_http_methods(["GET"])
def api_il_exp_data(request):
    """
    API endpoint for IL Experiment Database (Tm, Conductivity, ECW) with pagination, search and sorting

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Number of records per page (default: 20, max: 500)
    - search: Search term for Name, SMILES, Anion_SMILES, Cation_SMILES fields
    - sort_field: Field to sort by (default: 'id')
    - sort_order: 'asc' or 'desc' (default: 'asc')

    Example:
    GET /ionic_liquid/api/IL_Tm_conductivity_ECW_data?page=1&page_size=50&search=imidazolium&sort_field=Tm&sort_order=desc
    """
    try:
        
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 500)  
        search = request.GET.get('search', '').strip()
        sort_field = request.GET.get('sort_field', 'id')
        sort_order = request.GET.get('sort_order', 'asc')

        
        queryset = IL_Tm_conductivity_ECW_data.objects.all()

        
        if search:
            queryset = queryset.filter(
                Q(Name__icontains=search) |
                Q(SMILES__icontains=search) |
                Q(Anion_SMILES__icontains=search) |
                Q(Cation_SMILES__icontains=search)
            )

        
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'

        
        valid_fields = [f.name for f in IL_Tm_conductivity_ECW_data._meta.get_fields()]
        if sort_field.lstrip('-') in valid_fields:
            queryset = queryset.order_by(sort_field)

        
        total_count = queryset.count()

        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        
        fields = IL_Tm_conductivity_ECW_data._meta.get_fields()
        field_names = [f.name for f in fields]

        
        data = []
        for obj in page_obj:
            item = {}
            for field_name in field_names:
                value = getattr(obj, field_name)
                
                item[field_name] = value if value is not None else ''
            data.append(item)

        response_dict = {
            'success': True,
            'data': data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'meta': {
                'field_names': field_names,
                'searchable_fields': ['Name', 'SMILES', 'Anion_SMILES', 'Cation_SMILES'],
                'sortable_fields': field_names,
                'source': 'QC and EXP',
                'type': 'Ionic Liquid'
            }
        }

        return JsonResponse(response_dict)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch IL Experiment data'
        }, status=500)


@hybrid_login_required
@require_http_methods(["GET"])
def api_il_ml_data(request):
    """
    API endpoint for IL ML Database (Machine Learning Generated) with pagination, search and sorting

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Number of records per page (default: 20, max: 500)
    - search: Search term for Name, SMILES, Anion_SMILES, Cation_SMILES fields
    - sort_field: Field to sort by (default: 'id')
    - sort_order: 'asc' or 'desc' (default: 'asc')

    Example:
    GET /ionic_liquid/api/IL_ML_data?page=1&page_size=50&search=pyrrolidinium&sort_field=ECW&sort_order=desc
    """
    try:
        
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)  
        search = request.GET.get('search', '').strip()
        sort_field = request.GET.get('sort_field', 'id')
        sort_order = request.GET.get('sort_order', 'asc')

        
        queryset = IL_ML_data.objects.all()

        
        if search:
            queryset = queryset.filter(
                Q(Name__icontains=search) |
                Q(SMILES__icontains=search) |
                Q(Anion_SMILES__icontains=search) |
                Q(Cation_SMILES__icontains=search)
            )

        
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'

        
        valid_fields = [f.name for f in IL_ML_data._meta.get_fields()]
        if sort_field.lstrip('-') in valid_fields:
            queryset = queryset.order_by(sort_field)

        
        total_count = queryset.count()

        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        
        fields = IL_ML_data._meta.get_fields()
        field_names = [f.name for f in fields]

        
        data = []
        for obj in page_obj:
            item = {}
            for field_name in field_names:
                value = getattr(obj, field_name)
                
                item[field_name] = value if value is not None else ''
            data.append(item)

        response_dict = {
            'success': True,
            'data': data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
            'meta': {
                'field_names': field_names,
                'searchable_fields': ['Name', 'SMILES', 'Anion_SMILES', 'Cation_SMILES'],
                'sortable_fields': field_names,
                'source': 'ML',
                'type': 'Ionic Liquid'
            }
        }

        return JsonResponse(response_dict)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch IL ML data'
        }, status=500)
