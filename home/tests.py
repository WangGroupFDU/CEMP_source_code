import json
import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from PIL import Image

from autocompute.failure_utils import DEFAULT_FAILURE_CONTENT
from autocompute.models import ComputeTask
from home.md_previews import build_md_preview_manifest
from home.views import cipher_suite


@override_settings(ROOT_URLCONF="home.urls")
class CheckTaskStatusPreviewTests(TestCase):

    def setUp(self):

        self.temp_dir = tempfile.mkdtemp(prefix="cemp_md_preview_")
        self.override = override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL="/media/")
        self.override.enable()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="md_preview_user",
            password="testpass123",
            email="user@example.com",
        )
        self.client.force_login(self.user)

    def tearDown(self):

        self.override.disable()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_md_preview_manifest_selects_expected_files_and_converts_tiff(self):

        task_dir = self._create_md_task_directory("helper_case")
        self._write_rgb_tiff(task_dir / "Li_atomcharge_rdf+cn.tif", (255, 0, 0))
        self._write_gif(task_dir / "animation_Li_O.gif", (0, 255, 0))
        self._write_png(task_dir / "coordination_polar.png", (0, 0, 255))
        self._write_rgb_tiff(task_dir / "Na_component.tif", (120, 120, 120))

        previews = build_md_preview_manifest(str(task_dir), force_rebuild=True)

        self.assertEqual(
            [item["label"] for item in previews],
            [
                "RDF and CN for atom",
                "Coordination environment",
                "Coordination polar map",
            ],
        )
        self.assertTrue(previews[0]["url"].endswith("/query_previews/Li_atomcharge_rdf+cn.png"))
        self.assertTrue(previews[1]["url"].endswith("/animation_Li_O.gif"))
        self.assertTrue(previews[2]["url"].endswith("/coordination_polar.png"))
        self.assertFalse(any("component" in item["source_filename"] for item in previews))
        self.assertTrue((task_dir / "query_previews" / "Li_atomcharge_rdf+cn.png").exists())

    def test_check_task_status_returns_md_previews_and_legacy_dict(self):

        encrypted_id, task_dir = self._create_md_task(
            folder_name="md_success_case",
            image_specs=[
                ("snapshot.tif", "tiff", (200, 10, 10)),
                ("coordination_polar.png", "png", (10, 200, 10)),
                ("Li_component.tif", "tiff", (10, 10, 200)),
            ],
        )

        manifest_path = task_dir / "query_previews" / "manifest.json"
        self.assertFalse(manifest_path.exists())

        response = self.client.post(
            "/api/check_task_status/",
            data=json.dumps({"encrypted_id": encrypted_id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["task_type"], "MDCoumpute")
        self.assertIn("figure_previews", payload)
        self.assertIn("figure_data_url_dict", payload)
        self.assertEqual(
            [item["label"] for item in payload["figure_previews"]],
            ["Snapshot", "Coordination polar map"],
        )
        self.assertEqual(
            payload["figure_data_url_dict"],
            {
                "Snapshot": payload["figure_previews"][0]["url"],
                "Coordination polar map": payload["figure_previews"][1]["url"],
            },
        )
        self.assertTrue(payload["table_data_url"].endswith("/System.xlsx"))
        self.assertTrue(manifest_path.exists())
        self.assertTrue((task_dir / "query_previews" / "snapshot.png").exists())

    def test_check_task_status_for_non_md_task_does_not_return_previews(self):

        encrypted_id, _ = self._create_non_md_task("qc_case")

        response = self.client.post(
            "/api/check_task_status/",
            data=json.dumps({"encrypted_id": encrypted_id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["task_type"], "GaussianCompute")
        self.assertNotIn("figure_previews", payload)
        self.assertNotIn("figure_data_url_dict", payload)
        self.assertTrue(payload["table_data_url"].endswith("/result.xlsx"))

    def test_check_task_status_returns_status_message_when_failed_without_failure_file(self):

        encrypted_id, _ = self._create_non_md_task(
            "qc_failed_status_message_case",
            status="failed",
            status_message="Pending task exceeded timeout limit.",
            create_success_signal=False,
        )

        response = self.client.post(
            "/api/check_task_status/",
            data=json.dumps({"encrypted_id": encrypted_id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["task_type"], "GaussianCompute")
        self.assertEqual(payload["failure_content"], "Pending task exceeded timeout limit.")

    def test_check_task_status_returns_default_message_when_failed_without_details(self):

        encrypted_id, _ = self._create_non_md_task(
            "qc_failed_default_message_case",
            status="failed",
            status_message="",
            create_success_signal=False,
        )

        response = self.client.post(
            "/api/check_task_status/",
            data=json.dumps({"encrypted_id": encrypted_id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["failure_content"], DEFAULT_FAILURE_CONTENT)

    def _create_md_task(self, folder_name, image_specs):

        task_dir = self._create_md_task_directory(folder_name)
        (task_dir / "success.txt").write_text("success", encoding="utf-8")
        (task_dir / "System.xlsx").write_bytes(b"fake-xlsx-content")
        (task_dir / "results.zip").write_bytes(b"zip")

        for filename, image_type, color in image_specs:
            file_path = task_dir / filename
            if image_type == "tiff":
                self._write_rgb_tiff(file_path, color)
            elif image_type == "gif":
                self._write_gif(file_path, color)
            elif image_type == "png":
                self._write_png(file_path, color)
            else:
                raise ValueError(f"Unsupported image type: {image_type}")

        xlsx_url = f"/media/AutoCompute/MDCompute/Downloads/{folder_name}/System.xlsx"
        zip_url = f"/media/AutoCompute/MDCompute/Downloads/{folder_name}/results.zip"
        encrypted_id = self._create_task_record(
            task_dir=task_dir,
            task_type="MDCoumpute",
            download_url_list=[str(task_dir), xlsx_url, zip_url],
        )
        return encrypted_id, task_dir

    def _create_non_md_task(
        self,
        folder_name,
        *,
        status="success",
        status_message=None,
        create_success_signal=True,
    ):

        task_dir = Path(self.temp_dir) / "AutoCompute" / "QcCompute" / "Downloads" / folder_name
        task_dir.mkdir(parents=True, exist_ok=True)
        if create_success_signal:
            (task_dir / "success.txt").write_text("success", encoding="utf-8")
        (task_dir / "raw_output.log").write_text("log", encoding="utf-8")
        (task_dir / "result.xlsx").write_bytes(b"fake-xlsx-content")

        log_url = f"/media/AutoCompute/QcCompute/Downloads/{folder_name}/raw_output.log"
        xlsx_url = f"/media/AutoCompute/QcCompute/Downloads/{folder_name}/result.xlsx"
        encrypted_id = self._create_task_record(
            task_dir=task_dir,
            task_type="GaussianCompute",
            download_url_list=[str(task_dir), log_url, xlsx_url],
            status=status,
            status_message=status_message,
        )
        return encrypted_id, task_dir

    def _create_md_task_directory(self, folder_name):

        task_dir = Path(self.temp_dir) / "AutoCompute" / "MDCompute" / "Downloads" / folder_name
        task_dir.mkdir(parents=True, exist_ok=True)
        return task_dir

    def _create_task_record(
        self,
        task_dir,
        task_type,
        download_url_list,
        *,
        status="success",
        status_message=None,
    ):

        encrypted_id = cipher_suite.encrypt(
            json.dumps(download_url_list).encode("utf-8")
        ).decode("utf-8")
        ComputeTask.objects.create(
            user=self.user,
            task_type=task_type,
            task_id=encrypted_id,
            folder_path=str(task_dir),
            status=status,
            status_message=status_message,
        )
        return encrypted_id

    def _write_rgb_tiff(self, path, color):

        Image.new("RGB", (32, 32), color=color).save(path, format="TIFF")

    def _write_png(self, path, color):

        Image.new("RGB", (32, 32), color=color).save(path, format="PNG")

    def _write_gif(self, path, color):

        Image.new("P", (32, 32), color=0).save(path, format="GIF")
