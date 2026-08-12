import ast
import csv
import hashlib
import importlib.util
import json
import re
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from autocompute.public_algorithm_inventory import (
    ACTIVE_NOTEBOOKS,
    WORKFLOW_HELPER_MODULES,
    WORKFLOW_NOTEBOOKS,
)


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

FORBIDDEN_NOTEBOOK_MARKERS = [
    "PSEUDOCODE",
    "Public pseudocode",
    "Public message removed for release.",
    "Original notebook SHA256",
    "Original source SHA256",
    "/opt/cemp",
    "/data/ORCA_database",
    "/home/fwtop/apps/openmpi",
    "/home/public/orca",
    "/root/Gaussian16",
]

FORBIDDEN_NOTEBOOK_PATTERNS = {
    "RFC 1918 private IPv4 address": re.compile(
        r"(?<!\d)(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})(?!\d)"
    ),
}

REQUIRED_SOFTWARE_SETTING_KEYS = {
    "gaussian16_bin",
    "gaussian16_formchk",
    "gaussian_database_path",
    "orca_path",
    "orca_2mkl_path",
    "orca_database_path",
    "gmx_bin",
    "multiwfn_exe",
    "sobtop_home",
    "openmpi_bin",
    "openmpi_lib",
    "vmd_exe",
    "workflow_state_dir",
}


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


def count_csv_data_points(path, columns):
    """
    功能目的：
        统计实验数据表中指定性质列的非空数据点数量。
    输入参数：
        path: CSV 文件路径。
        columns: 需要统计的性质列名列表。
    返回值：
        指定列中非空、非 null 标记的单元格总数。
    关键流程：
        使用 DictReader 按列读取；先检查 manifest 指定列是否都存在，再逐行统计。
    可能报错或边界情况：
        如果 manifest 指定了不存在的列，会抛出 ValueError，防止静默少统计。
    """
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return 0

        missing_columns = [column for column in columns if column not in reader.fieldnames]
        if missing_columns:
            raise ValueError(f"data point columns not found: {', '.join(missing_columns)}")

        count = 0
        for row in reader:
            for column in columns:
                value = (row.get(column) or "").strip()
                if value and value.lower() not in {"nan", "none", "null"}:
                    count += 1
        return count


def resolve_model(model_path):
    app_label, model_name = model_path.split(".", 1)
    return apps.get_model(app_label, model_name)


def validate_public_algorithms(root):
    """
    功能目的：校验公开 notebook 白名单、源码完整性和无运行态输出要求。
    输入参数：root 为仓库根目录。
    返回值：失败说明列表；空列表表示通过。
    关键流程：比较 118+5 白名单、解析 JSON/Python、检查输出和发布清理标记。
    可能报错或边界情况：任意 notebook JSON 损坏时记录错误并继续检查其他文件。
    """
    failures = []
    expected = set(ACTIVE_NOTEBOOKS)
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.ipynb")
        if ".git" not in path.parts
    }

    if len(WORKFLOW_NOTEBOOKS) != 118:
        failures.append(f"algorithm inventory: expected 118 workflow notebooks, found {len(WORKFLOW_NOTEBOOKS)}")
    if len(ACTIVE_NOTEBOOKS) != 123:
        failures.append(f"algorithm inventory: expected 123 total notebooks, found {len(ACTIVE_NOTEBOOKS)}")
    for relative_path in sorted(expected - actual):
        failures.append(f"algorithm notebook missing: {relative_path}")
    for relative_path in sorted(actual - expected):
        failures.append(f"unregistered notebook found: {relative_path}")

    for relative_path in sorted(expected & actual):
        path = root / relative_path
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            failures.append(f"{relative_path}: invalid notebook JSON: {exc}")
            continue

        for cell_index, cell in enumerate(notebook.get("cells", [])):
            source_value = cell.get("source", [])
            source = "".join(source_value) if isinstance(source_value, list) else str(source_value)
            for marker in FORBIDDEN_NOTEBOOK_MARKERS:
                if marker in source:
                    failures.append(f"{relative_path}: forbidden marker remains in cell {cell_index}: {marker}")
            for description, pattern in FORBIDDEN_NOTEBOOK_PATTERNS.items():
                if pattern.search(source):
                    failures.append(
                        f"{relative_path}: forbidden {description} remains in cell {cell_index}"
                    )

            if cell.get("cell_type") != "code":
                continue
            if cell.get("execution_count") is not None:
                failures.append(f"{relative_path}: execution_count remains in cell {cell_index}")
            if cell.get("outputs"):
                failures.append(f"{relative_path}: output remains in cell {cell_index}")
            try:
                ast.parse(source)
            except SyntaxError as exc:
                failures.append(
                    f"{relative_path}: Python syntax error in cell {cell_index}, line {exc.lineno}: {exc.msg}"
                )

    return failures


