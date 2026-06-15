import csv
import hashlib
import json
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError


RESTRICTED_PHRASES = [
    "review" + "-only",
    "no " + "redistribution",
    "no " + "commercial use",
    "not " + "expected to run",
    "not the complete " + "production system",
    "paper " + "review only",
    "non-production " + "reproducibility assessment",
    "CEMP Source Code " + "Review License",
]


def sha256_file(path):
    """
    功能目的：
        计算文件 SHA256，用于确认公开数据资产未被意外替换。
    输入参数：
        path: 待校验文件路径。
    返回值：
        十六进制 SHA256 字符串。
    关键流程：
        以二进制分块读取文件，避免大文件一次进入内存。
    可能报错或边界情况：
        文件不存在时由调用方提前处理。
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_csv_rows(path):
    """
    功能目的：
        统计 CSV 数据行数，排除表头。
    输入参数：
        path: CSV 文件路径。
    返回值：
        数据行数量。
    关键流程：
        使用 csv.reader 逐行读取，避免依赖 pandas。
    可能报错或边界情况：
        空文件会返回 0，并在上层与 manifest rows 比较。
    """
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def resolve_model(model_path):
    app_label, model_name = model_path.split(".", 1)
    return apps.get_model(app_label, model_name)


def expected_asset_count(asset):
    """
    功能目的：读取 manifest 中的预期计数字段。
    输入参数：asset，单个 manifest asset 字典。
    返回值：rows 或 data_points 的值；没有计数字段时返回 None。
    关键流程：ML 数据使用 rows；实验与理论计算数据使用 data_points。
    边界情况：为了兼容旧 manifest，同时存在时 rows 优先。
    """
    if asset.get("rows") is not None:
        return asset.get("rows")
    return asset.get("data_points")


class Command(BaseCommand):
    help = "Verify public release manifest, demo data, and repository release language."

    def add_arguments(self, parser):
        parser.add_argument("--manifest", default="data/public_manifest.json")
        parser.add_argument("--include-paper", action="store_true")

    def handle(self, *args, **options):
        """
        功能目的：
            在发布前检查公开数据 manifest、demo 文件和限制性许可证措辞。
        输入参数：
            --manifest: manifest 路径；--include-paper: 是否强制检查完整论文资产。
        返回值：
            校验成功时输出 ok，失败时抛出 CommandError。
        关键流程：
            校验仓库内公开文件存在、SHA256、计数、demo 数据库行数和 README/LICENSE 语言。
        可能报错或边界情况：
            仓库内 local_path 资产总是检查；GitHub Release 模型归档默认跳过，
            传入 --include-paper 后必须存在并通过校验。
        """
        manifest_path = Path(options["manifest"])
        if not manifest_path.exists():
            raise CommandError(f"Manifest not found: {manifest_path}")

        root = manifest_path.parent.parent
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        failures = []

        for asset in manifest.get("assets", []):
            check_paper = options["include_paper"] and "paper" in asset.get("required_for", [])
            check_demo = "demo" in asset.get("required_for", [])
            local_path_value = asset.get("local_path")
            check_local = bool(local_path_value)
            if not check_local and not check_demo and not check_paper:
                continue

            if not local_path_value:
                release_asset_name = asset.get("release_asset_name")
                if check_paper and release_asset_name:
                    local_path = root / "release_assets" / release_asset_name
                    if not local_path.exists():
                        failures.append(f"{asset.get('name')}: release asset not found: {local_path}")
                        continue
                else:
                    if check_paper:
                        failures.append(f"{asset.get('name')}: no local_path for paper check")
                    continue
            else:
                local_path = root / local_path_value

            if not local_path.exists():
                failures.append(f"{asset.get('name')}: file not found: {local_path}")
                continue

            expected_sha256 = asset.get("sha256")
            if expected_sha256 and sha256_file(local_path) != expected_sha256:
                failures.append(f"{asset.get('name')}: sha256 mismatch")

            expected_count = expected_asset_count(asset)
            if asset.get("format") == "csv" and expected_count is not None:
                actual_rows = count_csv_rows(local_path)
                if actual_rows != expected_count:
                    failures.append(f"{asset.get('name')}: expected {expected_count} records, found {actual_rows}")

            model_path = asset.get("django_model")
            if model_path and check_demo:
                try:
                    model = resolve_model(model_path)
                    db_count = model.objects.count()
                    if expected_count is not None and db_count not in {0, expected_count}:
                        failures.append(f"{asset.get('name')}: database has {db_count} records, expected {expected_count}")
                except DatabaseError as exc:
                    failures.append(f"{asset.get('name')}: database check failed: {exc}")

        for path_value in ["README.md", "LICENSE"]:
            path = root / path_value
            if not path.exists():
                failures.append(f"{path_value}: missing")
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for phrase in RESTRICTED_PHRASES:
                if phrase.lower() in text:
                    failures.append(f"{path_value}: restricted phrase remains: {phrase}")

        if failures:
            raise CommandError("\n".join(failures))

        self.stdout.write(self.style.SUCCESS("public release verification passed"))
