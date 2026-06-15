#!/usr/bin/env python3
"""Print the public release preparation checklist."""


def main():
    """
    功能目的：
        输出公开发布前的最小检查命令，方便维护者复用。
    输入参数：
        无。
    返回值：
        无；向 stdout 打印命令。
    关键流程：
        只输出检查步骤，不修改任何文件。
    可能报错或边界情况：
        该脚本不替代人工审计、CSV 导出和 GitHub Release 发布流程。
    """
    print("python -m compileall -q .")
    print("python manage.py check")
    print("python manage.py test")
    print("python manage.py verify_public_release --manifest data/public_manifest.json")


if __name__ == "__main__":
    main()
