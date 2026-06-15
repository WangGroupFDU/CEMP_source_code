#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path


PUBLIC_TABLES = {
    "ionic_liquid_il": 1065,
    "ionic_liquid_il_ml_data": 100000,
    "ionic_liquid_cation_qc_data": 3774,
    "ionic_liquid_anion_qc_data": 2220,
    "polymer_experiment_polymer_data": 13116,
    "polymer_calculated_monomer_data": 10519,
    "polymer_calculated_polymer_data": 1000,
    "battery_manage_system_bms_experiment_result": 39,
}


def sha256_file(path):
    """
    功能目的：
        计算公开 SQLite 中间快照的 SHA256，供本地校验。
    输入参数：
        path: 快照文件路径。
    返回值：
        十六进制 SHA256 字符串。
    关键流程：
        分块读取文件，避免大文件一次性加载到内存。
    可能报错或边界情况：
        文件不存在或无读取权限时由 open 抛出异常。
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_create_sql(connection, table_name):
    """
    功能目的：
        从源 SQLite 中读取指定表的建表 SQL。
    输入参数：
        connection: 源 SQLite 连接。
        table_name: 表名。
    返回值：
        CREATE TABLE 语句。
    关键流程：
        查询 sqlite_master，确保只复制白名单表结构。
    可能报错或边界情况：
        源库缺表时抛出 RuntimeError，避免生成不完整快照。
    """
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    if row is None or not row[0]:
        raise RuntimeError(f"Source table not found: {table_name}")
    return row[0]


def copy_table(source, target, table_name):
    """
    功能目的：
        将白名单表从源 SQLite 复制到目标 SQLite。
    输入参数：
        source: 源 SQLite 连接。
        target: 目标 SQLite 连接。
        table_name: 要复制的表名。
    返回值：
        复制后的行数。
    关键流程：
        先创建表结构，再批量插入源表数据。
    可能报错或边界情况：
        表字段很多时仍按行批量复制；超大表会消耗较长时间但不会复制敏感表。
    """
    create_sql = fetch_create_sql(source, table_name)
    target.execute(create_sql)

    columns = [row[1] for row in source.execute(f"PRAGMA table_info({table_name})")]
    quoted_columns = ", ".join([f'"{column}"' for column in columns])
    placeholders = ", ".join(["?"] * len(columns))

    cursor = source.execute(f'SELECT {quoted_columns} FROM "{table_name}"')
    batch = []
    total = 0
    for row in cursor:
        batch.append(row)
        if len(batch) >= 1000:
            target.executemany(
                f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders})',
                batch,
            )
            total += len(batch)
            batch = []
    if batch:
        target.executemany(
            f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders})',
            batch,
        )
        total += len(batch)
    return total


def create_snapshot(source_path, output_path, metadata_path):
    """
    功能目的：
        生成只含公开数据表的 SQLite 快照和 JSON 元数据。
    输入参数：
        source_path: 私有完整 SQLite 路径。
        output_path: 公开快照输出路径。
        metadata_path: 元数据 JSON 输出路径。
    返回值：
        元数据字典。
    关键流程：
        删除已有输出；逐表复制白名单；校验行数；写入 SHA256、大小和行数。
    可能报错或边界情况：
        行数与预期不一致时抛错，避免错误资产被发布。
    """
    source_path = Path(source_path)
    output_path = Path(output_path)
    metadata_path = Path(metadata_path)

    if not source_path.exists():
        raise RuntimeError(f"Source SQLite not found: {source_path}")
    if output_path.exists():
        output_path.unlink()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    copied_rows = {}
    with sqlite3.connect(str(source_path)) as source, sqlite3.connect(str(output_path)) as target:
        for table_name, expected_rows in PUBLIC_TABLES.items():
            actual_rows = copy_table(source, target, table_name)
            if actual_rows != expected_rows:
                raise RuntimeError(
                    f"Row count mismatch for {table_name}: expected {expected_rows}, got {actual_rows}"
                )
            copied_rows[table_name] = actual_rows
        target.commit()

    metadata = {
        "asset": output_path.name,
        "license": "CC-BY-4.0",
        "sha256": sha256_file(output_path),
        "bytes": output_path.stat().st_size,
        "tables": copied_rows,
        "excluded_sensitive_tables": [
            "auth_user",
            "authtoken_token",
            "django_session",
            "django_admin_log",
            "tickets_ticket",
            "tickets_ticketmessage",
            "autocompute_computetask",
            "autocompute_computationtask",
        ],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return metadata


def main():
    """
    功能目的：
        命令行生成可供 CSV 导出的公开 SQLite 中间快照。
    输入参数：
        --source: 私有完整 SQLite；--output: 公开快照；--metadata: 元数据 JSON。
    返回值：
        无；成功时打印 SHA256 和输出路径。
    关键流程：
        严格使用 PUBLIC_TABLES 白名单，杜绝复制敏感运行态表。
    可能报错或边界情况：
        该脚本不上传资产；正式发布数据库时优先使用 tools/export_public_csv_assets.py 导出 CSV。
    """
    parser = argparse.ArgumentParser(description="Create sanitized CEMP SQLite intermediate for CSV export.")
    parser.add_argument("--source", default=os.environ.get("CEMP_PRIVATE_SQLITE", "db.sqlite3"))
    parser.add_argument("--output", default="release_assets/cemp_public_data.sqlite3")
    parser.add_argument("--metadata", default="release_assets/cemp_public_data.metadata.json")
    args = parser.parse_args()

    metadata = create_snapshot(args.source, args.output, args.metadata)
    print(f"created {args.output}")
    print(f"sha256 {metadata['sha256']}")


if __name__ == "__main__":
    main()
