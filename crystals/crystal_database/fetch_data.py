import argparse
import os

import pandas as pd
from mp_api.client import MPRester


FIELDS_REQUESTED = [
    "material_id",
    "is_magnetic",
    "ordering",
    "total_magnetization",
    "builder_meta",
    "nsites",
    "elements",
    "nelements",
    "composition",
    "composition_reduced",
    "formula_pretty",
    "formula_anonymous",
    "chemsys",
    "volume",
    "density",
    "density_atomic",
    "symmetry",
    "property_name",
    "deprecated",
    "deprecation_reasons",
    "last_updated",
    "origins",
    "warnings",
    "structure",
    "task_ids",
    "uncorrected_energy_per_atom",
    "energy_per_atom",
    "formation_energy_per_atom",
    "energy_above_hull",
    "is_stable",
    "equilibrium_reaction_energy_per_atom",
    "decomposes_to",
    "xas",
    "grain_boundaries",
    "band_gap",
    "cbm",
    "vbm",
    "efermi",
    "is_gap_direct",
    "is_metal",
    "es_source_calc_id",
    "bandstructure",
    "dos",
    "dos_energy_up",
    "dos_energy_down",
    "total_magnetization_normalized_vol",
    "total_magnetization_normalized_formula_units",
    "num_magnetic_sites",
    "num_unique_magnetic_sites",
    "types_of_magnetic_species",
    "k_voigt",
    "k_reuss",
    "k_vrh",
    "g_voigt",
    "g_reuss",
    "g_vrh",
    "universal_anisotropy",
    "homogeneous_poisson",
    "e_total",
    "e_ionic",
    "e_electronic",
    "n",
    "e_ij_max",
    "weighted_surface_energy_EV_PER_ANG2",
    "weighted_surface_energy",
    "weighted_work_function",
    "surface_anisotropy",
    "shape_factor",
    "has_reconstructed",
    "possible_species",
    "has_props",
    "theoretical",
]


def fetch_data_element(element, api_key, output_dir):
    """
    功能目的：
        从 Materials Project 拉取指定元素相关的晶体摘要数据，并保存为 CSV。
    输入参数：
        element: 元素符号，例如 Li 或 Na。
        api_key: Materials Project API key，必须从环境变量或命令行传入。
        output_dir: CSV 输出目录。
    返回值：
        输出 CSV 的绝对路径。
    关键流程：
        使用 mp_api 查询 summary 数据；将返回对象转为普通字典；写入以元素命名的 CSV。
    可能报错或边界情况：
        缺少 API key 会在 main 中提前报错；Materials Project 网络或权限错误会由 mp_api 抛出。
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{element}_crystal.csv")

    with MPRester(api_key) as mpr:
        docs = mpr.summary.search(elements=[element], fields=FIELDS_REQUESTED)

    rows = []
    for doc in docs:
        if hasattr(doc, "model_dump"):
            rows.append(doc.model_dump())
        elif hasattr(doc, "dict"):
            rows.append(doc.dict())
        else:
            rows.append(dict(doc))

    pd.DataFrame(rows).to_csv(output_path, index=False)
    return output_path


def main():
    """
    功能目的：
        提供可复现的命令行入口，避免在导入模块时触发远程 API 请求。
    输入参数：
        命令行参数 --elements、--output-dir、--api-key。
    返回值：
        无；成功时打印每个生成文件路径。
    关键流程：
        优先读取命令行 API key，其次读取 MP_API_KEY 环境变量。
    可能报错或边界情况：
        公开仓库不保存任何 API key；调用者必须自行申请并通过环境变量传入。
    """
    parser = argparse.ArgumentParser(description="Fetch public Materials Project crystal data.")
    parser.add_argument("--elements", nargs="+", default=["Li", "Na", "K", "Al", "Ca", "Mg", "Zn", "Ba"])
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--api-key", default=os.environ.get("MP_API_KEY", ""))
    args = parser.parse_args()

    if not args.api_key.strip():
        raise SystemExit("MP_API_KEY is required. Set it in the environment or pass --api-key.")

    for element in args.elements:
        output_path = fetch_data_element(element, args.api_key.strip(), args.output_dir)
        print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
