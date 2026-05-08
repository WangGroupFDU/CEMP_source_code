

from functools import wraps
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from rest_framework.authtoken.models import Token

def auto_compute_permission_required(view_func):
    @wraps(view_func)
    @login_required  
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or not profile.auto_compute_permission:
            return HttpResponseForbidden("You do not have permission to access AutoCompute. Please contact user@example.com to request access.")
        return view_func(request, *args, **kwargs)
    return _wrapped


def premium_permission_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or not profile.database_permission:
            return HttpResponseForbidden("You do not have premium permission to access this feature. Please contact user@example.com to request access.")
        return view_func(request, *args, **kwargs)
    return _wrapped


def email_in_valid_domains(view_func):
    """
    Decorator to check if user's email domain is in valid domains.
    Uses the existing validate_email_domain function logic to determine access.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        user_email = request.user.email
        if user_email:
            domain = user_email.split('@')[-1].lower()

            
            
            limited_auth_domains = ['126.com', '163.com', 'qq.com', 'gmail.com', 'outlook.com']

            if domain in limited_auth_domains:
                return HttpResponseForbidden(
                    f"Access restricted: Your email domain '{domain}' has limited authorization. "
                    f"This feature is only available to users with educational (*.edu.*), "
                    f"military (*.mil.*), or government (*.gov.*) domains. "
                    f"You can still access database download features. "
                    f"Please contact user@example.com for more information."
                )

        return view_func(request, *args, **kwargs)
    return _wrapped


def ml_prediction_permission_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or not profile.ml_prediction_permission:
            return HttpResponseForbidden("You do not have permission to access ML Prediction. Please contact user@example.com to request access.")
        return view_func(request, *args, **kwargs)
    return _wrapped

def gaussian_permission_required(view_func):
    @wraps(view_func)
    @login_required  
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or not profile.gaussian_permission:
            return HttpResponseForbidden("You do not have permission to access Gaussian related task. Please contact user@example.com to request access.")
        return view_func(request, *args, **kwargs)
    return _wrapped


def hybrid_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
            try:
                token = Token.objects.get(key=token_key)
                
                request.user = token.user
                return view_func(request, *args, **kwargs)
            except Token.DoesNotExist:
                pass  

        
        
        is_api = (
            request.content_type == 'application/json' or
            'Token' in auth_header or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )

        if is_api:
            
            return JsonResponse({
                'success': False,
                'error': '未登录或Token无效，请先登录获取Token'
            }, status=401)
        else:
            
            return redirect('/register/login/')

    return _wrapped
