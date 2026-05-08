from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = "register"

urlpatterns = [
    
    
    path(
        "login/", csrf_exempt(views.user_login), name="login"
    ),  
    path("logout/", csrf_exempt(views.user_logout), name="logout"),  
    path(
        "register/", csrf_exempt(views.user_register), name="register"
    ),  
    path("activate/", views.user_activate, name="activate"),  
    path(
        "resend_activation/",
        csrf_exempt(views.resend_activation_email),
        name="resend_activation",
    ),
    path("delete/<int:id>", views.user_delete, name="delete"),
    path("edit/<int:id>/", views.profile_edit, name="edit"),
    path(
        "admin/user-profiles/",
        views.user_profile_admin_view,
        name="user_profile_admin",
    ),
    path("modify_email/", views.modify_email, name="modify_email"),
    path("password_reset/", views.password_reset, name="password_reset"),
    path("send_test_email/", views.send_test_email, name="send_test_email"),
    
    path("api/user/", views.api_user_info, name="api_user_info"),  
    path(
        "api/get-or-create-token/",
        views.get_or_create_token,
        name="get_or_create_token",
    ),  
]
