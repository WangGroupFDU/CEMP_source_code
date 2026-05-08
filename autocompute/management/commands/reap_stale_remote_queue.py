from __future__ import annotations

from django.core.management.base import BaseCommand

from autocompute.remote_utils import reap_stale_remote_tasks


class Command(BaseCommand):

    help = "Reap stale remote queuing/pending tasks whose dispatcher PID has disappeared."

    def add_arguments(self, parser):

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只打印将被回收的任务，不真正修改数据库。",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="最多处理多少条候选任务。",
        )

    def handle(self, *args, **options):

        dry_run = bool(options["dry_run"])
        limit = options["limit"]
        reaped_tasks = reap_stale_remote_tasks(
            statuses=("queuing", "pending"),
            limit=limit,
            dry_run=dry_run,
        )

        mode_text = "DRY-RUN" if dry_run else "APPLIED"
        for item in reaped_tasks:
            self.stdout.write(
                f"[{mode_text}] id={item['id']} task_id={item['task_id']} "
                f"task_type={item['task_type']} status_before={item['status_before']} "
                f"reason={item['failure_message']}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Reaped {len(reaped_tasks)} stale remote tasks."
            )
        )
