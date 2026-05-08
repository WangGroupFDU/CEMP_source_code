import re

from django.urls import path, re_path, include

from . import views
from .views_utils.il_generator import generate_il_by_fragments
from .views_utils.database import (
    api_cation_qc_data, api_anion_qc_data, api_il_exp_data, api_il_ml_data
)


app_name='ionic_liquid'

IONIC_LIQUID_DATABASE_EXPORT_FILENAMES = tuple(views.DATABASE_EXPORT_FILES.values())
IONIC_LIQUID_EXPORT_PATTERN = "|".join(re.escape(name) for name in IONIC_LIQUID_DATABASE_EXPORT_FILENAMES)

SPA_EXCLUDE_PATTERNS = [
    'api/',
    'download/',
    'download_template/',
    'XGBoost_predict',
    'ionic_liquid_database_card_page',
    'ionic_liquid_analysis',
    'IL_ML_data',
    'Cation_QC_data',
    'Anion_QC_data',
    'IL_Tm_conductivity_ECW_data',
    'ajax/',
]
SPA_EXCLUDE_PATTERNS.extend(
    fr'{re.escape(name)}$' for name in IONIC_LIQUID_DATABASE_EXPORT_FILENAMES
)
SPA_CATCHALL_PATTERN = '|'.join(SPA_EXCLUDE_PATTERNS)

urlpatterns = [
    path('', views.ionic_liquid_base_page, name='ionic_liquid_base'),
    path('ionic_liquid', views.ionic_liquid_search, name='ionic_liquid'),
    path('ajax/load_anion_types/', views.load_anion_types, name='load_anion_types'),  
    path('ajax/load_anion_names/', views.load_anion_names, name='load_anion_names'),  
    path('search', views.ionic_liquid_search, name='search'),
    path('calculate', views.ionic_liquid_calculate, name='calculate'),
    path('predict', views.ionic_liquid_predict, name='predict'),
    

    
    path('XGBoost_predict', views.XGBoost_predict_page, name='XGBoost_predict_page'),
    path('XGBoost_predict/upload_excel', views.upload_excel_ILpredict_XGBoost_view, name='upload_excel_ILpredict_XGBoost'),
    path('XGBoost_predict/process_excel', views.process_excel_ILpredict_XGBoost_view, name='process_excel_ILpredict_XGBoost'),
    
    
    path('ionic_liquid_database_card_page', views.ionic_liquid_database_card_page, name='ionic_liquid_database_card_page'),
    path('IL_ML_data', views.IL_ML_data_view_paging, name='IL_ML_data'),
    path('Cation_QC_data', views.Cation_QC_data_view, name='Cation_QC_data'),
    path('Anion_QC_data', views.Anion_QC_data_view, name='Anion_QC_data'),
    path('IL_Tm_conductivity_ECW_data', views.IL_Tm_conductivity_ECW_data_view, name='IL_Tm_conductivity_ECW_data'),

    
    path('api/similarity_search/', views.api_il_similarity_search, name='api_il_similarity_search'),
    path('api/property_filter/', views.api_il_property_filter, name='api_il_property_filter'),
    path('ionic_liquid_analysis/', views.ionic_liquid_analysis_page, name='ionic_liquid_analysis_page'),

    
    path('api/Cation_QC_data', api_cation_qc_data, name='api_cation_qc_data'),
    path('api/Anion_QC_data', api_anion_qc_data, name='api_anion_qc_data'),
    path('api/IL_Tm_conductivity_ECW_data', api_il_exp_data, name='api_il_exp_data'),
    path('api/IL_ML_data', api_il_ml_data, name='api_il_ml_data'),
    
    
    path('api/generate_il_by_fragments', generate_il_by_fragments, name='generate_il_by_fragments'),
    
    path('download/<str:filename>', views.download_il_output, name='download_il_output'),
    
    path('download_template/<str:template_type>', views.download_il_template, name='download_il_template'),

    
    path("api/", include("ionic_liquid.api_urls")),

    
    
    
    
    re_path(r'^assets/(?P<path>.*)$', views.spa_assets, name='spa_assets'),

    
    re_path(r'^(?P<filename>RDKit_minimal\.(js|wasm)|.*_(core|backbone)\.xlsx|Ionic_liquid_list.xlsx|Ionic_liquid_list_output.xlsx)$',
            views.spa_static,
            name='spa_static'),
]

if IONIC_LIQUID_EXPORT_PATTERN:
    urlpatterns.append(
        re_path(
            rf'^({IONIC_LIQUID_EXPORT_PATTERN})$',
            views.download_database_export_file,
            name='ionic_liquid_database_export_file',
        )
    )



urlpatterns.append(
    re_path(
        rf'^(?!{SPA_CATCHALL_PATTERN}).*$',
        views.spa_index,
        name='spa_catch_all'
    )
)
