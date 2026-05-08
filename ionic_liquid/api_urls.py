from django.urls import path
from . import api_views

app_name="ionic_liquid"

urlpatterns = [
    
    path("ionic_liquid_predict_excel/", api_views.process_excel_ILpredict_XGBoost_view_api, name="api_ionic_liquid_predict_view",),
    
    path("ionic_liquid_predict_SMILES/", api_views.ionic_liquid_predict_from_smiles_api, name="api_ionic_liquid_predict_from_smiles_view",),
]