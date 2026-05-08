from django.urls import path
from . import views

app_name = 'contributor'  

urlpatterns = [
    path('', views.contributor_view, name='contributor'),  
    
]