

import sqlite3
import sys
import os
import argparse
from datetime import datetime, timezone

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public_example.sqlite3"
)


def main():
    parser = argparse.ArgumentParser(description="清理过期未激活用户")
    parser.add_argument("--delete", action="store_true", help="真正删除(默认dry-run)")
    parser.add_argument(
        "--days", type=int, default=30, help="超过多少天未激活的用户会被清理(默认30)"
    )
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, username, email, date_joined,
            CAST((julianday('now') - julianday(date_joined)) AS INTEGER) as days_ago
        FROM auth_user
        WHERE is_active = 0
          AND julianday('now') - julianday(date_joined) > ?
        ORDER BY date_joined
    """,
        (args.days,),
    )

    users = cursor.fetchall()

    if not users:
        print(f"没有超过 {args.days} 天未激活的用户。")
        conn.close()
        return

    print(f"找到 {len(users)} 个超过 {args.days} 天未激活的用户:\n")
    for u in users:
        print(f"  {u['username']:20s} | {u['email']:35s} | {u['days_ago']}天前注册")

    if not args.delete:
        print(f"\nDRY RUN — 添加 --delete 参数来执行删除。")
        conn.close()
        return

    user_ids = [u["id"] for u in users]
    placeholders = ",".join("?" * len(user_ids))

    
    related_tables = [
        "auth_user_groups",
        "auth_user_user_permissions",
        "authtoken_token",
        "django_admin_log",
    ]
    for table in related_tables:
        try:
            cursor.execute(
                f"DELETE FROM {table} WHERE user_id IN ({placeholders})", user_ids
            )
            deleted = cursor.rowcount
            if deleted:
                print(f"  清理 {table}: {deleted} 条记录")
        except sqlite3.OperationalError:
            pass

    
    try:
        cursor.execute(
            f"DELETE FROM register_profile WHERE user_id IN ({placeholders})", user_ids
        )
        if cursor.rowcount:
            print(f"  清理 register_profile: {cursor.rowcount} 条记录")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            f"DELETE FROM register_userprofile WHERE user_id IN ({placeholders})",
            user_ids,
        )
        if cursor.rowcount:
            print(f"  清理 register_userprofile: {cursor.rowcount} 条记录")
    except sqlite3.OperationalError:
        pass

    cursor.execute(f"DELETE FROM auth_user WHERE id IN ({placeholders})", user_ids)
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    print(f"\n完成: 删除了 {deleted} 个过期未激活用户。")


if __name__ == "__main__":
    main()
