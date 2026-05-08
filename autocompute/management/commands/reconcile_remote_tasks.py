from __future__ import annotations

from django.core.management.base import BaseCommand

from autocompute.remote_utils import reconcile_remote_tasks


class Command(BaseCommand):

    help = "Reconcile remote queuing/pending tasks, including stale PID, terminal signals and heartbeat timeout."

    def add_arguments(self, parser):

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只打印将被处理的任务，不真正修改数据库。",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="最多扫描多少条远程 queuing/pending 任务。",
        )
        parser.add_argument(
            "--kill-stuck-pids",
            dest="kill_stuck_pids",
            action="store_true",
            default=True,
            help="对心跳超时的 pending 任务先尝试终止 PID 树（默认开启）。",
        )
        parser.add_argument(
            "--no-kill-stuck-pids",
            dest="kill_stuck_pids",
            action="store_false",
            help="对心跳超时的 pending 任务不终止 PID 树，只改状态。",
        )

    def handle(self, *args, **options):

        dry_run = bool(options["dry_run"])
        limit = options["limit"]
        kill_stuck_pids = bool(options["kill_stuck_pids"])

        reconciled_tasks = reconcile_remote_tasks(
            limit=limit,
            dry_run=dry_run,
            kill_stuck_pids=kill_stuck_pids,
        )

        mode_text = "DRY-RUN" if dry_run else "APPLIED"
        for item in reconciled_tasks:
            kill_summary = item.get("kill_summary")
            kill_text = f" kill={kill_summary}" if kill_summary else ""
            self.stdout.write(
                f"[{mode_text}] id={item['id']} task_id={item['task_id']} "
                f"task_type={item['task_type']} status_before={item['status_before']} "
                f"action={item['action']} reason={item['reason']}{kill_text}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Reconciled {len(reconciled_tasks)} remote tasks."
            )
        )
