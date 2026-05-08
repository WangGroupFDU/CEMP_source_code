from django.conf import settings
from django.db import models
from django.utils import timezone


class Ticket(models.Model):

    CATEGORY_FEEDBACK = "feedback"
    CATEGORY_BUG = "bug"
    CATEGORY_QUESTION = "question"
    CATEGORY_FEATURE_REQUEST = "feature_request"
    CATEGORY_CHOICES = [
        (CATEGORY_FEEDBACK, "Feedback"),
        (CATEGORY_BUG, "Bug"),
        (CATEGORY_QUESTION, "Question"),
        (CATEGORY_FEATURE_REQUEST, "Feature Request"),
    ]

    STATUS_OPEN = "open"
    STATUS_WAITING_STAFF = "waiting_staff"
    STATUS_WAITING_USER = "waiting_user"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_WAITING_STAFF, "Waiting Staff"),
        (STATUS_WAITING_USER, "Waiting User"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_CLOSED, "Closed"),
    ]

    PRIORITY_LOW = "low"
    PRIORITY_NORMAL = "normal"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_NORMAL, "Normal"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    ]

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
        verbose_name="Creator",
    )
    subject = models.CharField(max_length=200, verbose_name="Subject")
    category = models.CharField(
        max_length=32,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_FEEDBACK,
        verbose_name="Category",
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
        verbose_name="Status",
    )
    priority = models.CharField(
        max_length=16,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_NORMAL,
        verbose_name="Priority",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    last_reply_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Reply At",
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Closed At",
    )

    class Meta:
        ordering = ["-updated_at", "-created_at"]
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self):
        return f"#{self.pk} {self.subject}"

    def get_status_presentation(self, for_staff=False):

        if self.status == self.STATUS_CLOSED:
            return {
                "label": "Closed",
                "tone": "closed",
                "help_text": "This ticket has been closed and cannot accept new messages.",
            }

        if for_staff:
            if self.status in {self.STATUS_WAITING_USER, self.STATUS_RESOLVED}:
                return {
                    "label": "Waiting",
                    "tone": "waiting",
                    "help_text": "Waiting for the user to confirm or provide more details.",
                }
            if self.status in {self.STATUS_OPEN, self.STATUS_WAITING_STAFF}:
                return {
                    "label": "Completed",
                    "tone": "completed",
                    "help_text": "The user has already responded. Staff can review the latest message.",
                }
        else:
            if self.status in {self.STATUS_OPEN, self.STATUS_WAITING_STAFF}:
                return {
                    "label": "Waiting",
                    "tone": "waiting",
                    "help_text": "Waiting for staff to review and reply.",
                }
            if self.status in {self.STATUS_WAITING_USER, self.STATUS_RESOLVED}:
                return {
                    "label": "Completed",
                    "tone": "completed",
                    "help_text": "Staff has replied. You can close the ticket or continue only if needed.",
                }

        return {
            "label": "Waiting",
            "tone": "waiting",
            "help_text": "This ticket is waiting for the next update.",
        }

    def mark_waiting_staff(self, reply_time=None):

        reply_time = reply_time or timezone.now()
        self.status = self.STATUS_WAITING_STAFF
        self.last_reply_at = reply_time
        if self.closed_at is not None:
            self.closed_at = None

    def mark_waiting_user(self, reply_time=None):

        reply_time = reply_time or timezone.now()
        self.status = self.STATUS_WAITING_USER
        self.last_reply_at = reply_time
        if self.closed_at is not None:
            self.closed_at = None

    def sync_closed_at(self):

        if self.status == self.STATUS_CLOSED:
            if self.closed_at is None:
                self.closed_at = timezone.now()
        else:
            self.closed_at = None

    def mark_closed(self, close_time=None):

        close_time = close_time or timezone.now()
        self.status = self.STATUS_CLOSED
        self.closed_at = close_time
        if self.last_reply_at is None:
            self.last_reply_at = close_time


class TicketMessage(models.Model):

    AUTHOR_USER = "user"
    AUTHOR_STAFF = "staff"
    AUTHOR_ROLE_CHOICES = [
        (AUTHOR_USER, "User"),
        (AUTHOR_STAFF, "Staff"),
    ]

    EMAIL_NOT_APPLICABLE = "not_applicable"
    EMAIL_PENDING = "pending"
    EMAIL_SENT = "sent"
    EMAIL_FAILED = "failed"
    EMAIL_DELIVERY_CHOICES = [
        (EMAIL_NOT_APPLICABLE, "Not Applicable"),
        (EMAIL_PENDING, "Pending"),
        (EMAIL_SENT, "Sent"),
        (EMAIL_FAILED, "Failed"),
    ]

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Ticket",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ticket_messages",
        verbose_name="Author",
    )
    author_role = models.CharField(
        max_length=16,
        choices=AUTHOR_ROLE_CHOICES,
        verbose_name="Author Role",
    )
    content = models.TextField(verbose_name="Content")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    notify_user = models.BooleanField(default=False, verbose_name="Notify User")
    email_delivery_status = models.CharField(
        max_length=20,
        choices=EMAIL_DELIVERY_CHOICES,
        default=EMAIL_NOT_APPLICABLE,
        verbose_name="Email Delivery Status",
    )
    email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Email Sent At",
    )
    email_error = models.TextField(blank=True, verbose_name="Email Error")

    class Meta:
        ordering = ["created_at", "pk"]
        verbose_name = "Ticket Message"
        verbose_name_plural = "Ticket Messages"

    def __str__(self):
        return f"Ticket #{self.ticket_id} message #{self.pk}"
