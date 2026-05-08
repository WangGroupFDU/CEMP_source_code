from django.urls import path, re_path, include
from . import views
from .sitemaps import StaticViewSitemap
from django.contrib.sitemaps import views as sitemaps_views         
from django.contrib.sitemaps.views import sitemap          

app_name = 'home'

sitemaps = {                                                        
    "static": StaticViewSitemap,
    
}

urlpatterns = [
    path('', views.home, name = 'homepage'),
    path("task_number_quarterly_counts/", views.quarterly_counts, name="task_number_quarterly_counts"), 
    path("calculate_task_quarterly_counts/", views.calculate_task_quarterly_counts, name="calculate_task_quarterly_counts"), 

    path('API_introduction/', views.API_introduction_view, name = 'API_introduction'),
    path('generate_API/', views.generate_api_key, name = 'generate_api_key'),
    path('News_and_Updates/', views.news_and_updates_view, name = 'news_and_updates'),
    path('How_to_cite/', views.how_to_cite_view, name = 'how_to_cite'),

    path('query/', views.query_view, name = 'query'),
    path('query/check_task_status', views.check_task_status, name = 'check_task_status'),
    path('query/cancel_task', views.cancel_task, name = 'cancel_task'), 

    path('admin', views.admin_view, name = 'admin'), 
    path('admin_query', views.admin_query_view, name = 'admin_query'), 
    path('admin_update_priority', views.update_task_priority, name = 'update_task_priority'), 
    path('admin_query_abs_task_file', views.get_task_directory, name = 'get_task_directory'), 
    path('admin_toggle_server_enabled', views.toggle_server_enabled, name='toggle_server_enabled'),

    
    path("api/check_task_status/", views.check_task_status, name="api_check_task_status"),

    
    path('tutorial_videos', views.tutorial_list, name = 'tutorial_list'), 
    
    re_path(r'^stream/(?P<app>[^/]+)/(?P<filename>.+)$',
            views.stream_video,
            name='video_stream'),
    
    
    path("googlea23ddb018d244e67.html", views.gsc_verify_view, name="gsc_verify"),  
    
    
    path(
        "sitemap.xml",                                     
        sitemap,                                           
        {"sitemaps": sitemaps},                            
        name="sitemap",                                    
    ),
]
