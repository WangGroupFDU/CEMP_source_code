from functools import partial

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import StaffTicketReplyForm, TicketCreateForm, TicketReplyForm
from .models import Ticket, TicketMessage
from .services import (
    create_staff_reply,
    enqueue_ticket_created_confirmation,
    ticket_email_notifications_enabled,
)


def _build_base_context(request):

    return {
        "show_admin": bool(request.user.is_staff),
    }


def _attach_ticket_status_presentations(tickets, for_staff=False):

    for ticket in tickets:
        ticket.status_presentation = ticket.get_status_presentation(for_staff=for_staff)
    return tickets


def _require_staff_user(request):

    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to access the ticket management page.")
    return None


@login_required(login_url="/register/login/")
def ticket_list_view(request):

    tickets = (
        Ticket.objects.filter(creator=request.user)
        .prefetch_related("messages")
        .order_by("-updated_at", "-created_at")
    )
    _attach_ticket_status_presentations(tickets, for_staff=False)
    context = {
        **_build_base_context(request),
        "tickets": tickets,
    }
    return render(request, "tickets/ticket_list.html", context)


@login_required(login_url="/register/login/")
def ticket_create_view(request):

    if request.method == "POST":
        form = TicketCreateForm(request.POST)
        if form.is_valid():
            now = timezone.now()
            with transaction.atomic():
                ticket = Ticket.objects.create(
                    creator=request.user,
                    subject=form.cleaned_data["subject"],
                    category=form.cleaned_data["category"],
                    priority=form.cleaned_data["priority"],
                    status=Ticket.STATUS_WAITING_STAFF,
                    last_reply_at=now,
                )
                TicketMessage.objects.create(
                    ticket=ticket,
                    author=request.user,
                    author_role=TicketMessage.AUTHOR_USER,
                    content=form.cleaned_data["content"],
                    notify_user=False,
                    email_delivery_status=TicketMessage.EMAIL_NOT_APPLICABLE,
                )
                if ticket_email_notifications_enabled():
                    transaction.on_commit(
                        partial(enqueue_ticket_created_confirmation, ticket.pk)
                    )

            messages.success(
                request,
                f"Ticket #{ticket.pk} has been created successfully.",
            )
            return redirect("tickets:detail", ticket_id=ticket.pk)
    else:
        form = TicketCreateForm()

    context = {
        **_build_base_context(request),
        "form": form,
    }
    return render(request, "tickets/ticket_form.html", context)


@login_required(login_url="/register/login/")
def ticket_detail_view(request, ticket_id):

    ticket = get_object_or_404(
        Ticket.objects.select_related("creator").prefetch_related("messages__author"),
        pk=ticket_id,
        creator=request.user,
    )
    can_reply = ticket.status != Ticket.STATUS_CLOSED
    can_close = ticket.status != Ticket.STATUS_CLOSED
    status_presentation = ticket.get_status_presentation(for_staff=False)

    if request.method == "POST":
        action = request.POST.get("action", "reply")
        if action == "close":
            if not can_close:
                return HttpResponseForbidden("This ticket has already been closed.")

            close_time = timezone.now()
            with transaction.atomic():
                ticket.mark_closed(close_time=close_time)
                ticket.save(
                    update_fields=["status", "last_reply_at", "closed_at", "updated_at"]
                )

            messages.success(request, f"Ticket #{ticket.pk} has been closed.")
            return redirect("tickets:detail", ticket_id=ticket.pk)
        if not can_reply:
            return HttpResponseForbidden("This ticket has been closed and cannot accept new replies.")

        form = TicketReplyForm(request.POST)
        if form.is_valid():
            reply_time = timezone.now()
            with transaction.atomic():
                TicketMessage.objects.create(
                    ticket=ticket,
                    author=request.user,
                    author_role=TicketMessage.AUTHOR_USER,
                    content=form.cleaned_data["content"],
                    notify_user=False,
                    email_delivery_status=TicketMessage.EMAIL_NOT_APPLICABLE,
                )
                ticket.mark_waiting_staff(reply_time=reply_time)
                ticket.save(
                    update_fields=["status", "last_reply_at", "closed_at", "updated_at"]
                )

            messages.success(request, "Your reply has been added to the ticket.")
            return redirect("tickets:detail", ticket_id=ticket.pk)
    else:
        form = TicketReplyForm()

    context = {
        **_build_base_context(request),
        "ticket": ticket,
        "ticket_messages": ticket.messages.all(),
        "form": form,
        "can_reply": can_reply,
        "can_close": can_close,
        "status_presentation": status_presentation,
    }
    return render(request, "tickets/ticket_detail.html", context)


