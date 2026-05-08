

from __future__ import annotations

import fcntl
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from autocompute.media_cleanup import cleanup_expired_task_directories


LOCK_FILE_PATH = "/tmp/cemp_cleanup_expired_task_dirs.lock"


@contextmanager
def file_lock(lock_file_path: str) -> Iterator[None]:

    lock_path = Path(lock_file_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    with lock_path.open("w", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CommandError(f"清理任务已在运行中：{lock_file_path}") from exc

        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class Command(BaseCommand):
    help = "清理超过保留期的 CEMP media 任务目录，并同步删除远端镜像目录。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=60,
            help="保留天数，默认 60 天。",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只输出候选目录与计划动作，不做任何删除或状态修改。",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="限制本轮最多处理的目录数量，便于首次小批量验证。",
        )
        parser.add_argument(
            "--root",
            action="append",
            dest="roots",
            default=None,
            help="仅处理指定相对根目录，可重复传入。",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        limit = options["limit"]
        roots = options["roots"]

        if days <= 0:
            raise CommandError("--days 必须大于 0。")
        if limit is not None and limit <= 0:
            raise CommandError("--limit 必须大于 0。")

        with file_lock(LOCK_FILE_PATH):
            results = cleanup_expired_task_directories(
                days=days,
                dry_run=dry_run,
                limit=limit,
                root_filters=roots,
            )

        log_dir = Path(settings.BASE_DIR) / "logs" / "media_cleanup"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"media_cleanup_{datetime.now().strftime('%Y%m%d')}.jsonl"

        with log_path.open("a", encoding="utf-8") as log_handle:
            for record in results:
                log_handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        success_count = sum(
            1
            for record in results
            if not record.get("error")
        )
        failure_count = len(results) - success_count

        self.stdout.write(
            self.style.SUCCESS(
                f"cleanup_expired_task_dirs 完成：total={len(results)} success={success_count} failure={failure_count} dry_run={dry_run}"
            )
        )
        self.stdout.write(f"审计日志已写入：{log_path}")

        if failure_count:
            self.stdout.write(self.style.WARNING("存在失败记录，请检查 JSONL 审计日志。"))
