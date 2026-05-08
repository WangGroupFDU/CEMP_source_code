from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from autocompute.remote_utils import run_remote_queue_scheduler_loop


class Command(BaseCommand):

    help = "Run the single-writer remote queue scheduler."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="只执行一轮调度与对账，然后退出。",
        )
        parser.add_argument(
            "--sleep-seconds",
            type=int,
            default=5,
            help="常驻模式每轮之间的休眠秒数，默认 5 秒。",
        )

    def handle(self, *args, **options):
        try:
            run_remote_queue_scheduler_loop(
                once=bool(options["once"]),
                sleep_seconds=int(options["sleep_seconds"]),
            )
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc
