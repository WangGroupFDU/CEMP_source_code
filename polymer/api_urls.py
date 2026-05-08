from django.urls import path
from . import api_views

app_name="polymer"

urlpatterns = [
    
    path("polymer_predict_excel/", api_views.process_polymer_predict_view_api, name="api_polymer_predict_view",),
    path("polymer_predict_psmiles/", api_views.polymer_predict_properties_from_psmiles, name="api_polymer_predict_PSMILES_view",),

]