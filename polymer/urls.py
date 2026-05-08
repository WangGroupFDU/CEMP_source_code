import re

from django.urls import path, re_path, include
from django.conf import settings
from django.views.static import serve as static_serve

from polymer import views

POLYMER_DATABASE_EXPORT_FILENAMES = tuple(views.DATABASE_EXPORT_FILES.values())
POLYMER_EXPORT_PATTERN = "|".join(re.escape(name) for name in POLYMER_DATABASE_EXPORT_FILENAMES)

SPA_EXCLUDE_PATTERNS = [
    'api/',
    'polymer_database/$',
    'generate_polymer',
    'predict_copolymer',
    'visualization_structure',
    'polymer_predict_page',
    'upload_polymer_predict_file',
    'process_polymer_predict',
]
SPA_EXCLUDE_PATTERNS.extend(
    fr'{re.escape(name)}$' for name in POLYMER_DATABASE_EXPORT_FILENAMES
)
SPA_CATCHALL_PATTERN = '|'.join(SPA_EXCLUDE_PATTERNS)


app_name="polymer"

urlpatterns = [
    path('', views.display, name='display'), 
    
    path('generate_polymer_display', views.generate_polymer_display, name='generate_polymer_display'), 
    path('generate_polymer/', views.generate_polymer, name='generate_polymer'), 
    path('predict_copolymer/', views.copolymer_property_predict, name='copolymer_property_predict'), 

    
    path('visualization_structure/', views.visualization_structure, name='visualization_structure'), 
    
    
    
    path('polymer_database/', views.polymer_database_card_display_view, name='polymerdatabase_display_card'), 
    
    
    
    

    
    path('polymer_predict_page', views.polymer_predict_page_view, name='polymer_predict_page'), 
    path('upload_polymer_predict_file', views.upload_excel_polymer_predict_file_view, name='upload_excel_polymer_predict_file'), 
    path('process_polymer_predict', views.process_polymer_predict_view, name='process_polymer_predict'), 
    
    
    path('api/similarity-search/', views.api_similarity_search, name='api_similarity_search'), 
    path('api/polymer-prediction/', views.polymerization_prediction, name='api_polymer_prediction'), 

    
    path('api/experiment-polymer-data/', views.api_experiment_polymer_data, name='api_experiment_polymer_data'), 
    path('api/public/experiment-polymer-data/', views.api_public_experiment_polymer_data, name='api_public_experiment_polymer_data'), 
    path('api/public/calculated-polymer-data/', views.api_public_calculated_polymer_data, name='api_public_calculated_polymer_data'), 
    path('api/public/calculated-monomer-data/', views.api_public_calculated_monomer_data, name='api_public_calculated_monomer_data'), 
    path('api/download/<str:database_name>/', views.download_database_export, name='download_database_export'), 

    
    path("api/", include("polymer.api_urls")),

    
    
    re_path(r'^assets/(?P<path>.*)$', views.analysis_assets, name='polymer_assets'),

    
    re_path(r'^(?P<filename>RDKit_minimal\.(js|wasm)|.*_template\.(csv|xlsx))$',
            views.analysis_static,
            name='polymer_static'),
]

if POLYMER_EXPORT_PATTERN:
    urlpatterns.append(
        re_path(
            rf'^({POLYMER_EXPORT_PATTERN})$',
            views.download_database_export_file,
            name='polymer_database_export_file',
        )
    )



urlpatterns.append(
    re_path(rf'^(?!{SPA_CATCHALL_PATTERN}).*$', views.analysis_index, name='polymer_spa'),
)
