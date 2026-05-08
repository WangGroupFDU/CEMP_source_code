from __future__ import annotations

from django.core.management.base import BaseCommand

from autocompute.remote_utils import run_remote_task_worker


class Command(BaseCommand):

    help = "Run one scheduler-managed remote task worker."

    def add_arguments(self, parser):
        parser.add_argument(
            "task_id",
            type=str,
            help="ComputeTask.task_id（加密字符串）。",
        )

    def handle(self, *args, **options):
        run_remote_task_worker(str(options["task_id"]))
