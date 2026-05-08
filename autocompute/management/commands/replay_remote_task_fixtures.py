

from __future__ import annotations

import json
from typing import Sequence

from django.core.management.base import BaseCommand, CommandError

from autocompute.remote_replay_debug import (
    discover_fixture_records,
    get_default_fixture_registry_path,
    get_default_report_root,
    get_registered_remote_task_types,
    run_fixture_replays,
)


class Command(BaseCommand):
    help = "发现远程成功任务 fixture，并在指定计算节点上执行全量 task_type 回放测试。"

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["discover", "run"],
            help="discover: 生成 fixture 注册表；run: 在指定节点上执行回放测试。",
        )
        parser.add_argument(
            "--registry-path",
            default=get_default_fixture_registry_path(),
            help="fixture 注册表 JSON 路径。",
        )
        parser.add_argument(
            "--report-root",
            default=get_default_report_root(),
            help="回放报告与工作目录根路径。",
        )
        parser.add_argument(
            "--target-server",
            default="",
            help="run 动作必填：待测节点的 server_name。",
        )
        parser.add_argument(
            "--target-remote-root",
            default="",
            help="显式指定待测节点上的回放测试根目录，例如 /path/to/example/test_folder 。",
        )
        parser.add_argument(
            "--parallel-workers",
            type=int,
            default=1,
            help="并发回放的最大任务数；默认 1，建议与目标节点 task_limit 保持一致。",
        )
        parser.add_argument(
            "--task-type",
            action="append",
            dest="task_types",
            default=[],
            help="仅回放指定 task_type，可重复传入；默认回放全部已注册远程 task_type。",
        )
        parser.add_argument(
            "--stop-on-failure",
            action="store_true",
            help="默认遇到失败会继续测试其余 task_type；开启后首个失败即停止。",
        )

    def handle(self, *args, **options):
        action = options["action"]
        registry_path = options["registry_path"]
        report_root = options["report_root"]
        task_types: Sequence[str] = options["task_types"] or get_registered_remote_task_types()

        if action == "discover":
            records, missing = discover_fixture_records(registry_path=registry_path)
            payload = {
                "registry_path": registry_path,
                "discovered_count": len(records),
                "missing_task_types": missing,
                "task_types": sorted(records.keys()),
            }
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
            if missing:
                raise CommandError(
                    f"Fixture discovery incomplete. Missing task types: {', '.join(missing)}"
                )
            return

        target_server = str(options["target_server"] or "").strip()
        if not target_server:
            raise CommandError("--target-server is required when action=run")

        summary = run_fixture_replays(
            target_server_name=target_server,
            registry_path=registry_path,
            task_types=task_types,
            report_root=report_root,
            target_remote_root=options["target_remote_root"] or None,
            parallel_workers=options["parallel_workers"],
            continue_on_failure=not options["stop_on_failure"],
        )
        self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2))
        if not summary.get("all_passed", False):
            raise CommandError(
                f"Replay qualification failed for {target_server}. "
                f"See {summary.get('summary_json_path')} and {summary.get('summary_md_path')}."
            )
