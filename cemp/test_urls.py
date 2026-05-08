from django.contrib import admin
from django.contrib.auth import get_user_model, login
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import include, path

from home import views as home_views


def placeholder_view(request):

    return HttpResponse("ok")


def test_login_view(request, username):

    user_model = get_user_model()
    user = user_model.objects.get(username=username)
    login(request, user)
    return redirect(request.GET.get("next", "/tickets/"))


home_patterns = (
    [
        path("", placeholder_view, name="homepage"),
        path("admin", home_views.admin_view, name="admin"),
        path("query/", placeholder_view, name="query"),
    ],
    "home",
)

autocompute_patterns = ([path("", placeholder_view, name="index")], "autocompute")
ionic_patterns = ([path("", placeholder_view, name="ionic_liquid_base")], "ionic_liquid")
polymer_patterns = ([path("", placeholder_view, name="display")], "polymer")
crystals_patterns = ([path("", placeholder_view, name="crystal_display")], "crystals")
bms_patterns = ([path("", placeholder_view, name="battery_manage_system")], "bms")


urlpatterns = [
    path("", include(home_patterns, namespace="home")),
    path("__test_login__/<str:username>/", test_login_view, name="test_login"),
    path("register/", include("register.urls")),
    path("autocompute/", include(autocompute_patterns, namespace="autocompute")),
    path("ionic_liquid/", include(ionic_patterns, namespace="ionic_liquid")),
    path("polymer/", include(polymer_patterns, namespace="polymer")),
    path("crystals/", include(crystals_patterns, namespace="crystals")),
    path("battery_manage_system/", include(bms_patterns, namespace="bms")),
    path("tickets/", include("tickets.urls")),
    path("admin/", admin.site.urls),
]
