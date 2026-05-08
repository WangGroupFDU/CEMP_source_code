

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(max_length=200, verbose_name="Subject")),
                ("category", models.CharField(choices=[("feedback", "Feedback"), ("bug", "Bug"), ("question", "Question"), ("feature_request", "Feature Request")], default="feedback", max_length=32, verbose_name="Category")),
                ("status", models.CharField(choices=[("open", "Open"), ("waiting_staff", "Waiting Staff"), ("waiting_user", "Waiting User"), ("resolved", "Resolved"), ("closed", "Closed")], default="open", max_length=32, verbose_name="Status")),
                ("priority", models.CharField(choices=[("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")], default="normal", max_length=16, verbose_name="Priority")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                ("last_reply_at", models.DateTimeField(blank=True, null=True, verbose_name="Last Reply At")),
                ("closed_at", models.DateTimeField(blank=True, null=True, verbose_name="Closed At")),
                ("creator", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tickets", to=settings.AUTH_USER_MODEL, verbose_name="Creator")),
            ],
            options={
                "verbose_name": "Ticket",
                "verbose_name_plural": "Tickets",
                "ordering": ["-updated_at", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TicketMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("author_role", models.CharField(choices=[("user", "User"), ("staff", "Staff")], max_length=16, verbose_name="Author Role")),
                ("content", models.TextField(verbose_name="Content")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("notify_user", models.BooleanField(default=False, verbose_name="Notify User")),
                ("email_delivery_status", models.CharField(choices=[("not_applicable", "Not Applicable"), ("pending", "Pending"), ("sent", "Sent"), ("failed", "Failed")], default="not_applicable", max_length=20, verbose_name="Email Delivery Status")),
                ("email_sent_at", models.DateTimeField(blank=True, null=True, verbose_name="Email Sent At")),
                ("email_error", models.TextField(blank=True, verbose_name="Email Error")),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ticket_messages", to=settings.AUTH_USER_MODEL, verbose_name="Author")),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="tickets.ticket", verbose_name="Ticket")),
            ],
            options={
                "verbose_name": "Ticket Message",
                "verbose_name_plural": "Ticket Messages",
                "ordering": ["created_at", "pk"],
            },
        ),
    ]

