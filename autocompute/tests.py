import json
import importlib.util
import io
import shutil
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from unittest import mock

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from autocompute.models import ComputeTask
from autocompute.capability_registry import (
    GAUSSIAN_HTQC,
    MD_GROMACS_GAUSSIAN,
    ORCA_HTQC,
    POLYMER_GENERATION,
    VISUALIZATION_ANALYSIS,
)
from autocompute import failure_utils
from autocompute.api_views import material_recommendation_search_api, molecule_property_similarity_search_api
from autocompute.material_recommendation import search_material_recommendation_candidates
from autocompute.molecule_lookup import clear_molecule_lookup_cache, lookup_molecule_property_similarity
from autocompute import remote_utils
from autocompute import run_MD_QC_utils
from autocompute import utils as autocompute_utils
from autocompute import views as autocompute_views
from ionic_liquid.models import Anion_QC_data, Cation_QC_data
from ionic_liquid.models import IL_Tm_conductivity_ECW_data
from polymer.models import experiment_polymer_data
from crystals.models import Crystal


class MoleculePropertySimilaritySearchTests(TestCase):

    def setUp(self):

        clear_molecule_lookup_cache()
        self.user = get_user_model().objects.create_user(
            username="molecule_lookup_user",
            password="testpass123",
            email="user@example.com",
        )
        self.factory = APIRequestFactory()

    def tearDown(self):

        clear_molecule_lookup_cache()

    def test_exact_match_returns_found_with_properties(self):

        Cation_QC_data.objects.create(Name="ethanol", SMILES="CCO", HOMO_Hatree=-0.25)

        result = lookup_molecule_property_similarity("CCO")

        self.assertEqual(result["status"], "found")
        self.assertTrue(result["has_exact_match"])
        self.assertFalse(result["needs_qc_prompt"])
        self.assertGreaterEqual(len(result["exact_matches"]), 1)
        first = result["exact_matches"][0]
        self.assertEqual(first["database"], "ionic_liquid.Cation_QC_data")
        self.assertEqual(first["name"], "ethanol")
        self.assertEqual(first["similarity_percent"], "100.00%")
        self.assertEqual(first["properties"]["HOMO_Hatree"], -0.25)

    def test_without_exact_match_returns_top3_sorted(self):

        for name, smiles in [("ethane", "CC"), ("ethanol", "CCO"), ("propane", "CCC"), ("benzene", "c1ccccc1")]:
            Anion_QC_data.objects.create(Name=name, SMILES=smiles)

        result = lookup_molecule_property_similarity("CCN", topk=3)

        self.assertEqual(result["status"], "similar")
        self.assertFalse(result["has_exact_match"])
        self.assertTrue(result["needs_qc_prompt"])
        self.assertEqual(len(result["similar_matches"]), 3)
        similarities = [item["similarity"] for item in result["similar_matches"]]
        self.assertEqual(similarities, sorted(similarities, reverse=True))

    def test_psmiles_can_be_parsed_and_searched(self):

        experiment_polymer_data.objects.create(Name="polyethylene_unit", PSMILES="*CC*")

        result = lookup_molecule_property_similarity("*CC*")

        self.assertEqual(result["status"], "found")
        self.assertTrue(
            any(match["database"] == "polymer.experiment_polymer_data" for match in result["exact_matches"])
        )

    def test_api_rejects_invalid_smiles(self):

        request = self.factory.post(
            "/autocompute/api/molecule_property_similarity_search/",
            {"smiles": "not_a_valid_smiles["},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = molecule_property_similarity_search_api(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error_code"], "invalid_request")

    def test_api_requires_database_permission(self):

        self.user.userprofile.database_permission = False
        self.user.userprofile.save(update_fields=["database_permission"])
        request = self.factory.post(
            "/autocompute/api/molecule_property_similarity_search/",
            {"smiles": "CCO"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = molecule_property_similarity_search_api(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_code"], "permission_denied")
        self.assertEqual(response.data["required_permission"], "database_permission")


class MaterialRecommendationSearchTests(TestCase):

    def setUp(self):

        self.user = get_user_model().objects.create_user(
            username="material_recommend_user",
            password="testpass123",
            email="user@example.com",
        )
        self.factory = APIRequestFactory()

    def test_ionic_liquid_candidates_include_properties_and_metadata(self):

        IL_Tm_conductivity_ECW_data.objects.create(
            Name="demo_il",
            SMILES="CCO",
            Conductivity_mS_per_cm=12.3,
            Tm_K=280.0,
            ECW_V=4.8,
            Source="demo-source",
        )

        result = search_material_recommendation_candidates(
            "推荐高电导率低熔点宽电化学窗口离子液体",
            domains=["ionic_liquid"],
            topk_pool=5,
        )

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["candidate_pool"])
        self.assertEqual(result["candidate_pool"], result["candidates"])
        self.assertEqual(result["count"], len(result["candidate_pool"]))
        first = result["candidate_pool"][0]
        self.assertEqual(first["domain"], "ionic_liquid")
        self.assertEqual(first["source_table"], "ionic_liquid.IL_Tm_conductivity_ECW_data")
        self.assertEqual(first["properties"]["Conductivity_mS_per_cm"], 12.3)
        self.assertEqual(first["metadata"]["Source"], "demo-source")
        self.assertNotIn("Source", first["properties"])

    def test_auto_domain_can_return_polymer_and_crystal_candidates(self):

        experiment_polymer_data.objects.create(
            Name="demo_polymer",
            PSMILES="*CC*",
            Tg_K=420.0,
            Dielectric_Constant_Total=8.5,
            Youngs_Modulus_MPa=1200.0,
            Reference="demo-reference",
        )
        Crystal.objects.create(
            crystal="Li",
            label="demo_crystal",
            band_gap=2.100,
            chemsys="Li-O",
            density=3.200,
            density_atomic=0.050,
            deprecated="False",
            efermi=1.100,
            energy_above_hull=0.01000,
            energy_per_atom=-5.200,
            formation_energy_per_atom=-1.20000,
            formula_anonymous="AB",
            formula_pretty="LiO",
            is_gap_direct="True",
            is_magnetic="False",
            is_metal="False",
            is_stable="True",
            nelements=2,
            nsites=2,
            num_magnetic_sites=0,
            num_unique_magnetic_sites=0,
            ordering="NM",
            theoretical="True",
            total_magnetization=0.000,
            volume=20.000,
        )

        result = search_material_recommendation_candidates("推荐高介电聚合物和稳定晶体电极材料", domains=["auto"], topk_pool=10)
        domains = {item["domain"] for item in result["candidate_pool"]}

        self.assertIn("polymer", domains)
        self.assertIn("crystal", domains)

    def test_api_rejects_empty_query(self):

        request = self.factory.post("/autocompute/api/material_recommendation_search/", {"query": ""}, format="json")
        force_authenticate(request, user=self.user)

        response = material_recommendation_search_api(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error_code"], "invalid_request")

    def test_api_requires_database_permission(self):

        self.user.userprofile.database_permission = False
        self.user.userprofile.save(update_fields=["database_permission"])
        request = self.factory.post(
            "/autocompute/api/material_recommendation_search/",
            {"query": "推荐高电导率离子液体"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = material_recommendation_search_api(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["required_permission"], "database_permission")

    def test_api_rejects_invalid_seed_smiles(self):

        request = self.factory.post(
            "/autocompute/api/material_recommendation_search/",
            {
                "query": "推荐和 seed 类似的材料",
                "seed_molecules": [{"name": "bad", "smiles": "not_a_valid_smiles["}],
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = material_recommendation_search_api(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error_code"], "invalid_request")


class RemoteSchedulerTests(TestCase):

    def setUp(self):

        self.temp_dir = tempfile.mkdtemp(prefix="cemp_remote_scheduler_")
        self.server_info_path = Path(self.temp_dir) / "remote_server_info.json"
        self.user = get_user_model().objects.create_user(
            username="scheduler_user",
            password="testpass123",
            email="user@example.com",
        )

    def tearDown(self):

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_select_remote_server_prefers_lower_utilization_ratio(self):

        self._write_server_pool(
            [
                self._server("server_a", "user@<PRIVATE_IP>:", 7, "/srv/a"),
                self._server("server_b", "user@<PRIVATE_IP>:", 10, "/srv/b"),
            ]
        )
        for _ in range(4):
            self._create_task(status="pending", server_name="server_a")
        for _ in range(5):
            self._create_task(status="pending", server_name="server_b")

        with self._patch_server_pool():
            selected_server = remote_utils.select_least_utilized_remote_server()

        self.assertIsNotNone(selected_server)
        self.assertEqual(selected_server["server_name"], "server_b")
        self.assertEqual(selected_server["pending_count"], 5)

    def test_select_remote_server_breaks_tie_by_oldest_assignment_proxy(self):

        self._write_server_pool(
            [
                self._server("server_a", "user@<PRIVATE_IP>:", 4, "/srv/a"),
                self._server("server_b", "user@<PRIVATE_IP>:", 4, "/srv/b"),
            ]
        )
        older_task = self._create_task(status="success", server_name="server_a")
        newer_task = self._create_task(status="success", server_name="server_b")
        self._set_created_at(older_task, timezone.now() - timedelta(hours=2))
        self._set_created_at(newer_task, timezone.now() - timedelta(minutes=10))

        with self._patch_server_pool():
            selected_server = remote_utils.select_least_utilized_remote_server()

        self.assertIsNotNone(selected_server)
        self.assertEqual(selected_server["server_name"], "server_a")

    def test_claim_remote_dispatch_slot_keeps_task_queued_when_all_servers_full(self):

        self._write_server_pool(
            [
                self._server("server_a", "user@<PRIVATE_IP>:", 1, "/srv/a", capabilities=[GAUSSIAN_HTQC]),
                self._server("server_b", "user@<PRIVATE_IP>:", 1, "/srv/b", capabilities=[GAUSSIAN_HTQC]),
            ]
        )
        self._create_task(status="pending", server_name="server_a")
        self._create_task(status="pending", server_name="server_b")
        queued_task = self._create_task(
            status="queuing",
            server_name=None,
            priority=5,
            task_type="HTQC_single_point_energy",
        )

        with self._patch_server_pool(), mock.patch.object(
            remote_utils,
            "_check_remote_server_runtime_health",
            return_value=(True, ""),
        ):
            selected_server = remote_utils._claim_remote_dispatch_slot(queued_task)

        queued_task.refresh_from_db()
        self.assertIsNone(selected_server)
        self.assertEqual(queued_task.status, "queuing")
        self.assertIsNone(queued_task.server_name)

    def test_claim_remote_dispatch_slot_propagates_sqlite_lock_for_fresh_transaction_retry(self):

        self._write_server_pool(
            [
                self._server(
                    "server_retry",
                    "user@<PRIVATE_IP>:",
                    3,
                    "/srv/retry",
                    capabilities=[GAUSSIAN_HTQC],
                )
            ]
        )
        queued_task = self._create_task(
            status="queuing",
            server_name=None,
            priority=5,
            task_type="HTQC_single_point_energy",
        )
        selected_server = {
            **remote_utils._load_remote_server_pool(str(self.server_info_path))[0],
            "pending_count": 0,
            "utilization": 0.0,
        }

        with self._patch_server_pool(), mock.patch.object(
            remote_utils,
            "_check_remote_server_runtime_health",
            return_value=(True, ""),
        ), mock.patch.object(
            remote_utils,
            "select_least_utilized_remote_server",
            return_value=selected_server,
        ), mock.patch(
            "django.db.models.query.QuerySet.update",
            side_effect=OperationalError("database is locked"),
        ):
            with self.assertRaises(OperationalError):
                remote_utils._claim_remote_dispatch_slot(queued_task)

        queued_task.refresh_from_db()
        self.assertEqual(queued_task.status, "queuing")
        self.assertIsNone(queued_task.server_name)

    def test_run_task_immediately_remote_binds_server_at_dispatch_time(self):

        self._write_server_pool(
            [
                self._server("server_a", "user@<PRIVATE_IP>:", 1, "/srv/a_root", capabilities=[GAUSSIAN_HTQC]),
                self._server(
                    "server_b",
                    "user@<PRIVATE_IP>:",
                    2,
                    "/srv/b_root",
                    capabilities=[GAUSSIAN_HTQC, ORCA_HTQC, POLYMER_GENERATION],
                ),
            ]
        )
        self._create_task(status="pending", server_name="server_a")
        task = self._create_task(
            status="pending",
            server_name=None,
            priority=5,
            task_type="Generate_homopolymer",
        )
        captured_call = {}

        def fake_remote_task_func(source_dir, download_dir, task_obj, remote_target, remote_IP=None):

            captured_call["source_dir"] = source_dir
            captured_call["download_dir"] = download_dir
            captured_call["remote_target"] = remote_target
            captured_call["remote_IP"] = remote_IP
            captured_call["server_name"] = task_obj.server_name
            task_obj.status = "success"
            task_obj.save(update_fields=["status"])
            return task_obj

        legacy_absolute_target = "/srv/a_root/AutoCompute/QcCompute/Downloads"

        with self._patch_server_pool(), mock.patch.object(
            remote_utils.time,
            "sleep",
            return_value=None,
        ), mock.patch.object(
            remote_utils,
            "_check_remote_server_runtime_health",
            return_value=(True, ""),
        ):
            remote_utils.run_task_immediately_remote(
                fake_remote_task_func,
                "/tmp/source",
                "/tmp/download",
                task,
                legacy_absolute_target,
            )

        task.refresh_from_db()
        self.assertEqual(task.server_name, "server_b")
        self.assertEqual(task.status, "success")
        self.assertEqual(captured_call["server_name"], "server_b")
        self.assertEqual(captured_call["remote_IP"], "user@<PRIVATE_IP>:")
        self.assertEqual(
            captured_call["remote_target"],
            "/srv/b_root/AutoCompute/QcCompute/Downloads",
        )

    def test_run_task_immediately_remote_writes_failure_details_when_server_pool_is_empty(self):

        task_dir = Path(self.temp_dir) / "remote_pre_dispatch_failure"
        task_dir.mkdir(parents=True, exist_ok=True)
        task = self._create_task(
            status="pending",
            server_name=None,
            priority=5,
            task_type="HTQC_single_point_energy",
            folder_path=str(task_dir),
        )

        with self._patch_server_pool(), mock.patch.object(
            remote_utils,
            "_load_remote_server_pool",
            return_value=[],
        ):
            result_task = remote_utils.run_task_immediately_remote(
                lambda *args, **kwargs: None,
                "/tmp/source",
                str(task_dir),
                task,
                "/remote/target",
            )

        result_task.refresh_from_db()
        self.assertEqual(result_task.status, "failed")
        self.assertEqual(result_task.status_message, "No remote servers are configured.")
        self.assertTrue((task_dir / "failure.txt").exists())
        self.assertIn(
            "No remote servers are configured.",
            (task_dir / "failure.txt").read_text(encoding="utf-8"),
        )

    def test_select_remote_server_filters_by_capability(self):

        self._write_server_pool(
            [
                self._server(
                    "server_gaussian",
                    "user@<PRIVATE_IP>:",
                    10,
                    "/srv/gaussian",
                    capabilities=[GAUSSIAN_HTQC],
                ),
                self._server(
                    "server_orca",
                    "user@<PRIVATE_IP>:",
                    10,
                    "/srv/orca",
                    capabilities=[ORCA_HTQC],
                ),
            ]
        )
        for _ in range(3):
            self._create_task(status="pending", server_name="server_orca")

        with self._patch_server_pool():
            selected_server = remote_utils.select_least_utilized_remote_server(
                required_capability=ORCA_HTQC,
            )

        self.assertIsNotNone(selected_server)
        self.assertEqual(selected_server["server_name"], "server_orca")

    def test_select_remote_server_ignores_disabled_nodes(self):

        self._write_server_pool(
            [
                self._server(
                    "server_disabled",
                    "user@<PRIVATE_IP>:",
                    10,
                    "/srv/a",
                    enabled=False,
                    capabilities=[GAUSSIAN_HTQC],
                ),
                self._server(
                    "server_enabled",
                    "user@<PRIVATE_IP>:",
                    10,
                    "/srv/b",
                    capabilities=[GAUSSIAN_HTQC],
                ),
            ]
        )

        with self._patch_server_pool():
            selected_server = remote_utils.select_least_utilized_remote_server(
                required_capability=GAUSSIAN_HTQC,
            )

        self.assertIsNotNone(selected_server)
        self.assertEqual(selected_server["server_name"], "server_enabled")

    def test_select_remote_server_skips_unhealthy_candidate(self):

        self._write_server_pool(
            [
                self._server(
                    "server_a",
                    "user@<PRIVATE_IP>:",
                    10,
                    "/srv/a",
                    capabilities=[GAUSSIAN_HTQC],
                ),
                self._server(
                    "server_b",
                    "user@<PRIVATE_IP>:",
                    10,
                    "/srv/b",
                    capabilities=[GAUSSIAN_HTQC],
                ),
            ]
        )

        def fake_health_check(server, task_type, cache_ttl_seconds=60):

            if server["server_name"] == "server_a":
                return False, "missing settings"
            return True, ""

        with self._patch_server_pool(), mock.patch.object(
            remote_utils,
            "_check_remote_server_runtime_health",
            side_effect=fake_health_check,
        ):
            selected_server = remote_utils.select_least_utilized_remote_server(
                required_capability=GAUSSIAN_HTQC,
                task_type="HTQC_single_point_energy",
                enable_health_checks=True,
            )

        self.assertIsNotNone(selected_server)
        self.assertEqual(selected_server["server_name"], "server_b")

    def test_dispatch_remote_task_fails_when_no_enabled_server_registered_for_capability(self):

        task_dir = Path(self.temp_dir) / "remote_missing_capability"
        task_dir.mkdir(parents=True, exist_ok=True)
        task = self._create_task(
            status="pending",
            server_name=None,
            priority=5,
            task_type="HTQC_single_point_energy",
            folder_path=str(task_dir),
        )
        self._write_server_pool(
            [
                self._server(
                    "server_visual",
                    "user@<PRIVATE_IP>:",
                    10,
                    "/srv/visual",
                    capabilities=[VISUALIZATION_ANALYSIS],
                )
            ]
        )

        with self._patch_server_pool():
            result_task = remote_utils.run_task_immediately_remote(
                lambda *args, **kwargs: None,
                "/tmp/source",
                str(task_dir),
                task,
                "/remote/target",
            )

        result_task.refresh_from_db()
        self.assertEqual(result_task.status, "failed")
        self.assertIn(
            "No enabled remote servers are registered for capability gaussian_htqc.",
            result_task.status_message,
        )

    def test_dispatch_remote_task_fails_for_deprecated_remote_task_type(self):

        task_dir = Path(self.temp_dir) / "deprecated_remote_task"
        task_dir.mkdir(parents=True, exist_ok=True)
        task = self._create_task(
            status="pending",
            server_name=None,
            priority=5,
            task_type="MDCoumpute_ORCA",
            folder_path=str(task_dir),
        )
        self._write_server_pool(
            [
                self._server(
                    "server_md",
                    "user@<PRIVATE_IP>:",
                    10,
                    "/srv/md",
                    capabilities=[MD_GROMACS_GAUSSIAN],
                )
            ]
        )

        with self._patch_server_pool():
            result_task = remote_utils.run_task_immediately_remote(
                lambda *args, **kwargs: None,
                "/tmp/source",
                str(task_dir),
                task,
                "/remote/target",
            )

        result_task.refresh_from_db()
        self.assertEqual(result_task.status, "failed")
        self.assertIn("has been deprecated", result_task.status_message)

    def test_run_task_immediately_writes_failure_details_when_wrapper_catches_exception(self):

        task_dir = Path(self.temp_dir) / "local_immediate_failure"
        task_dir.mkdir(parents=True, exist_ok=True)
        task = self._create_task(
            status="pending",
            server_name=None,
            priority=3,
            task_type="From SMILES to Name",
            folder_path=str(task_dir),
        )
        task.remote_type = "local"
        task.save(update_fields=["remote_type"])

        def raising_task_func(source_dir, download_dir, task_obj):

            raise RuntimeError("intentional immediate failure")

        with self.assertRaises(RuntimeError):
            run_MD_QC_utils.run_task_immediately(
                raising_task_func,
                "/tmp/source",
                str(task_dir),
                task,
            )

        task.refresh_from_db()
        self.assertEqual(task.status, "failed")
        self.assertIn("RuntimeError: intentional immediate failure", task.status_message)
        self.assertTrue((task_dir / "failure.txt").exists())
        self.assertIn(
            "RuntimeError: intentional immediate failure",
            (task_dir / "failure.txt").read_text(encoding="utf-8"),
        )

    def test_dispatch_remote_task_reaps_stale_queue_head_and_runs_next_task(self):

        stale_dir = Path(self.temp_dir) / "stale_queue_head"
        next_dir = Path(self.temp_dir) / "next_queue_task"
        stale_dir.mkdir(parents=True, exist_ok=True)
        next_dir.mkdir(parents=True, exist_ok=True)

        self._write_server_pool(
            [
                self._server(
                    "server_a",
                    "user@<PRIVATE_IP>:",
                    3,
                    "/srv/a",
                    capabilities=[GAUSSIAN_HTQC],
                )
            ]
        )
        stale_task = self._create_task(
            status="queuing",
            priority=5,
            task_type="HTQC_single_point_energy",
            folder_path=str(stale_dir),
        )
        next_task = self._create_task(
            status="pending",
            priority=5,
            task_type="HTQC_single_point_energy",
            folder_path=str(next_dir),
        )
        ComputeTask.objects.filter(pk=stale_task.pk).update(pid=43210)
        stale_task.refresh_from_db()
        next_task.refresh_from_db()

        captured_call = {}

        def fake_remote_task_func(source_dir, download_dir, task_obj, remote_target, remote_IP=None):

            captured_call["remote_target"] = remote_target
            captured_call["remote_IP"] = remote_IP
            task_obj.status = "success"
            task_obj.save(update_fields=["status"])
            return task_obj

        with self._patch_server_pool(), mock.patch.object(
            remote_utils.time,
            "sleep",
            return_value=None,
        ), mock.patch.object(
            remote_utils,
            "_check_remote_server_runtime_health",
            return_value=(True, ""),
        ), mock.patch.object(
            remote_utils.psutil,
            "pid_exists",
            side_effect=lambda pid: False if int(pid) == 43210 else True,
        ):
            remote_utils.run_task_immediately_remote(
                fake_remote_task_func,
                "/tmp/source",
                str(next_dir),
                next_task,
                "/srv/a/AutoCompute/QcCompute/Downloads",
            )

        stale_task.refresh_from_db()
        next_task.refresh_from_db()
        self.assertEqual(stale_task.status, "failed")
        self.assertIn(
            remote_utils.QUEUED_DISPATCHER_DISAPPEARED_MESSAGE,
            stale_task.status_message,
        )
        self.assertEqual(next_task.status, "success")
        self.assertEqual(next_task.server_name, "server_a")
        self.assertEqual(captured_call["remote_IP"], "user@<PRIVATE_IP>:")
        self.assertEqual(
            captured_call["remote_target"],
            "/srv/a/AutoCompute/QcCompute/Downloads",
        )

    def test_dispatch_remote_task_retries_after_sqlite_lock_then_succeeds(self):

        task_dir = Path(self.temp_dir) / "sqlite_lock_retry"
        task_dir.mkdir(parents=True, exist_ok=True)
        task = self._create_task(
            status="pending",
            priority=5,
            task_type="HTQC_single_point_energy",
            folder_path=str(task_dir),
        )
        self._write_server_pool(
            [
                self._server(
                    "server_retry",
                    "user@<PRIVATE_IP>:",
                    3,
                    "/srv/retry",
                    capabilities=[GAUSSIAN_HTQC],
                )
            ]
        )

        selected_server = {
            **remote_utils._load_remote_server_pool(str(self.server_info_path))[0],
            "pending_count": 0,
            "utilization": 0.0,
        }

        def fake_remote_task_func(source_dir, download_dir, task_obj, remote_target, remote_IP=None):

            task_obj.status = "success"
            task_obj.save(update_fields=["status"])
            return task_obj

        sleep_mock = mock.Mock(return_value=None)
        with self._patch_server_pool(), mock.patch.object(
            remote_utils.time,
            "sleep",
            sleep_mock,
        ), mock.patch.object(
            remote_utils,
            "reconcile_remote_tasks",
            return_value=[],
        ), mock.patch.object(
            remote_utils,
            "_claim_remote_dispatch_slot",
            side_effect=[
                OperationalError("database is locked"),
                selected_server,
            ],
        ) as claim_mock:
            remote_utils.run_task_immediately_remote(
                fake_remote_task_func,
                "/tmp/source",
                str(task_dir),
                task,
                "AutoCompute/QcCompute/Downloads",
            )

        task.refresh_from_db()
        self.assertEqual(task.status, "success")
        self.assertEqual(claim_mock.call_count, 2)
        self.assertIn(mock.call(1), sleep_mock.call_args_list)

    def test_reconcile_remote_tasks_updates_terminal_signals_and_heartbeat_timeout(self):

        success_dir = Path(self.temp_dir) / "reconcile_success"
        failure_dir = Path(self.temp_dir) / "reconcile_failure"
        stale_pending_dir = Path(self.temp_dir) / "reconcile_stale_pending"
        stale_heartbeat_dir = Path(self.temp_dir) / "reconcile_stale_heartbeat"
        for path in [success_dir, failure_dir, stale_pending_dir, stale_heartbeat_dir]:
            path.mkdir(parents=True, exist_ok=True)

        (success_dir / "success.txt").write_text("ok", encoding="utf-8")
        (failure_dir / "failure.txt").write_text("remote failed", encoding="utf-8")

        success_task = self._create_task(
            status="pending",
            priority=5,
            task_type="HTQC_binding_energy",
            folder_path=str(success_dir),
        )
        failure_task = self._create_task(
            status="pending",
            priority=5,
            task_type="HTQC_binding_energy",
            folder_path=str(failure_dir),
        )
        stale_pending_task = self._create_task(
            status="pending",
            priority=5,
            task_type="HTQC_binding_energy",
            folder_path=str(stale_pending_dir),
        )
        stale_heartbeat_task = self._create_task(
            status="pending",
            priority=5,
            task_type="HTQC_binding_energy",
            folder_path=str(stale_heartbeat_dir),
        )

        ComputeTask.objects.filter(pk=stale_pending_task.pk).update(pid=20202)
        ComputeTask.objects.filter(pk=stale_heartbeat_task.pk).update(
            pid=30303,
            last_heartbeat_at=timezone.now() - timedelta(hours=49),
        )
        stale_pending_task.refresh_from_db()
        stale_heartbeat_task.refresh_from_db()

        with mock.patch.object(
            remote_utils.psutil,
            "pid_exists",
            side_effect=lambda pid: False if int(pid) == 20202 else True,
        ), mock.patch.object(
            remote_utils,
            "_kill_task_pid_tree",
            return_value={"attempted": True, "killed_pids": [30303]},
        ) as kill_mock:
            reconciled = remote_utils.reconcile_remote_tasks(
                dry_run=False,
                kill_stuck_pids=True,
            )

        success_task.refresh_from_db()
        failure_task.refresh_from_db()
        stale_pending_task.refresh_from_db()
        stale_heartbeat_task.refresh_from_db()

        action_map = {item["id"]: item["action"] for item in reconciled}
        self.assertEqual(success_task.status, "success")
        self.assertEqual(action_map[success_task.id], "mark_success_from_success_signal")
        self.assertEqual(failure_task.status, "failed")
        self.assertEqual(action_map[failure_task.id], "mark_failed_from_failure_signal")
        self.assertEqual(stale_pending_task.status, "failed")
        self.assertEqual(action_map[stale_pending_task.id], "mark_failed_stale_pending")
        self.assertEqual(stale_heartbeat_task.status, "failed")
        self.assertEqual(action_map[stale_heartbeat_task.id], "mark_failed_heartbeat_timeout")
        self.assertEqual(kill_mock.call_count, 1)

    def test_remote_task_heartbeat_timeout_covers_all_active_remote_task_types(self):

        active_remote_task_types = [
            "MDCoumpute",
            "HTQC_single_point_energy",
            "HTQC_single_point_energy_orca",
            "HTQC_binding_energy",
            "HTQC_binding_energy_orca",
            "HTQC_pka_pkb_calculation",
            "HTQC_ox_red_calculation",
            "HTQC_ox_red_calculation_orca",
            "HTQC_reaction_thermo_properties_calculation",
            "HTQC_global_reaction_properties_descriptors_calculation",
            "Manual_Mode_QCcompute",
            "Manual_Mode_QCcompute_energy",
            "DrawESP",
            "DrawESP_remote",
            "Draw_HOMO_LUMO_orb",
            "NCI_analysis",
            "NCI_promolecular_analysis",
            "Markov_GDyNet_analysis",
        ]

        missing_timeout_task_types = []
        for task_type in active_remote_task_types:
            task = ComputeTask(task_type=task_type)
            if remote_utils._remote_task_heartbeat_timeout(task) is None:
                missing_timeout_task_types.append(task_type)

        self.assertEqual(
            missing_timeout_task_types,
            [],
            msg=f"以下远程任务类型尚未接入统一心跳超时治理：{missing_timeout_task_types}",
        )

    def test_reconcile_remote_tasks_command_dry_run_only_reports_candidates(self):

        stale_queue_dir = Path(self.temp_dir) / "reconcile_dry_run_queue"
        stale_queue_dir.mkdir(parents=True, exist_ok=True)
        stale_queue_task = self._create_task(
            status="queuing",
            priority=5,
            task_type="HTQC_single_point_energy",
            folder_path=str(stale_queue_dir),
        )
        ComputeTask.objects.filter(pk=stale_queue_task.pk).update(pid=11111)

        stdout = io.StringIO()
        with mock.patch.object(
            remote_utils.psutil,
            "pid_exists",
            return_value=False,
        ):
            call_command(
                "reconcile_remote_tasks",
                "--dry-run",
                stdout=stdout,
            )

        stale_queue_task.refresh_from_db()
        output = stdout.getvalue()
        self.assertEqual(stale_queue_task.status, "queuing")
        self.assertIn("action=mark_failed_stale_queuing", output)
        self.assertIn("Reconciled 1 remote tasks.", output)

    def test_mark_task_failed_retries_sqlite_lock(self):

        task_dir = Path(self.temp_dir) / "mark_failed_retry"
        task_dir.mkdir(parents=True, exist_ok=True)
        task = self._create_task(
            status="pending",
            priority=5,
            task_type="HTQC_single_point_energy",
            folder_path=str(task_dir),
        )

        original_save = ComputeTask.save
        call_counter = {"count": 0}

        def flaky_save(instance, *args, **kwargs):

            call_counter["count"] += 1
            if call_counter["count"] == 1:
                raise OperationalError("database is locked")
            return original_save(instance, *args, **kwargs)

        with mock.patch.object(
            remote_utils.time,
            "sleep",
            return_value=None,
        ) as sleep_mock, mock.patch.object(
            ComputeTask,
            "save",
            autospec=True,
            side_effect=flaky_save,
        ):
            failure_utils.mark_task_failed(
                task,
                "unit test failure",
                write_failure_file=False,
                create_failure_dir=False,
            )

        task.refresh_from_db()
        self.assertEqual(task.status, "failed")
        self.assertEqual(task.status_message, "unit test failure")
        self.assertEqual(call_counter["count"], 2)
        self.assertIn(mock.call(1), sleep_mock.call_args_list)

    def test_reap_stale_remote_queue_command_marks_dead_remote_tasks_failed(self):

        stale_queue_dir = Path(self.temp_dir) / "stale_queue_command"
        stale_pending_dir = Path(self.temp_dir) / "stale_pending_command"
        done_dir = Path(self.temp_dir) / "done_signal_command"
        stale_queue_dir.mkdir(parents=True, exist_ok=True)
        stale_pending_dir.mkdir(parents=True, exist_ok=True)
        done_dir.mkdir(parents=True, exist_ok=True)
        (done_dir / "success.txt").write_text("ok", encoding="utf-8")

        stale_queue_task = self._create_task(
            status="queuing",
            priority=5,
            task_type="HTQC_single_point_energy",
            folder_path=str(stale_queue_dir),
        )
        stale_pending_task = self._create_task(
            status="pending",
            priority=5,
            task_type="HTQC_single_point_energy",
            folder_path=str(stale_pending_dir),
        )
        done_task = self._create_task(
            status="queuing",
            priority=5,
            task_type="HTQC_single_point_energy",
            folder_path=str(done_dir),
        )
        ComputeTask.objects.filter(pk=stale_queue_task.pk).update(pid=10101)
        ComputeTask.objects.filter(pk=stale_pending_task.pk).update(pid=20202)
        ComputeTask.objects.filter(pk=done_task.pk).update(pid=30303)

        stdout = io.StringIO()
        with mock.patch.object(
            remote_utils.psutil,
            "pid_exists",
            return_value=False,
        ):
            call_command("reap_stale_remote_queue", stdout=stdout)

        stale_queue_task.refresh_from_db()
        stale_pending_task.refresh_from_db()
        done_task.refresh_from_db()
        self.assertEqual(stale_queue_task.status, "failed")
        self.assertEqual(stale_pending_task.status, "failed")
        self.assertEqual(done_task.status, "queuing")
        self.assertIn(
            remote_utils.QUEUED_DISPATCHER_DISAPPEARED_MESSAGE,
            stale_queue_task.status_message,
        )
        self.assertIn(
            remote_utils.PENDING_REMOTE_PROCESS_DISAPPEARED_MESSAGE,
            stale_pending_task.status_message,
        )
        self.assertIn("Reaped 2 stale remote tasks.", stdout.getvalue())

    def test_single_scheduler_dispatches_earliest_capability_matching_task(self):

        md_dir = Path(self.temp_dir) / "scheduler_md_head"
        htqc_dir = Path(self.temp_dir) / "scheduler_htqc_next"
        md_dir.mkdir(parents=True, exist_ok=True)
        htqc_dir.mkdir(parents=True, exist_ok=True)

        self._write_server_pool(
            [
                self._server(
                    "server_gaussian",
                    "user@<PRIVATE_IP>:",
                    2,
                    "/srv/gaussian",
                    capabilities=[GAUSSIAN_HTQC],
                )
            ]
        )
        md_task = self._create_task(
            status="queuing",
            task_type="MDCoumpute",
            folder_path=str(md_dir),
        )
        htqc_task = self._create_task(
            status="queuing",
            task_type="HTQC_single_point_energy",
            folder_path=str(htqc_dir),
        )
        now = timezone.now()
        self._set_created_at(md_task, now - timedelta(minutes=2))
        self._set_created_at(htqc_task, now - timedelta(minutes=1))
        remote_utils.persist_remote_dispatch_request(
            md_task,
            source_dir=str(md_dir),
            download_dir=str(md_dir),
            func_path="autocompute.remote_utils.run_Gromacs_MD_notebook_tasks_remote",
            remote_target_subpath="AutoCompute/MDCompute/Downloads",
        )
        remote_utils.persist_remote_dispatch_request(
            htqc_task,
            source_dir=str(htqc_dir),
            download_dir=str(htqc_dir),
            func_path="autocompute.remote_utils.run_Gaussian_single_point_energy_notebook_tasks_remote",
            remote_target_subpath="AutoCompute/QcCompute/Downloads",
        )

        fake_proc = mock.Mock()
        fake_proc.pid = 4242
        with self._patch_server_pool(), mock.patch.object(
            remote_utils,
            "_start_remote_task_worker",
            return_value=fake_proc,
        ):
            result = remote_utils._dispatch_one_remote_task_from_queue()

        md_task.refresh_from_db()
        htqc_task.refresh_from_db()
        self.assertEqual(result["action"], "dispatched")
        self.assertEqual(result["task_id"], htqc_task.task_id)
        self.assertEqual(md_task.status, "queuing")
        self.assertEqual(htqc_task.status, "pending")
        self.assertEqual(htqc_task.server_name, "server_gaussian")
        self.assertEqual(htqc_task.pid, 4242)

    def test_single_scheduler_finalizes_pending_success_signal(self):

        task_dir = Path(self.temp_dir) / "scheduler_success_signal"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "success.txt").write_text("ok", encoding="utf-8")
        task = self._create_task(
            status="pending",
            server_name="server_a",
            task_type="HTQC_single_point_energy",
            folder_path=str(task_dir),
        )
        ComputeTask.objects.filter(pk=task.pk).update(pid=5151)
        task.refresh_from_db()

        result = remote_utils._finalize_pending_remote_task(task)

        task.refresh_from_db()
        self.assertEqual(result["action"], "success_from_success_signal")
        self.assertEqual(task.status, "success")

    def _create_task(
        self,
        status: str,
        server_name: str = None,
        priority: int = 3,
        task_type: str = "scheduler_test",
        folder_path: str = "/tmp/test-folder",
    ) -> ComputeTask:

        return ComputeTask.objects.create(
            user=self.user,
            task_type=task_type,
            task_id=f"task-{uuid.uuid4()}",
            folder_path=folder_path,
            status=status,
            priority=priority,
            remote_type="remote",
            server_name=server_name,
        )

    def _server(
        self,
        server_name: str,
        ip: str,
        task_limit: int,
        remote_target_dir: str,
        *,
        ssh_port: int = 22,
        enabled: bool = True,
        capabilities=None,
    ) -> dict:

        if capabilities is None:
            capabilities = [
                GAUSSIAN_HTQC,
                ORCA_HTQC,
                MD_GROMACS_GAUSSIAN,
                VISUALIZATION_ANALYSIS,
            ]

        return {
            "server_name": server_name,
            "IP": ip,
            "ssh_port": ssh_port,
            "enabled": enabled,
            "capabilities": capabilities,
            "task_limit": task_limit,
            "remote_target_dir": remote_target_dir,
        }

    def _write_server_pool(self, servers) -> None:

        self.server_info_path.write_text(
            json.dumps(servers, ensure_ascii=False),
            encoding="utf-8",
        )

    def _patch_server_pool(self):

        return mock.patch.object(
            remote_utils,
            "_get_remote_server_info_file_path",
            return_value=str(self.server_info_path),
        )

    def _set_created_at(self, task: ComputeTask, new_created_at) -> None:

        ComputeTask.objects.filter(pk=task.pk).update(created_at=new_created_at)
        task.refresh_from_db()


class QCDatabaseUtilsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        helper_path = (
            Path(__file__).resolve().parent
            / "static"
            / "QcAutocompute_programe"
            / "HTQC_single_point_energy"
            / "qc_database_utils.py"
        )
        spec = importlib.util.spec_from_file_location("qc_database_utils_under_test", helper_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        cls.helper = module

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cemp_qc_db_utils_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_database_excel_to_dict_filters_ambiguous_rows(self):
        db_dir = self.temp_dir / "Gaussian_database" / "opt+freq"
        db_dir.mkdir(parents=True, exist_ok=True)
        excel_path = db_dir / "molecule.xlsx"
        df = pd.DataFrame(
            [
                {"FileName": "dup_exact", "SMILES": "CCO"},
                {"FileName": "dup_exact", "SMILES": "CCO"},
                {"FileName": "amb_file", "SMILES": "CCN"},
                {"FileName": "amb_file", "SMILES": "CCC"},
                {"FileName": "amb_smiles_a", "SMILES": "CCO"},
                {"FileName": "amb_smiles_b", "SMILES": "OCC"},
                {"FileName": "clean_one", "SMILES": "O"},
            ]
        )
        df.to_excel(excel_path, index=False)

        mapping = self.helper.read_database_excel_to_dict(str(excel_path))

        self.assertEqual(mapping, {"O": "clean_one"})

    def test_add_and_copy_files_use_stable_storage_name(self):
        source_dir = self.temp_dir / "source"
        database_dir = self.temp_dir / "Gaussian_database" / "opt+freq"
        destination_dir = self.temp_dir / "dest"
        source_dir.mkdir(parents=True, exist_ok=True)
        database_dir.mkdir(parents=True, exist_ok=True)
        destination_dir.mkdir(parents=True, exist_ok=True)

        excel_path = Path(self.helper.ensure_database_excel(str(database_dir)))
        working_stem = "Example_Name"
        for suffix in [".gjf", ".chk", ".out"]:
            (source_dir / f"{working_stem}{suffix}").write_text(f"content-{suffix}", encoding="utf-8")

        self.helper.add_and_normalize_smiles(
            {"C(C)O": "Example Name"},
            str(source_dir),
            str(database_dir),
            str(excel_path),
        )

        stored_df = pd.read_excel(excel_path)
        self.assertEqual(len(stored_df), 1)
        stable_name = stored_df.loc[0, "FileName"]
        self.assertTrue(stable_name.startswith("g16_optfreq_"))
        self.assertEqual(stored_df.loc[0, "SMILES"], "CCO")

        for suffix in [".gjf", ".chk", ".out"]:
            self.assertTrue((database_dir / f"{stable_name}{suffix}").exists())
            self.assertFalse((database_dir / f"{working_stem}{suffix}").exists())

        self.helper.copy_files_based_on_smiles(
            str(database_dir),
            str(excel_path),
            {"CCO": "Copied Name"},
            str(destination_dir),
        )
        for suffix in [".gjf", ".chk", ".out"]:
            copied_file = destination_dir / f"Copied_Name{suffix}"
            self.assertTrue(copied_file.exists())
            self.assertEqual(copied_file.read_text(encoding="utf-8"), f"content-{suffix}")


class MDQCDatabaseUtilsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        helper_path = (
            Path(__file__).resolve().parent
            / "static"
            / "MDAutocompute_programe"
            / "md_qc_database_utils.py"
        )
        spec = importlib.util.spec_from_file_location("md_qc_database_utils_under_test", helper_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        cls.helper = module

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cemp_md_qc_db_utils_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_collect_small_molecule_rows_preserves_original_name_and_smiles(self):
        df = pd.DataFrame(
            [
                {"Name": "Poly_A", "SMILES": "C=C", "is polymer": True},
                {"Name": "EC", "SMILES": "O=C1OCCO1", "is polymer": False},
                {"Name": "Li+", "SMILES": "[Li+]", "is polymer": False},
            ]
        )

        rows = self.helper.collect_small_molecule_rows(df)

        self.assertEqual(
            rows,
            [
                {"Name": "EC", "SMILES": "O=C1OCCO1"},
                {"Name": "Li+", "SMILES": "[Li+]"},
            ],
        )

    def test_copy_reusable_results_to_success_uses_smiles_and_keeps_working_name(self):
        database_dir = self.temp_dir / "Gaussian_database" / "opt+freq"
        destination_dir = self.temp_dir / "Gaussian" / "opt+freq" / "success"
        database_dir.mkdir(parents=True, exist_ok=True)
        destination_dir.mkdir(parents=True, exist_ok=True)
        excel_path = Path(self.helper.ensure_database_excel(str(database_dir)))

        canonical_smiles = self.helper.canonicalize_smiles("C(C)O")
        stable_name = self.helper.build_stable_storage_name(canonical_smiles)
        for suffix in [".gjf", ".chk", ".out"]:
            (database_dir / f"{stable_name}{suffix}").write_text(f"db-{suffix}", encoding="utf-8")
        pd.DataFrame([{"FileName": stable_name, "SMILES": canonical_smiles}]).to_excel(excel_path, index=False)

        missing_rows, found_rows = self.helper.copy_reusable_results_to_success(
            rows=[{"Name": "Example Name", "SMILES": "OCC"}],
            database_directory=str(database_dir),
            database_excel_path=str(excel_path),
            destination_directory=str(destination_dir),
        )

        self.assertEqual(missing_rows, [])
        self.assertEqual(found_rows, [{"Name": "Example Name", "SMILES": "OCC"}])
        for suffix in [".gjf", ".chk", ".out"]:
            self.assertTrue((destination_dir / f"Example_Name{suffix}").exists())
            self.assertFalse((destination_dir / f"{stable_name}{suffix}").exists())

    def test_store_success_results_to_database_writes_stable_name(self):
        source_dir = self.temp_dir / "Gaussian" / "opt+freq" / "success"
        database_dir = self.temp_dir / "Gaussian_database" / "opt+freq"
        source_dir.mkdir(parents=True, exist_ok=True)
        database_dir.mkdir(parents=True, exist_ok=True)
        excel_path = Path(self.helper.ensure_database_excel(str(database_dir)))

        for suffix in [".gjf", ".chk", ".out"]:
            (source_dir / f"EC{suffix}").write_text(f"source-{suffix}", encoding="utf-8")

        self.helper.store_success_results_to_database(
            rows=[{"Name": "EC", "SMILES": "O=C1OCCO1"}],
            source_directory=str(source_dir),
            database_directory=str(database_dir),
            database_excel_path=str(excel_path),
        )

        stored_df = pd.read_excel(excel_path)
        self.assertEqual(len(stored_df), 1)
        stable_name = stored_df.loc[0, "FileName"]
        self.assertTrue(stable_name.startswith("g16_optfreq_"))
        self.assertEqual(stored_df.loc[0, "SMILES"], self.helper.canonicalize_smiles("O=C1OCCO1"))

        for suffix in [".gjf", ".chk", ".out"]:
            self.assertTrue((database_dir / f"{stable_name}{suffix}").exists())
            self.assertFalse((database_dir / f"EC{suffix}").exists())

    def test_get_gaussian_optfreq_database_paths_follow_settings_result(self):
        custom_root = self.temp_dir / "custom_root"
        custom_root.mkdir(parents=True, exist_ok=True)

        optfreq, excel_path = self.helper.get_gaussian_optfreq_database_paths(
            {"gaussian_database_path": str(custom_root)}
        )

        expected_optfreq = str((custom_root / "Gaussian_database" / "opt+freq").resolve())
        expected_excel = str((custom_root / "Gaussian_database" / "opt+freq" / "molecule.xlsx").resolve())

        self.assertEqual(optfreq, expected_optfreq)
        self.assertTrue(Path(optfreq).is_dir())
        self.assertEqual(str(Path(excel_path).resolve()), expected_excel)
        self.assertTrue(Path(excel_path).is_file())


class RemoteQCSubmissionViewTests(TestCase):

    def setUp(self):

        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            username=f"remote_submit_{uuid.uuid4().hex[:8]}",
            password="testpass123",
            email="user@example.com",
        )
        self.temp_media_root = tempfile.mkdtemp(prefix="cemp_remote_submit_")

    def tearDown(self):

        shutil.rmtree(self.temp_media_root, ignore_errors=True)

    def test_pka_submission_uses_remote_dispatch(self):

        self._assert_remote_submission(
            view_func=autocompute_views.process_excel_QcCoumpute_HTQC_pka_pkb,
            excel_filename="pkb_DFT.xlsx",
            expected_source_suffix=str(
                Path("autocompute/static/QcAutocompute_programe/HTQC_pka_pkb")
            ),
            expected_func_path="autocompute.remote_utils.run_Gaussian_pka_pkb_notebook_tasks_remote",
        )

    def test_reaction_thermo_submission_uses_remote_dispatch(self):

        self._assert_remote_submission(
            view_func=autocompute_views.process_excel_HTQC_reaction_thermo,
            excel_filename="HTQC_reaction_thermo.xlsx",
            expected_source_suffix=str(
                Path("autocompute/static/QcAutocompute_programe/HTQC_reaction_thermo")
            ),
            expected_func_path="autocompute.remote_utils.run_Gaussian_reaction_thermo_notebook_tasks_remote",
        )

    def test_global_reaction_submission_uses_remote_dispatch(self):

        self._assert_remote_submission(
            view_func=autocompute_views.process_excel_HTQC_global_reaction_properties,
            excel_filename="HTQC_global_reaction_descriptors.xlsx",
            expected_source_suffix=str(
                Path("autocompute/static/QcAutocompute_programe/HTQC_global_reaction_descriptors_calculation")
            ),
            expected_func_path="autocompute.remote_utils.run_Gaussian_global_reaction_properties_notebook_tasks_remote",
        )

    def _assert_remote_submission(self, view_func, excel_filename: str, expected_source_suffix: str, expected_func_path: str) -> None:

        request = self.factory.post(
            "/autocompute/test/",
            {"excel_file": self._build_excel_upload(excel_filename)},
        )
        request.user = self.user

        fake_process = mock.Mock()
        fake_process.pid = 4321

        with override_settings(MEDIA_ROOT=self.temp_media_root), mock.patch.object(
            autocompute_views.subprocess,
            "Popen",
            return_value=fake_process,
        ) as popen_mock:
            response = view_func(request)

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content.decode("utf-8"))
        task = ComputeTask.objects.get(task_id=payload["encrypted_id"])

        self.assertEqual(task.remote_type, "remote")
        self.assertEqual(task.status, "queuing")
        self.assertIsNone(task.server_name)
        self.assertEqual(task.pid, 4321)

        command = popen_mock.call_args[0][0]
        self.assertEqual(command[2], "new_execute_long_task_generic_remote")
        self.assertTrue(command[4].endswith(expected_source_suffix))
        self.assertEqual(command[6], expected_func_path)
        self.assertEqual(command[7], autocompute_views.REMOTE_QC_DOWNLOADS_TARGET)

    def _build_excel_upload(self, filename: str) -> SimpleUploadedFile:

        buffer = io.BytesIO()
        pd.DataFrame(
            [
                {"Name": "example", "SMILES": "O"},
            ]
        ).to_excel(buffer, index=False)
        buffer.seek(0)
        return SimpleUploadedFile(
            filename,
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


class OrcaManualModeXYZParsingTests(TestCase):

    def setUp(self):

        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            username=f"orca_xyz_{uuid.uuid4().hex[:8]}",
            password="testpass123",
            email="user@example.com",
        )

    def test_parse_xyz_content_accepts_valid_standard_xyz(self):

        xyz_content = (
            "3\n"
            "water molecule\n"
            "O 0.000000 0.000000 0.000000\n"
            "H 0.758602 0.000000 0.504284\n"
            "H -0.758602 0.000000 0.504284\n"
        )

        parsed = autocompute_utils.parse_xyz_content(xyz_content)

        self.assertEqual(parsed["atom_count"], 3)
        self.assertEqual(parsed["comment_line"], "water molecule")
        self.assertEqual(
            parsed["coordinate_block"],
            "\n".join(
                [
                    "O 0.000000 0.000000 0.000000",
                    "H 0.758602 0.000000 0.504284",
                    "H -0.758602 0.000000 0.504284",
                ]
            ),
        )

    def test_extract_xyz_coordinate_block_allows_trailing_blank_lines(self):

        xyz_content = (
            "2\n"
            "helium dimer\n"
            "He 0.0 0.0 0.0\n"
            "He 0.0 0.0 1.2\n"
            "\n"
            "\n"
        )

        coordinate_block = autocompute_utils.extract_xyz_coordinate_block(xyz_content)
        self.assertEqual(coordinate_block, "He 0.0 0.0 0.0\nHe 0.0 0.0 1.2")

    def test_parse_xyz_content_rejects_invalid_atom_count(self):

        with self.assertRaisesMessage(ValueError, "positive integer atom count"):
            autocompute_utils.parse_xyz_content(
                "abc\ncomment\nH 0.0 0.0 0.0\n"
            )

    def test_parse_xyz_content_rejects_coordinate_count_mismatch(self):

        with self.assertRaisesMessage(ValueError, "coordinate lines"):
            autocompute_utils.parse_xyz_content(
                "3\ncomment\nH 0.0 0.0 0.0\nH 0.0 0.0 1.0\n"
            )

    def test_parse_xyz_content_rejects_invalid_coordinate_line(self):

        with self.assertRaisesMessage(ValueError, "Invalid XYZ coordinate line"):
            autocompute_utils.parse_xyz_content(
                "2\ncomment\nH 0.0 0.0 0.0\nbad_line\n"
            )

    def test_manual_mode_optfreq_view_returns_400_for_invalid_xyz(self):

        response = self._post_manual_mode_view(
            autocompute_views.manual_mode_qccompute_byurl,
            "not_a_valid_xyz\n",
        )

        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content.decode("utf-8"))
        self.assertIn("error", payload)
        self.assertEqual(ComputeTask.objects.count(), 0)

    def test_manual_mode_energy_view_returns_400_for_invalid_xyz(self):

        response = self._post_manual_mode_view(
            autocompute_views.manual_mode_qccompute_byurl_energy,
            "2\ncomment\nH 0.0 0.0 0.0\n",
        )

        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content.decode("utf-8"))
        self.assertIn("error", payload)
        self.assertEqual(ComputeTask.objects.count(), 0)

    def _post_manual_mode_view(self, view_func, xyz_text: str):

        request = self.factory.post(
            "/autocompute/test/",
            {
                "xyz_file": SimpleUploadedFile(
                    "test.xyz",
                    xyz_text.encode("utf-8"),
                    content_type="chemical/x-xyz",
                ),
                "total_charge": "0",
                "spin_multiplicity": "1",
                "system_name": "water",
            },
        )
        request.user = self.user
        request.content_type = "multipart/form-data"

        with mock.patch.object(
            autocompute_views, "get_authenticated_user", return_value=self.user
        ), mock.patch.object(
            autocompute_views, "can_submit_today", return_value=(True, 3)
        ):
            return view_func(request)
