from functools import partial
import logging
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.db import close_old_connections, transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .models import Ticket, TicketMessage


logger = logging.getLogger("django")


def ticket_email_notifications_enabled():

    return getattr(settings, "TICKETS_ENABLE_EMAIL_NOTIFICATIONS", False)


def build_ticket_detail_url(ticket):

    detail_path = reverse("tickets:detail", kwargs={"ticket_id": ticket.pk})
    site_domain = getattr(settings, "SITE_DOMAIN", "").rstrip("/")
    if site_domain:
        return f"{site_domain}{detail_path}"
    return detail_path


def send_ticket_created_confirmation(ticket_id):

    ticket = Ticket.objects.select_related("creator").get(pk=ticket_id)
    if not ticket.creator.email:
        return False, "Ticket creator does not have an email address."

    context = {
        "ticket": ticket,
        "detail_url": build_ticket_detail_url(ticket),
    }
    subject = f"[CEMP] Ticket #{ticket.pk} has been received"
    message = render_to_string("tickets/emails/ticket_created.txt", context)

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [ticket.creator.email],
            fail_silently=False,
        )
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _run_email_job(func, *args):

    if not ticket_email_notifications_enabled():
        return

    def _runner():
        close_old_connections()
        try:
            success, error_message = func(*args)
            if not success and error_message:
                logger.warning(
                    "Ticket email task %s failed: %s",
                    getattr(func, "__name__", str(func)),
                    error_message,
                )
        except Exception:
            logger.exception(
                "Unexpected exception while executing ticket email task %s",
                getattr(func, "__name__", str(func)),
            )
        finally:
            close_old_connections()

    if getattr(settings, "TICKETS_EMAIL_ASYNC", True):
        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        return

    _runner()


def send_staff_reply_notification(message_id):

    message = TicketMessage.objects.select_related(
        "ticket",
        "ticket__creator",
        "author",
    ).get(pk=message_id)

    if message.author_role != TicketMessage.AUTHOR_STAFF or not message.notify_user:
        TicketMessage.objects.filter(pk=message.pk).update(
            email_delivery_status=TicketMessage.EMAIL_NOT_APPLICABLE,
            email_error="",
        )
        return False, "Notification is not applicable for this message."

    recipient = message.ticket.creator.email
    if not recipient:
        TicketMessage.objects.filter(pk=message.pk).update(
            email_delivery_status=TicketMessage.EMAIL_FAILED,
            email_error="Ticket creator does not have an email address.",
            email_sent_at=None,
        )
        return False, "Ticket creator does not have an email address."

    context = {
        "ticket": message.ticket,
        "message": message,
        "detail_url": build_ticket_detail_url(message.ticket),
    }
    subject = f"[CEMP] New reply for Ticket #{message.ticket.pk}"
    body = render_to_string("tickets/emails/ticket_staff_reply.txt", context)

    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )
        TicketMessage.objects.filter(pk=message.pk).update(
            email_delivery_status=TicketMessage.EMAIL_SENT,
            email_sent_at=timezone.now(),
            email_error="",
        )
        return True, ""
    except Exception as exc:
        TicketMessage.objects.filter(pk=message.pk).update(
            email_delivery_status=TicketMessage.EMAIL_FAILED,
            email_sent_at=None,
            email_error=str(exc),
        )
        return False, str(exc)


def enqueue_ticket_created_confirmation(ticket_id):

    _run_email_job(send_ticket_created_confirmation, ticket_id)


def enqueue_staff_reply_notification(message_id):

    _run_email_job(send_staff_reply_notification, message_id)


def create_staff_reply(ticket, author, content):

    reply_time = timezone.now()
    email_enabled = ticket_email_notifications_enabled()
    message = TicketMessage.objects.create(
        ticket=ticket,
        author=author,
        author_role=TicketMessage.AUTHOR_STAFF,
        content=content,
        notify_user=email_enabled,
        email_delivery_status=(
            TicketMessage.EMAIL_PENDING
            if email_enabled
            else TicketMessage.EMAIL_NOT_APPLICABLE
        ),
        email_sent_at=None,
        email_error="",
    )

    if ticket.status not in [Ticket.STATUS_RESOLVED, Ticket.STATUS_CLOSED]:
        ticket.mark_waiting_user(reply_time=reply_time)
    else:
        ticket.last_reply_at = reply_time
        ticket.sync_closed_at()

    ticket.save(update_fields=["status", "last_reply_at", "closed_at", "updated_at"])
    if email_enabled:
        transaction.on_commit(partial(enqueue_staff_reply_notification, message.pk))
    return message
