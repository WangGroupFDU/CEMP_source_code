from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from register.models import Profile
from register.models import UserProfile

admin.site.register(Profile)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'auto_compute_permission',
        'database_permission',
        'ml_prediction_permission',
        'gaussian_permission',
        'daily_task_limit',
    )
    list_select_related = ('user',)

    def changelist_view(self, request, extra_context=None):

        return redirect(reverse("register:user_profile_admin"))

    def change_view(self, request, object_id, form_url="", extra_context=None):

        target_url = reverse("register:user_profile_admin")
        return redirect(f"{target_url}?focus_profile={object_id}")
