"""cemp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from django.http import JsonResponse  
from rest_framework.authtoken import views as authtoken_views


def health(request):                  
    return JsonResponse({"status": "ok"})  

urlpatterns = [
    path('', include('home.urls')),
    path('index/', include('home.urls')),
    path('tickets/', include('tickets.urls')),
    path('ionic_liquid/', include('ionic_liquid.urls')),
    path('polymer/', include('polymer.urls')),
    path('crystals/', include('crystals.urls')),
    path('battery_manage_system/', include('battery_manage_system.urls')),
    path('register/', include('register.urls')),
    path('autocompute/', include('autocompute.urls')),
    path('contributor/', include('contributor.urls')),  
    
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  
    
    path("health/", health, name="health"),  
    
    path("api/token/", authtoken_views.obtain_auth_token, name="api_token_auth"),
    
]



urlpatterns +=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
