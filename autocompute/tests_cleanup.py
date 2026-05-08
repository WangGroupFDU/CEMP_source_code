import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from autocompute import media_cleanup
from autocompute.models import ComputationTask, ComputeTask


class MediaCleanupServiceTests(TestCase):

    def setUp(self):
        self.temp_media_root = tempfile.mkdtemp(prefix="cemp_media_cleanup_")
        self.override = override_settings(MEDIA_ROOT=self.temp_media_root)
        self.override.enable()
        self.user = get_user_model().objects.create_user(
            username="cleanup_user",
            password="testpass123",
            email="user@example.com",
        )

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.temp_media_root, ignore_errors=True)

    def test_build_expired_candidates_only_returns_standard_task_dirs(self):

        old_folder = "20240101_010203_expiredabc"
        new_folder = "20260401_010203_recentabc"
        invalid_folder = "manual_backup_folder"

        (Path(self.temp_media_root) / "AutoCompute" / "QcCompute" / "Downloads" / old_folder).mkdir(parents=True)
        (Path(self.temp_media_root) / "AutoCompute" / "QcCompute" / "Downloads" / new_folder).mkdir(parents=True)
        (Path(self.temp_media_root) / "AutoCompute" / "QcCompute" / "Downloads" / invalid_folder).mkdir(parents=True)
        (Path(self.temp_media_root) / "Polymer" / "Database_full" / old_folder).mkdir(parents=True)

        now = timezone.make_aware(datetime(2026, 4, 7, 12, 0, 0), timezone.get_current_timezone())
        candidates = media_cleanup.build_expired_candidates(days=60, now=now)
        candidate_names = {candidate.folder_name for candidate in candidates}

        self.assertIn(old_folder, candidate_names)
        self.assertNotIn(new_folder, candidate_names)
        self.assertNotIn(invalid_folder, candidate_names)

    @mock.patch("autocompute.media_cleanup.delete_remote_directory")
    @mock.patch("autocompute.media_cleanup.terminate_remote_processes")
    @mock.patch("autocompute.media_cleanup.terminate_local_process")
    @mock.patch("autocompute.media_cleanup._load_remote_server_pool")
    def test_cleanup_active_expired_task_marks_failed_and_deletes_directory(
        self,
        mock_load_remote_server_pool,
        mock_terminate_local_process,
        mock_terminate_remote_processes,
        mock_delete_remote_directory,
    ):

        folder_name = "20240101_010203_expiredactive"
        local_dir = Path(self.temp_media_root) / "AutoCompute" / "QcCompute" / "Downloads" / folder_name
        local_dir.mkdir(parents=True)
        (local_dir / "dummy.txt").write_text("stale", encoding="utf-8")

        compute_task = ComputeTask.objects.create(
            user=self.user,
            task_type="HTQC_single_point_energy",
            task_id="compute-stale-task",
            folder_path=str(local_dir),
            status="pending",
            pid=12345,
            remote_type="remote",
            server_name="AMD9654_supervisor_node",
        )
        legacy_task = ComputationTask.objects.create(
            user=self.user,
            status="RUNNING",
            upload_file_path=str(local_dir / "input.xlsx"),
            download_file_path=str(local_dir / "result.xlsx"),
            progress=0.5,
        )

        mock_load_remote_server_pool.return_value = [
            {
                "server_name": "AMD9654_supervisor_node",
                "IP": "user@<PRIVATE_HOST>:",
                "task_limit": 9,
                "remote_target_dir": "/path/to/example",
                "order": 0,
            }
        ]
        mock_terminate_local_process.return_value = {"status": "terminated", "success": True, "error": ""}
        mock_terminate_remote_processes.return_value = {
            "status": "terminated",
            "success": True,
            "error": "",
            "stdout": "",
            "stderr": "",
        }
        mock_delete_remote_directory.return_value = {
            "status": "deleted",
            "success": True,
            "error": "",
            "stdout": "",
            "stderr": "",
        }

        now = timezone.make_aware(datetime(2026, 4, 7, 12, 0, 0), timezone.get_current_timezone())
        results = media_cleanup.cleanup_expired_task_directories(days=60, now=now)

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertFalse(result["error"])
        self.assertEqual(result["local_delete_status"]["status"], "deleted")
        self.assertFalse(local_dir.exists())

        compute_task.refresh_from_db()
        legacy_task.refresh_from_db()
        self.assertEqual(compute_task.status, "failed")
        self.assertEqual(compute_task.pid, None)
        self.assertIn(media_cleanup.EXPIRED_CLEANUP_REASON, compute_task.status_message)
        self.assertEqual(legacy_task.status, "FAILED")
        self.assertIn(media_cleanup.EXPIRED_CLEANUP_REASON, legacy_task.error_message)

        mock_delete_remote_directory.assert_called_once()
        remote_delete_call = mock_delete_remote_directory.call_args[0]
        self.assertEqual(remote_delete_call[0], "user@<PRIVATE_HOST>")
        self.assertEqual(
            remote_delete_call[1],
            f"/path/to/example/AutoCompute/QcCompute/Downloads/{folder_name}",
        )

    @mock.patch("autocompute.media_cleanup.delete_remote_directory")
    @mock.patch("autocompute.media_cleanup._load_remote_server_pool")
    def test_cleanup_remote_delete_failure_keeps_local_directory(
        self,
        mock_load_remote_server_pool,
        mock_delete_remote_directory,
    ):

        folder_name = "20240101_010203_remotefail"
        local_dir = Path(self.temp_media_root) / "AutoCompute" / "MDCompute" / "Downloads" / folder_name
        local_dir.mkdir(parents=True)

        mock_load_remote_server_pool.return_value = [
            {
                "server_name": "AMD9654_supervisor_node",
                "IP": "user@<PRIVATE_HOST>:",
                "task_limit": 9,
                "remote_target_dir": "/path/to/example",
                "order": 0,
            }
        ]
        mock_delete_remote_directory.return_value = {
            "status": "error",
            "success": False,
            "error": "ssh failed",
            "stdout": "",
            "stderr": "ssh failed",
        }

        now = timezone.make_aware(datetime(2026, 4, 7, 12, 0, 0), timezone.get_current_timezone())
        results = media_cleanup.cleanup_expired_task_directories(days=60, now=now)

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIn("远端目录删除失败", result["error"])
        self.assertTrue(local_dir.exists())

    def test_cleanup_non_mirrored_root_only_deletes_local_directory(self):

        folder_name = "20240101_010203_uploadstale"
        local_dir = Path(self.temp_media_root) / "AutoCompute" / "QcCompute" / "Uploads" / folder_name
        local_dir.mkdir(parents=True)
        (local_dir / "input.xlsx").write_text("xlsx", encoding="utf-8")

        now = timezone.make_aware(datetime(2026, 4, 7, 12, 0, 0), timezone.get_current_timezone())
        results = media_cleanup.cleanup_expired_task_directories(days=60, now=now)

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertFalse(result["remote_delete_status"])
        self.assertEqual(result["local_delete_status"]["status"], "deleted")
        self.assertFalse(local_dir.exists())
