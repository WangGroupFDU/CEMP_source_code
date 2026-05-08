
import json  
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes  
from rest_framework.authentication import TokenAuthentication  
from rest_framework.permissions import IsAuthenticated  
from rest_framework.parsers import MultiPartParser, FormParser  
from rest_framework.response import Response  
from rest_framework import status  

from crystals.views import upload_prediction

def make_api_cif_upload_return_ID(legacy_view):

    @api_view(["POST"])
    @authentication_classes([TokenAuthentication])
    @permission_classes([IsAuthenticated])
    @parser_classes([MultiPartParser, FormParser])
    def api_view_func(request):
        
        
        
        
        model_type = request.data.get("modelSelect", None)  
        if not model_type:
            return Response(
                {"error": "Missing field: modelSelect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        if "cifFile" not in request.FILES:
            return Response(
                {"error": "Missing file field: cifFile"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        
        
        legacy_response = legacy_view(request._request)  

        
        
        
        try:
            data = json.loads(legacy_response.content.decode("utf-8"))
            return Response(data, status=getattr(legacy_response, "status_code", 200))
        except Exception:
            return Response(
                {"error": "Legacy view did not return valid JSON"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return api_view_func


upload_prediction_api = make_api_cif_upload_return_ID(upload_prediction)





from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from crystals.models import Crystal


@csrf_exempt
def api_crystal_list(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    types = list(
        Crystal.objects.values_list('crystal', flat=True)
        .distinct()
        .order_by('crystal')
    )
    return JsonResponse({'crystal_types': types})


@csrf_exempt
def api_crystal_data(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    selected = request.GET.get('crystal', 'Al')
    excluded_fields = ['id', 'author', 'Author']

    field_names = [
        f.name for f in Crystal._meta.get_fields()
        if f.name not in excluded_fields and not isinstance(f, type(Crystal))
    ]

    qs = Crystal.objects.filter(crystal=selected)
    data = []
    from decimal import Decimal
    for row in qs:
        row_dict = {}
        for name in field_names:
            val = getattr(row, name)
            if isinstance(val, Decimal):
                val = float(val)
            row_dict[name] = val
        data.append(row_dict)

    return JsonResponse({
        'field_names': field_names,
        'data': data,
        'selected_crystal': selected,
        'total': len(data),
    })
