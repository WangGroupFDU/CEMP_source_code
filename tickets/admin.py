from functools import partial

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.forms import Textarea
from django.urls import reverse

from .models import Ticket, TicketMessage
from .services import (
    create_staff_reply,
    send_staff_reply_notification,
    ticket_email_notifications_enabled,
)


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1
    can_delete = False
    fields = (
        "author",
        "author_role",
        "content",
        "created_at",
        "notify_user",
        "email_delivery_status",
        "email_sent_at",
        "email_error",
    )
    readonly_fields = (
        "author",
        "author_role",
        "created_at",
        "email_delivery_status",
        "email_sent_at",
        "email_error",
    )
    formfield_overrides = {
        TicketMessage._meta.get_field("content").__class__: {
            "widget": Textarea(attrs={"rows": 4, "cols": 80})
        }
    }

    def get_extra(self, request, obj=None, **kwargs):

        return 1 if obj else 0


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "creator",
        "category",
        "priority",
        "status",
        "last_reply_at",
        "updated_at",
    )
    list_filter = ("status", "category", "priority", "updated_at")
    search_fields = ("subject", "creator__username", "creator__email")
    ordering = ("-updated_at", "-created_at")
    readonly_fields = ("created_at", "updated_at", "last_reply_at", "closed_at")
    inlines = [TicketMessageInline]
    actions = ["retry_reply_email"]

    def changelist_view(self, request, extra_context=None):

        if request.GET.get("native") == "1":
            return super().changelist_view(request, extra_context=extra_context)
        return redirect(reverse("tickets:manage_list"))

    def change_view(self, request, object_id, form_url="", extra_context=None):

        if request.GET.get("native") == "1":
            return super().change_view(
                request,
                object_id,
                form_url=form_url,
                extra_context=extra_context,
            )
        return redirect(reverse("tickets:manage_detail", kwargs={"ticket_id": object_id}))

    def has_add_permission(self, request):

        return False

    def save_model(self, request, obj, form, change):

        obj.sync_closed_at()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):

        instances = formset.save(commit=False)
        for deleted_obj in formset.deleted_objects:
            deleted_obj.delete()

        ticket = form.instance

        for instance in instances:
            is_new = instance.pk is None
            if isinstance(instance, TicketMessage):
                if is_new:
                    create_staff_reply(
                        ticket=ticket,
                        author=request.user,
                        content=instance.content,
                    )
                else:
                    instance.save()
            else:
                instance.save()

        formset.save_m2m()

    @admin.action(description="Retry sending staff reply email")
    def retry_reply_email(self, request, queryset):

        if not ticket_email_notifications_enabled():
            self.message_user(
                request,
                "Ticket email notifications are currently disabled. Replies are only updated inside CEMP pages.",
                level=messages.INFO,
            )
            return

        pending_messages = TicketMessage.objects.filter(
            ticket__in=queryset,
            author_role=TicketMessage.AUTHOR_STAFF,
            notify_user=True,
        ).exclude(email_delivery_status=TicketMessage.EMAIL_SENT)

        total = pending_messages.count()
        if total == 0:
            self.message_user(
                request,
                "No pending or failed staff reply emails were found for the selected tickets.",
                level=messages.INFO,
            )
            return

        success_count = 0
        failure_count = 0
        for message_obj in pending_messages:
            success, _ = send_staff_reply_notification(message_obj.pk)
            if success:
                success_count += 1
            else:
                failure_count += 1

        level = messages.SUCCESS if failure_count == 0 else messages.WARNING
        self.message_user(
            request,
            f"Retried {total} reply emails: {success_count} succeeded, {failure_count} failed.",
            level=level,
        )
