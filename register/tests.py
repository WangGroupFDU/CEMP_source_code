from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from autocompute.models import ComputeTask
from register.models import UserProfile


class UserProfileAdminViewTests(TestCase):

    def setUp(self):

        self.staff_user = User.objects.create_user(
            username="staff_admin",
            email="user@example.com",
            password="test-pass-123",
            is_staff=True,
            is_superuser=True,
        )
        self.normal_user = User.objects.create_user(
            username="normal_user",
            email="user@example.com",
            password="test-pass-123",
        )
        self.target_user = User.objects.create_user(
            username="target_user",
            email="user@example.com",
            password="test-pass-123",
        )
        self.second_target = User.objects.create_user(
            username="second_target",
            email="user@example.com",
            password="test-pass-123",
        )

        self.target_profile = self.target_user.userprofile
        self.second_profile = self.second_target.userprofile

        self.target_profile.auto_compute_permission = True
        self.target_profile.gaussian_permission = False
        self.target_profile.database_permission = True
        self.target_profile.ml_prediction_permission = False
        self.target_profile.daily_task_limit = 3
        self.target_profile.save()

        self.second_profile.auto_compute_permission = False
        self.second_profile.gaussian_permission = True
        self.second_profile.database_permission = False
        self.second_profile.ml_prediction_permission = True
        self.second_profile.daily_task_limit = 2
        self.second_profile.save()

        ComputeTask.objects.create(
            user=self.target_user,
            task_id="task-001",
            folder_path="/tmp/task-001",
            status="success",
        )
        ComputeTask.objects.create(
            user=self.target_user,
            task_id="task-002",
            folder_path="/tmp/task-002",
            status="failed",
        )

        self.page_url = reverse("register:user_profile_admin")

    def test_login_required_for_permission_page(self):

        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/register/login/", response.url)

    def test_non_staff_user_forbidden(self):

        self.client.login(username="normal_user", password="test-pass-123")
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, 403)

    def test_staff_can_view_stats_and_task_count(self):

        self.client.login(username="staff_admin", password="test-pass-123")
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stats"]["total_users"], 4)
        self.assertEqual(response.context["stats"]["auto_compute_users"], 1)
        profiles = list(response.context["profiles"])
        target_profile = next(profile for profile in profiles if profile.id == self.target_profile.id)
        self.assertEqual(target_profile.task_count, 2)

    def test_search_and_filter_work(self):

        self.client.login(username="staff_admin", password="test-pass-123")
        response = self.client.get(
            self.page_url,
            {
                "q": "target_user",
                "gaussian_permission": "false",
                "auto_compute_permission": "true",
            },
        )
        self.assertEqual(response.status_code, 200)
        profiles = list(response.context["profiles"])
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].user.username, "target_user")

    def test_single_update_persists_changes(self):

        self.client.login(username="staff_admin", password="test-pass-123")
        response = self.client.post(
            self.page_url,
            {
                "action_type": "single_update",
                "profile_id": self.target_profile.id,
                "auto_compute_permission": "",
                "gaussian_permission": "on",
                "database_permission": "on",
                "ml_prediction_permission": "on",
                "daily_task_limit": "8",
                "return_query": "q=target_user",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("q=target_user", response.url)

        self.target_profile.refresh_from_db()
        self.assertFalse(self.target_profile.auto_compute_permission)
        self.assertTrue(self.target_profile.gaussian_permission)
        self.assertTrue(self.target_profile.database_permission)
        self.assertTrue(self.target_profile.ml_prediction_permission)
        self.assertEqual(self.target_profile.daily_task_limit, 8)

    def test_batch_permission_update(self):

        self.client.login(username="staff_admin", password="test-pass-123")
        response = self.client.post(
            self.page_url,
            {
                "action_type": "batch_permission",
                "selected_profiles": [self.target_profile.id, self.second_profile.id],
                "permission_field": "gaussian_permission",
                "permission_value": "disable",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.target_profile.refresh_from_db()
        self.second_profile.refresh_from_db()
        self.assertFalse(self.target_profile.gaussian_permission)
        self.assertFalse(self.second_profile.gaussian_permission)

    def test_batch_daily_limit_update(self):

        self.client.login(username="staff_admin", password="test-pass-123")
        response = self.client.post(
            self.page_url,
            {
                "action_type": "batch_daily_limit",
                "selected_profiles": [self.target_profile.id, self.second_profile.id],
                "batch_daily_task_limit": "6",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.target_profile.refresh_from_db()
        self.second_profile.refresh_from_db()
        self.assertEqual(self.target_profile.daily_task_limit, 6)
        self.assertEqual(self.second_profile.daily_task_limit, 6)

    def test_batch_update_requires_selection(self):

        self.client.login(username="staff_admin", password="test-pass-123")
        response = self.client.post(
            self.page_url,
            {
                "action_type": "batch_permission",
                "permission_field": "database_permission",
                "permission_value": "enable",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please select at least one user")

    def test_admin_changelist_redirects_to_frontend_page(self):

        self.client.login(username="staff_admin", password="test-pass-123")
        response = self.client.get(reverse("admin:register_userprofile_changelist"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.page_url)

    def test_admin_change_redirects_with_focus_profile(self):

        self.client.login(username="staff_admin", password="test-pass-123")
        response = self.client.get(
            reverse("admin:register_userprofile_change", args=[self.target_profile.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{self.page_url}?focus_profile={self.target_profile.id}",
        )

    def test_home_admin_route_redirects_to_new_page(self):

        self.client.login(username="staff_admin", password="test-pass-123")
        response = self.client.get(reverse("home:admin"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.page_url)
