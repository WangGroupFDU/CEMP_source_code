import csv
import json
from decimal import Decimal
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


def resolve_model(model_path):
    """
    功能目的：
        根据 manifest 中的 Django 模型路径解析模型类。
    输入参数：
        model_path: 形如 ionic_liquid.IL 的字符串。
    返回值：
        Django model class。
    关键流程：
        将 app_label 和 model_name 拆开后交给 Django app registry。
    可能报错或边界情况：
        路径缺少点号或模型不存在时抛出 CommandError，便于用户定位 manifest 问题。
    """
    if "." not in model_path:
        raise CommandError(f"Invalid django_model value: {model_path}")
    app_label, model_name = model_path.split(".", 1)
    model = apps.get_model(app_label, model_name)
    if model is None:
        raise CommandError(f"Model not found: {model_path}")
    return model


def convert_value(field, value):
    """
    功能目的：
        将 CSV 字符串转换为 Django 字段可保存的 Python 值。
    输入参数：
        field: Django 字段对象。
        value: CSV 中读取到的原始字符串。
    返回值：
        转换后的 Python 值。
    关键流程：
        空字符串按 None 处理；数值字段按字段类型转换；其他字段保留字符串。
    可能报错或边界情况：
        CSV 中数值格式错误时会抛出 ValueError，并由调用方附带字段名报告。
    """
    if value == "":
        return None if getattr(field, "null", False) else ""

    internal_type = field.get_internal_type()
    if internal_type in {"FloatField"}:
        return float(value)
    if internal_type in {"IntegerField", "PositiveIntegerField", "PositiveSmallIntegerField", "BigIntegerField"}:
        return int(value)
    if internal_type == "DecimalField":
        return Decimal(value)
    if internal_type == "BooleanField":
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return value


def load_csv(model, csv_path):
    """
    功能目的：
        将单个 CSV 文件导入指定 Django 模型。
    输入参数：
        model: 目标 Django 模型。
        csv_path: UTF-8 CSV 文件路径。
    返回值：
        导入的记录数。
    关键流程：
        读取表头；跳过模型中不存在的列；按字段类型转换；bulk_create 写入。
    可能报错或边界情况：
        CSV 缺少可导入字段、字段类型不匹配或文件不存在时抛出明确异常。
    """
    model_fields = {
        field.name: field
        for field in model._meta.get_fields()
        if getattr(field, "concrete", False) and not getattr(field, "auto_created", False)
    }
    objects = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise CommandError(f"CSV file has no header: {csv_path}")

        importable_fields = [name for name in reader.fieldnames if name in model_fields]
        if not importable_fields:
            raise CommandError(f"CSV file has no columns matching {model.__name__}: {csv_path}")

        for row_number, row in enumerate(reader, start=2):
            kwargs = {}
            for field_name in importable_fields:
                field = model_fields[field_name]
                try:
                    kwargs[field_name] = convert_value(field, row.get(field_name, ""))
                except Exception as exc:
                    raise CommandError(
                        f"Invalid value for {model.__name__}.{field_name} at {csv_path}:{row_number}: {exc}"
                    )
            objects.append(model(**kwargs))

    if objects:
        model.objects.bulk_create(objects, batch_size=1000)
    return len(objects)


def expected_asset_count(asset):
    """
    功能目的：
        读取 manifest 中用于数据库导入校验的记录数字段。
    输入参数：
        asset: 单个 manifest asset 字典。
    返回值：
        优先返回 rows；若不存在则返回 data_points；二者都不存在时返回 None。
    关键流程：
        数据库导入校验使用 CSV 行数；实验 data_points 只用于发布统计，不用于导入。
    可能报错或边界情况：
        旧 demo 资产可能只有 data_points，且其值等于 demo CSV 行数，因此保留回退。
    """
    if asset.get("rows") is not None:
        return asset.get("rows")
    return asset.get("data_points")


class Command(BaseCommand):
    help = "Load public CEMP demo data from data/public_manifest.json."

    def add_arguments(self, parser):
        parser.add_argument("--manifest", default="data/public_manifest.json")
        parser.add_argument("--mode", choices=["demo", "paper"], default="demo")
        parser.add_argument("--append", action="store_true")

    def handle(self, *args, **options):
        """
        功能目的：
            根据 manifest 导入公开 demo 数据，生成可本地查询的最小数据库。
        输入参数：
            --manifest: manifest 路径；--mode: demo 或 paper；--append: 是否保留已有记录。
        返回值：
            通过 stdout 输出每个资产的导入结果。
        关键流程：
            过滤 required_for 中包含 mode 的本地 CSV 资产；每个模型只清空一次，
            再逐个导入，避免同一数据表由多个 CSV 组成时被后续文件覆盖。
        可能报错或边界情况：
            模型归档等非 CSV 资产缺少 local_path 时会跳过，不影响 demo 导入。
        """
        manifest_path = Path(options["manifest"])
        if not manifest_path.exists():
            raise CommandError(f"Manifest not found: {manifest_path}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assets = manifest.get("assets", [])
        mode = options["mode"]
        loaded = 0
        cleared_models = set()

        with transaction.atomic():
            for asset in assets:
                if mode not in asset.get("required_for", []):
                    continue
                if asset.get("format") != "csv" or not asset.get("local_path"):
                    self.stdout.write(f"skip {asset.get('name')} (not a local CSV asset)")
                    continue
                if not asset.get("django_model"):
                    self.stdout.write(f"skip {asset.get('name')} (no django_model loader)")
                    continue

                csv_path = manifest_path.parent.parent / asset["local_path"]
                if not csv_path.exists():
                    raise CommandError(f"Required data file not found: {csv_path}")

                model = resolve_model(asset["django_model"])
                model_label = model._meta.label_lower
                if not options["append"] and model_label not in cleared_models:
                    model.objects.all().delete()
                    cleared_models.add(model_label)
                count = load_csv(model, csv_path)
                loaded += count
                expected_count = expected_asset_count(asset)
                if expected_count is not None and expected_count != count:
                    raise CommandError(
                        f"Count mismatch for {asset['name']}: expected {expected_count}, loaded {count}"
                    )
                self.stdout.write(self.style.SUCCESS(f"loaded {count} records into {asset['django_model']}"))

        self.stdout.write(self.style.SUCCESS(f"public data load complete: {loaded} records"))
