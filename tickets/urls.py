from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("", views.ticket_list_view, name="list"),
    path("new/", views.ticket_create_view, name="create"),
    path("manage/", views.ticket_manage_list_view, name="manage_list"),
    path("manage/<int:ticket_id>/", views.ticket_manage_detail_view, name="manage_detail"),
    path("<int:ticket_id>/", views.ticket_detail_view, name="detail"),
]
