from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = "bms"





















urlpatterns = [
    path("api/add_data/", views.add_data, name="api_add_data"),
    path("api/visual/", views.visualize_battery_data, name="api_visual"),
    path("api/opendata_view/", views.view_opendata, name="api_view_opendata"),
    path(
        "api/short_prediction/", views.bms_short_prediction, name="api_short_prediction"
    ),
    path("api/long_prediction/", views.bms_long_prediction, name="api_long_prediction"),
    path(
        "api/pattern_recognition/",
        views.pattern_recognition,
        name="api_pattern_recognition",
    ),
    path("api/download/<str:filename>/", views.download_file, name="api_download_file"),
    re_path(r"^$", views.spa_index, name="battery_manage_system"),
    re_path(r"^assets/(?P<path>.*)$", views.spa_assets, name="bms_assets"),
    re_path(r"^.*$", views.spa_index, name="bms_spa"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
