import os

from mp_api.client import MPRester


def fetch_reference_materials(api_key):
    """
    功能目的：
        使用调用者提供的 Materials Project API key 拉取少量参考材料。
    输入参数：
        api_key: 通过 MP_API_KEY 环境变量提供的 API key。
    返回值：
        Materials Project summary 文档列表。
    关键流程：
        查询固定 material_id，用于检查 mp-api 配置是否可用。
    可能报错或边界情况：
        公开仓库不保存 API key；缺少环境变量时 main 会提前退出。
    """
    with MPRester(api_key) as mpr:
        return mpr.summary.search(material_ids=["mp-149", "mp-13", "mp-22526"])


def main():
    """
    功能目的：
        提供安全的 Materials Project 连接 smoke test。
    输入参数：
        无命令行参数，读取 MP_API_KEY 环境变量。
    返回值：
        无；成功时打印返回文档数量。
    关键流程：
        检查环境变量后再发起请求，避免导入模块时触发外部 API。
    可能报错或边界情况：
        API key 无权限、网络失败或 mp-api 版本不兼容时由 mp-api 抛出异常。
    """
    api_key = os.environ.get("MP_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("MP_API_KEY is required for this smoke test.")
    docs = fetch_reference_materials(api_key)
    print(f"Fetched {len(docs)} Materials Project records.")


if __name__ == "__main__":
    main()