@login_required(login_url="/register/login/")
def ticket_manage_list_view(request):

    forbidden_response = _require_staff_user(request)
    if forbidden_response is not None:
        return forbidden_response

    tickets = Ticket.objects.select_related("creator").all().order_by("-updated_at", "-created_at")

    selected_status = request.GET.get("status", "").strip()
    selected_category = request.GET.get("category", "").strip()
    selected_priority = request.GET.get("priority", "").strip()
    query = request.GET.get("q", "").strip()

    if selected_status:
        tickets = tickets.filter(status=selected_status)
    if selected_category:
        tickets = tickets.filter(category=selected_category)
    if selected_priority:
        tickets = tickets.filter(priority=selected_priority)
    if query:
        tickets = tickets.filter(
            Q(subject__icontains=query)
            | Q(creator__username__icontains=query)
            | Q(creator__email__icontains=query)
        )
    _attach_ticket_status_presentations(tickets, for_staff=True)

    context = {
        **_build_base_context(request),
        "tickets": tickets,
        "status_choices": Ticket.STATUS_CHOICES,
        "category_choices": Ticket.CATEGORY_CHOICES,
        "priority_choices": Ticket.PRIORITY_CHOICES,
        "selected_status": selected_status,
        "selected_category": selected_category,
        "selected_priority": selected_priority,
        "query": query,
    }
    return render(request, "tickets/ticket_manage_list.html", context)


@login_required(login_url="/register/login/")
def ticket_manage_detail_view(request, ticket_id):

    forbidden_response = _require_staff_user(request)
    if forbidden_response is not None:
        return forbidden_response

    ticket = get_object_or_404(
        Ticket.objects.select_related("creator").prefetch_related("messages__author"),
        pk=ticket_id,
    )
    can_reply = ticket.status != Ticket.STATUS_CLOSED
    can_close = ticket.status != Ticket.STATUS_CLOSED
    status_presentation = ticket.get_status_presentation(for_staff=True)

    if request.method == "POST":
        action = request.POST.get("action", "reply")
        if action == "close":
            if not can_close:
                return HttpResponseForbidden("This ticket has already been closed.")

            close_time = timezone.now()
            with transaction.atomic():
                ticket.mark_closed(close_time=close_time)
                ticket.save(
                    update_fields=["status", "last_reply_at", "closed_at", "updated_at"]
                )

            messages.success(request, f"Ticket #{ticket.pk} has been closed.")
            return redirect("tickets:manage_detail", ticket_id=ticket.pk)
        if not can_reply:
            return HttpResponseForbidden("This ticket has been closed and cannot accept new replies.")

        form = StaffTicketReplyForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                create_staff_reply(
                    ticket=ticket,
                    author=request.user,
                    content=form.cleaned_data["content"],
                )

            messages.success(request, f"Reply to Ticket #{ticket.pk} has been submitted successfully.")
            return redirect("tickets:manage_detail", ticket_id=ticket.pk)
    else:
        form = StaffTicketReplyForm()

    context = {
        **_build_base_context(request),
        "ticket": ticket,
        "ticket_messages": ticket.messages.all(),
        "form": form,
        "can_reply": can_reply,
        "can_close": can_close,
        "status_presentation": status_presentation,
    }
    return render(request, "tickets/ticket_manage_detail.html", context)
