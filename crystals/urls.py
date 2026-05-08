from django.urls import path, re_path, include

from crystals import views

app_name="crystals"

urlpatterns = [
    
    path('', views.crystal_display, name='crystal_display'),
    path('crystal_selected/', views.crystal_selected,name='crystal_selected'), 
    path('crystal_search/',views.crystal_search,name='crystal_search'),
    path('crystal_visualize/',views.crystal_visualize,name='crystal_visualize'), 
    path('crystal_structure_visualization_upload/',views.crystal_structure_visualization_upload,name='crystal_structure_visualization_upload'),
    path('crystal_prediction/',views.crystal_property_prediction_page,name='crystal_prediction'), 
    path('crystal_prediction_upload/',views.upload_prediction,name='crystal_upload_prediction'),
    path('upload_data/',views.upload_data,name='upload_data'),
    path('calculate/',views.calculate,name='calculate'),
    path('prediction/',views.prediction,name='prediction'),

    
    path("api/", include("crystals.api_urls")),

    
    re_path(r'^app/assets/(?P<path>.*)$', views.spa_assets, name='spa_assets'),
    re_path(r'^app/.*$', views.spa_index, name='spa_catch_all'),
]