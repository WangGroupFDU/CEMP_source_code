from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import RequestFactory
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.admin.sites import AdminSite

from .admin import TicketAdmin
from .models import Ticket, TicketMessage


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SITE_DOMAIN="https://example.com",
    ROOT_URLCONF="cemp.test_urls",
)
class TicketViewsTests(TestCase):

    def setUp(self):

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="ticket_user",
            email="user@example.com",
            password="Pass1234!",
        )
        self.other_user = user_model.objects.create_user(
            username="other_user",
            email="user@example.com",
            password="Pass1234!",
        )
        self.admin_user = user_model.objects.create_superuser(
            username="ticket_admin",
            email="user@example.com",
            password="Pass1234!",
        )
        self.request_factory = RequestFactory()

    def test_login_required_for_ticket_pages(self):
        self.assertEqual(self.client.get(reverse("tickets:list")).status_code, 302)
        self.assertEqual(self.client.get(reverse("tickets:create")).status_code, 302)
        self.assertEqual(self.client.get(reverse("tickets:manage_list")).status_code, 302)
        self.assertEqual(
            self.client.get(reverse("tickets:manage_detail", kwargs={"ticket_id": 1})).status_code,
            302,
        )

    def test_create_ticket_writes_first_message(self):
        self.client.login(username="ticket_user", password="Pass1234!")
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("tickets:create"),
                data={
                    "subject": "Need support for query page",
                    "category": Ticket.CATEGORY_FEEDBACK,
                    "priority": Ticket.PRIORITY_NORMAL,
                    "content": "I have a suggestion for the query page.",
                },
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(TicketMessage.objects.count(), 1)

        ticket = Ticket.objects.get()
        message = TicketMessage.objects.get()
        self.assertEqual(ticket.creator, self.user)
        self.assertEqual(ticket.status, Ticket.STATUS_WAITING_STAFF)
        self.assertEqual(message.author_role, TicketMessage.AUTHOR_USER)
        self.assertEqual(message.content, "I have a suggestion for the query page.")
        self.assertEqual(len(mail.outbox), 0)

    def test_user_cannot_access_other_users_ticket(self):
        ticket = Ticket.objects.create(
            creator=self.user,
            subject="Private ticket",
            category=Ticket.CATEGORY_QUESTION,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_STAFF,
        )
        self.client.login(username="other_user", password="Pass1234!")
        response = self.client.get(
            reverse("tickets:detail", kwargs={"ticket_id": ticket.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_user_reply_switches_ticket_back_to_waiting_staff(self):
        ticket = Ticket.objects.create(
            creator=self.user,
            subject="Need follow-up",
            category=Ticket.CATEGORY_BUG,
            priority=Ticket.PRIORITY_HIGH,
            status=Ticket.STATUS_WAITING_USER,
        )
        TicketMessage.objects.create(
            ticket=ticket,
            author=self.admin_user,
            author_role=TicketMessage.AUTHOR_STAFF,
            content="Please provide more details.",
            notify_user=True,
            email_delivery_status=TicketMessage.EMAIL_SENT,
        )

        self.client.login(username="ticket_user", password="Pass1234!")
        response = self.client.post(
            reverse("tickets:detail", kwargs={"ticket_id": ticket.pk}),
            data={"content": "Here are the missing details."},
            follow=True,
        )

        ticket.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ticket.status, Ticket.STATUS_WAITING_STAFF)
        self.assertEqual(ticket.messages.count(), 2)
        self.assertEqual(ticket.messages.last().author_role, TicketMessage.AUTHOR_USER)

    def test_user_status_labels_are_clear_in_ticket_list(self):
        waiting_ticket = Ticket.objects.create(
            creator=self.user,
            subject="Waiting for staff",
            category=Ticket.CATEGORY_FEEDBACK,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_STAFF,
        )
        completed_ticket = Ticket.objects.create(
            creator=self.user,
            subject="Staff completed reply",
            category=Ticket.CATEGORY_FEEDBACK,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_USER,
        )
        closed_ticket = Ticket.objects.create(
            creator=self.user,
            subject="Closed ticket",
            category=Ticket.CATEGORY_FEEDBACK,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_CLOSED,
        )

        self.client.login(username="ticket_user", password="Pass1234!")
        response = self.client.get(reverse("tickets:list"))

        status_map = {
            ticket.subject: ticket.status_presentation["label"]
            for ticket in response.context["tickets"]
            if ticket.pk in {waiting_ticket.pk, completed_ticket.pk, closed_ticket.pk}
        }
        self.assertEqual(status_map["Waiting for staff"], "Waiting")
        self.assertEqual(status_map["Staff completed reply"], "Completed")
        self.assertEqual(status_map["Closed ticket"], "Closed")

    def test_user_can_close_ticket_and_stop_new_replies(self):
        ticket = Ticket.objects.create(
            creator=self.user,
            subject="Close by user",
            category=Ticket.CATEGORY_QUESTION,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_USER,
        )

        self.client.login(username="ticket_user", password="Pass1234!")
        response = self.client.post(
            reverse("tickets:detail", kwargs={"ticket_id": ticket.pk}),
            data={"action": "close"},
            follow=True,
        )

        ticket.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ticket.status, Ticket.STATUS_CLOSED)
        self.assertIsNotNone(ticket.closed_at)
        self.assertContains(response, "Ticket #")
        self.assertContains(response, "Closed")
        self.assertContains(response, "cannot accept new messages")

    def test_admin_reply_inline_updates_status_without_email(self):
        ticket = Ticket.objects.create(
            creator=self.user,
            subject="Admin flow",
            category=Ticket.CATEGORY_QUESTION,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_STAFF,
        )
        TicketMessage.objects.create(
            ticket=ticket,
            author=self.user,
            author_role=TicketMessage.AUTHOR_USER,
            content="Please help me.",
            notify_user=False,
            email_delivery_status=TicketMessage.EMAIL_NOT_APPLICABLE,
        )

        self.client.login(username="ticket_admin", password="Pass1234!")
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                f"{reverse('admin:tickets_ticket_change', args=[ticket.pk])}?native=1",
                data={
                    "creator": str(ticket.creator_id),
                    "subject": ticket.subject,
                    "category": ticket.category,
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "messages-TOTAL_FORMS": "2",
                    "messages-INITIAL_FORMS": "1",
                    "messages-MIN_NUM_FORMS": "0",
                    "messages-MAX_NUM_FORMS": "1000",
                    "messages-0-id": str(ticket.messages.first().pk),
                    "messages-0-ticket": str(ticket.pk),
                    "messages-0-content": ticket.messages.first().content,
                    "messages-0-notify_user": "",
                    "messages-1-id": "",
                    "messages-1-ticket": str(ticket.pk),
                    "messages-1-content": "This is the maintainer reply.",
                    "messages-1-notify_user": "on",
                    "_save": "Save",
                },
                follow=True,
            )

        ticket.refresh_from_db()
        staff_message = ticket.messages.order_by("created_at").last()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ticket.status, Ticket.STATUS_WAITING_USER)
        self.assertEqual(staff_message.author_role, TicketMessage.AUTHOR_STAFF)
        self.assertEqual(
            staff_message.email_delivery_status,
            TicketMessage.EMAIL_NOT_APPLICABLE,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_retry_reply_email_action_skips_when_email_disabled(self):
        ticket = Ticket.objects.create(
            creator=self.user,
            subject="Retry email",
            category=Ticket.CATEGORY_FEEDBACK,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_USER,
        )
        message = TicketMessage.objects.create(
            ticket=ticket,
            author=self.admin_user,
            author_role=TicketMessage.AUTHOR_STAFF,
            content="Reply should be retried.",
            notify_user=True,
            email_delivery_status=TicketMessage.EMAIL_FAILED,
            email_error="Temporary SMTP failure",
        )

        request = self.request_factory.post("/admin/tickets/ticket/")
        request.user = self.admin_user
        setattr(request, "session", self.client.session)
        setattr(request, "_messages", FallbackStorage(request))
        admin_instance = TicketAdmin(Ticket, AdminSite())
        admin_instance.retry_reply_email(request, Ticket.objects.filter(pk=ticket.pk))

        message.refresh_from_db()
        self.assertEqual(message.email_delivery_status, TicketMessage.EMAIL_FAILED)
        self.assertEqual(len(mail.outbox), 0)

    def test_non_staff_user_cannot_access_manage_pages(self):
        ticket = Ticket.objects.create(
            creator=self.user,
            subject="Private admin panel",
            category=Ticket.CATEGORY_QUESTION,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_STAFF,
        )

        self.client.login(username="ticket_user", password="Pass1234!")
        self.assertEqual(self.client.get(reverse("tickets:manage_list")).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("tickets:manage_detail", kwargs={"ticket_id": ticket.pk})).status_code,
            403,
        )

    def test_staff_manage_list_can_filter_and_search_all_tickets(self):
        Ticket.objects.create(
            creator=self.user,
            subject="Autocompute bug report",
            category=Ticket.CATEGORY_BUG,
            priority=Ticket.PRIORITY_HIGH,
            status=Ticket.STATUS_WAITING_STAFF,
        )
        Ticket.objects.create(
            creator=self.other_user,
            subject="Feature request for database",
            category=Ticket.CATEGORY_FEATURE_REQUEST,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_USER,
        )

        self.client.login(username="ticket_admin", password="Pass1234!")
        response = self.client.get(
            reverse("tickets:manage_list"),
            data={"status": Ticket.STATUS_WAITING_STAFF, "q": "ticket_user"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Autocompute bug report")
        self.assertNotContains(response, "Feature request for database")

    def test_staff_status_labels_are_reversed_in_manage_list(self):
        user_replied_ticket = Ticket.objects.create(
            creator=self.user,
            subject="User already replied",
            category=Ticket.CATEGORY_BUG,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_STAFF,
        )
        waiting_user_ticket = Ticket.objects.create(
            creator=self.user,
            subject="Waiting for user reply",
            category=Ticket.CATEGORY_QUESTION,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_USER,
        )

        self.client.login(username="ticket_admin", password="Pass1234!")
        response = self.client.get(reverse("tickets:manage_list"))

        status_map = {
            ticket.subject: ticket.status_presentation["label"]
            for ticket in response.context["tickets"]
            if ticket.pk in {user_replied_ticket.pk, waiting_user_ticket.pk}
        }
        self.assertEqual(status_map["User already replied"], "Completed")
        self.assertEqual(status_map["Waiting for user reply"], "Waiting")

    def test_staff_manage_detail_reply_creates_staff_message(self):
        ticket = Ticket.objects.create(
            creator=self.user,
            subject="Dedicated reply page",
            category=Ticket.CATEGORY_QUESTION,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_STAFF,
        )
        TicketMessage.objects.create(
            ticket=ticket,
            author=self.user,
            author_role=TicketMessage.AUTHOR_USER,
            content="I need a stable admin reply page.",
            notify_user=False,
            email_delivery_status=TicketMessage.EMAIL_NOT_APPLICABLE,
        )

        self.client.login(username="ticket_admin", password="Pass1234!")
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("tickets:manage_detail", kwargs={"ticket_id": ticket.pk}),
                data={"content": "This issue will now be handled in the dedicated page."},
                follow=True,
            )

        ticket.refresh_from_db()
        latest_message = ticket.messages.order_by("created_at").last()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ticket.status, Ticket.STATUS_WAITING_USER)
        self.assertEqual(latest_message.author_role, TicketMessage.AUTHOR_STAFF)
        self.assertEqual(
            latest_message.email_delivery_status,
            TicketMessage.EMAIL_NOT_APPLICABLE,
        )
        self.assertContains(response, "Reply to Ticket")
        self.assertEqual(len(mail.outbox), 0)

    def test_staff_can_close_ticket_from_manage_page(self):
        ticket = Ticket.objects.create(
            creator=self.user,
            subject="Close by staff",
            category=Ticket.CATEGORY_QUESTION,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_STAFF,
        )

        self.client.login(username="ticket_admin", password="Pass1234!")
        response = self.client.post(
            reverse("tickets:manage_detail", kwargs={"ticket_id": ticket.pk}),
            data={"action": "close"},
            follow=True,
        )

        ticket.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ticket.status, Ticket.STATUS_CLOSED)
        self.assertIsNotNone(ticket.closed_at)
        self.assertContains(response, "Closed")
        self.assertContains(response, "read-only")

    def test_admin_ticket_urls_redirect_to_manage_pages(self):
        ticket = Ticket.objects.create(
            creator=self.user,
            subject="Admin redirect",
            category=Ticket.CATEGORY_FEEDBACK,
            priority=Ticket.PRIORITY_NORMAL,
            status=Ticket.STATUS_WAITING_STAFF,
        )

        self.client.login(username="ticket_admin", password="Pass1234!")
        changelist_response = self.client.get(reverse("admin:tickets_ticket_changelist"))
        change_response = self.client.get(reverse("admin:tickets_ticket_change", args=[ticket.pk]))

        self.assertEqual(changelist_response.status_code, 302)
        self.assertEqual(changelist_response.url, reverse("tickets:manage_list"))
        self.assertEqual(change_response.status_code, 302)
        self.assertEqual(
            change_response.url,
            reverse("tickets:manage_detail", kwargs={"ticket_id": ticket.pk}),
        )
