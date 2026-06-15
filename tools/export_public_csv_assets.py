import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path


TABLE_EXPORTS = [
    {
        "name": "autocompute_cation_qc",
        "table": "ionic_liquid_cation",
        "output": "autocompute_cation_qc.csv",
        "count_key": "data_points",
    },
    {
        "name": "autocompute_anion_qc",
        "table": "ionic_liquid_anion",
        "output": "autocompute_anion_qc.csv",
        "count_key": "data_points",
    },
    {
        "name": "autocompute_ionic_liquid_qc",
        "table": "ionic_liquid_il",
        "output": "autocompute_ionic_liquid_qc.csv",
        "count_key": "data_points",
    },
    {
        "name": "autocompute_electrolyte_qc",
        "table": "ionic_liquid_electrolyte",
        "output": "autocompute_electrolyte_qc.csv",
        "count_key": "data_points",
    },
    {
        "name": "autocompute_li_electrolyte_qc",
        "table": "ionic_liquid_li_electrolyte",
        "output": "autocompute_li_electrolyte_qc.csv",
        "count_key": "data_points",
    },
    {
        "name": "autocompute_metal_anion_binding_energy",
        "table": "ionic_liquid_metal_anion_energy",
        "output": "autocompute_metal_anion_binding_energy.csv",
        "count_key": "data_points",
    },
    {
        "name": "autocompute_example_small_molecules",
        "table": "ionic_liquid_example",
        "output": "autocompute_example_small_molecules.csv",
        "count_key": "data_points",
    },
]


def sha256_file(path):
    """
    功能目的：计算公开数据文件的 SHA256。
    输入参数：path，待计算的本地文件路径。
    返回值：十六进制 SHA256 字符串。
    关键流程：按 1 MB 分块读取，避免大 CSV 一次进入内存。
    边界情况：文件不存在时由 open 抛出 FileNotFoundError。
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(output_path, header, rows):
    """
    功能目的：按公开发布要求写出 RFC 4180 风格 CSV。
    输入参数：
        output_path: 输出 CSV 路径。
        header: 表头字段名序列。
        rows: 可迭代的数据行。
    返回值：写出的数据行数量，不包含表头。
    关键流程：使用 utf-8-sig 写入 BOM，csv.writer 负责逗号、引号和换行转义，
        lineterminator 固定为 CRLF，方便 Excel 在 macOS/Windows 打开。
    边界情况：None 值写为空字符串，避免导出 Python 字面量 None。
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\r\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow(["" if value is None else value for value in row])
            count += 1
    return count


def export_sqlite_table(connection, table_name, output_path):
    """
    功能目的：从 SQLite 中导出一个白名单公开表。
    输入参数：
        connection: sqlite3 数据库连接。
        table_name: 需要导出的表名。
        output_path: 输出 CSV 路径。
    返回值：导出的数据点数量。
    关键流程：读取 PRAGMA table_info 得到稳定列顺序，再 SELECT 全表。
    边界情况：表不存在或没有字段时主动抛出 RuntimeError，避免生成空假文件。
    """
    cursor = connection.cursor()
    columns = [row[1] for row in cursor.execute(f"PRAGMA table_info({table_name})")]
    if not columns:
        raise RuntimeError(f"SQLite table not found or has no columns: {table_name}")
    rows = cursor.execute(f"SELECT * FROM {table_name}")
    return write_csv(output_path, columns, rows)


def normalise_csv(input_path, output_path):
    """
    功能目的：把已有 CSV 规范化为公开发布格式。
    输入参数：
        input_path: 原始 CSV 路径。
        output_path: 规范化后的输出路径。
    返回值：数据行数量，不包含表头。
    关键流程：utf-8-sig 读取以兼容已有 BOM；再统一写为 UTF-8 BOM + CRLF。
    边界情况：空 CSV 会抛出 RuntimeError，因为公开数据资产必须有表头。
    """
    with input_path.open("r", encoding="utf-8-sig", newline="") as input_handle:
        reader = csv.reader(input_handle)
        try:
            header = next(reader)
        except StopIteration:
            raise RuntimeError(f"CSV file is empty: {input_path}")
        return write_csv(output_path, header, reader)


def describe_asset(name, output_path, count_key, count):
    """
    功能目的：生成 manifest 更新所需的资产摘要。
    输入参数：
        name: 资产名称。
        output_path: 输出文件路径。
        count_key: 计数字段名，实验/理论数据为 data_points，ML 数据为 rows。
        count: 数据点或行数。
    返回值：包含文件名、大小、SHA256 和计数的字典。
    关键流程：所有值来自导出后的最终文件，避免记录源文件旧校验。
    边界情况：output_path 必须已存在。
    """
    return {
        "name": name,
        "path": str(output_path),
        "bytes": output_path.stat().st_size,
        "sha256": sha256_file(output_path),
        count_key: count,
    }


def main():
    """
    功能目的：导出 GitHub 公开发布所需的 CSV 数据资产。
    输入参数：
        --sqlite-path: 完整 CEMP SQLite 数据库路径。
        --polymer-prediction-csv: OMG polymer ML 预测结果 CSV。
        --output-dir: 公开 CSV 输出目录，默认 data/public。
    返回值：向 stdout 输出 JSON 摘要，供同步 manifest。
    关键流程：先导出 autocompute/Database 白名单小分子表，再规范化 polymer ML CSV。
    边界情况：不会导出用户、token、session、任务、日志、ticket 或上传文件表。
    """
    parser = argparse.ArgumentParser(description="Export public CEMP CSV data assets.")
    parser.add_argument("--sqlite-path", required=True)
    parser.add_argument("--polymer-prediction-csv", required=True)
    parser.add_argument("--output-dir", default="data/public")
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite_path).expanduser().resolve()
    polymer_prediction_csv = Path(args.polymer_prediction_csv).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser()
    if not sqlite_path.is_file():
        raise SystemExit(f"SQLite database not found: {sqlite_path}")
    if not polymer_prediction_csv.is_file():
        raise SystemExit(f"Polymer prediction CSV not found: {polymer_prediction_csv}")

    summaries = []
    with sqlite3.connect(str(sqlite_path)) as connection:
        for item in TABLE_EXPORTS:
            output_path = output_dir / item["output"]
            count = export_sqlite_table(connection, item["table"], output_path)
            summaries.append(describe_asset(item["name"], output_path, item["count_key"], count))

    polymer_output = output_dir / "polymer_predicted_omg_deepsa_cemp_property.csv"
    polymer_count = normalise_csv(polymer_prediction_csv, polymer_output)
    summaries.append(
        describe_asset(
            "polymer_predicted_omg_deepsa_cemp_property",
            polymer_output,
            "rows",
            polymer_count,
        )
    )

    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
