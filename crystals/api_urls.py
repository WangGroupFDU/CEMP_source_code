from django.urls import path
from . import api_views

app_name="crystals"

urlpatterns = [
    
    path("crystal_predict_excel/", api_views.upload_prediction_api, name="api_crystal_predict_view",),

    
    path("crystal_list/", api_views.api_crystal_list, name="api_crystal_list"),
    path("crystal_data/", api_views.api_crystal_data, name="api_crystal_data"),
]