def validate_workflow_support_files(root):
    """
    功能目的：校验 notebook 实际导入的辅助模块与共享软件配置模块。
    输入参数：root 为仓库根目录。
    返回值：失败说明列表。
    关键流程：逐个解析辅助模块，再动态加载共享配置并核对公共键。
    可能报错或边界情况：模块导入或配置解析失败时记录异常，不影响后续检查汇总。
    """
    failures = []
    for relative_path in WORKFLOW_HELPER_MODULES:
        path = root / relative_path
        if not path.is_file():
            failures.append(f"workflow helper missing: {relative_path}")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            failures.append(f"{relative_path}: helper module cannot be parsed: {exc}")

    settings_path = root / "autocompute" / "static" / "cemp_software_settings.py"
    if not settings_path.is_file():
        failures.append(f"workflow settings module missing: {settings_path.relative_to(root)}")
        return failures

    try:
        spec = importlib.util.spec_from_file_location("cemp_public_software_settings", settings_path)
        if spec is None or spec.loader is None:
            raise ImportError("unable to create module specification")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        parsed = module.load_and_apply_settings()
    except Exception as exc:
        failures.append(f"workflow settings module cannot be loaded: {type(exc).__name__}: {exc}")
        return failures

    missing_keys = sorted(REQUIRED_SOFTWARE_SETTING_KEYS - set(parsed))
    if missing_keys:
        failures.append(f"workflow settings keys missing: {', '.join(missing_keys)}")
    return failures


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
            仓库内 local_path 资产总是检查；没有 local_path 的旧 Release 资产仅在
            传入 --include-paper 后按 release_asset_name 从 release_assets/ 回退检查。
        """
        manifest_path = Path(options["manifest"])
        if not manifest_path.exists():
            raise CommandError(f"Manifest not found: {manifest_path}")

        root = manifest_path.parent.parent
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        failures = []

        failures.extend(validate_public_algorithms(root))
        failures.extend(validate_workflow_support_files(root))

        algorithm_inventory = manifest.get("algorithm_inventory", {})
        expected_algorithm_metadata = {
            "workflow_notebooks": len(WORKFLOW_NOTEBOOKS),
            "inference_notebooks": len(ACTIVE_NOTEBOOKS) - len(WORKFLOW_NOTEBOOKS),
            "total_notebooks": len(ACTIVE_NOTEBOOKS),
        }
        for key, expected_value in expected_algorithm_metadata.items():
            if algorithm_inventory.get(key) != expected_value:
                failures.append(
                    f"manifest algorithm_inventory.{key}: expected {expected_value}, "
                    f"found {algorithm_inventory.get(key)!r}"
                )

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

            expected_rows = asset.get("rows")
            expected_data_points = asset.get("data_points")
            if asset.get("format") == "csv" and expected_rows is not None:
                actual_rows = count_csv_rows(local_path)
                if actual_rows != expected_rows:
                    failures.append(f"{asset.get('name')}: expected {expected_rows} rows, found {actual_rows}")

            if asset.get("format") == "csv" and expected_data_points is not None:
                data_point_columns = asset.get("data_point_columns")
                if data_point_columns:
                    try:
                        actual_data_points = count_csv_data_points(local_path, data_point_columns)
                    except ValueError as exc:
                        failures.append(f"{asset.get('name')}: {exc}")
                    else:
                        if actual_data_points != expected_data_points:
                            failures.append(
                                f"{asset.get('name')}: expected {expected_data_points} data points, "
                                f"found {actual_data_points}"
                            )
                elif expected_rows is None:
                    actual_rows = count_csv_rows(local_path)
                    if actual_rows != expected_data_points:
                        failures.append(
                            f"{asset.get('name')}: expected {expected_data_points} records, found {actual_rows}"
                        )

            model_path = asset.get("django_model")
            if model_path and check_demo:
                try:
                    model = resolve_model(model_path)
                    db_count = model.objects.count()
                    expected_db_count = expected_rows
                    if expected_db_count is None and not asset.get("data_point_columns"):
                        expected_db_count = expected_data_points
                    if expected_db_count is not None and db_count not in {0, expected_db_count}:
                        failures.append(
                            f"{asset.get('name')}: database has {db_count} records, expected {expected_db_count}"
                        )
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
