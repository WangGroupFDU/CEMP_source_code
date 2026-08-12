"""CEMP 公开版本中可达算法 notebook 的唯一白名单。"""

from __future__ import annotations

from typing import Dict, Iterable, Tuple


STANDARD_MD_NOTEBOOKS = (
    "1_Polymer_RESP_repeat_unit.ipynb",
    "2_Polymer_chg_and_Polymer_creation_ Linear_polymer.ipynb",
    "3_create_Polymer_itp_top.ipynb",
    "4_generate_Gaussian_inputfile.ipynb",
    "5_opt+freq_calculation.ipynb",
    "6_opt+freq_failure_correction.ipynb",
    "7_opt+freq_imaginary_frequencies.ipynb",
    "8_MD_process.ipynb",
    "9_post_analysis.ipynb",
    "11_component_energy_calculation.ipynb",
    "12_calculate_solvent_cage_escape_energy.ipynb",
    "13_coordination_environment_distribution.ipynb",
)

ORCA_MD_NOTEBOOKS = (
    "1_Polymer_RESP_repeat_unit.ipynb",
    "2_Polymer_chg_and_Polymer_creation_ Linear_polymer.ipynb",
    "3_create_Polymer_itp_top.ipynb",
    "4_generate_Gaussian_inputfile.ipynb",
    "5_opt+freq_calculation.ipynb",
    "6_opt+freq_imaginary_frequencies.ipynb",
    "8_MD_process.ipynb",
    "9_post_analysis.ipynb",
)

GAUSSIAN_SINGLE_POINT = tuple(
    f"Gas_component_{index}_{suffix}.ipynb"
    for index, suffix in (
        (1, "generate_Gaussian_inputfile"),
        (2, "opt+freq_calculation"),
        (3, "opt+freq_failure_correction"),
        (4, "opt+freq_imaginary_frequencies"),
        (5, "energy_calculation"),
        (6, "energy_failure_correction"),
        (7, "Extracting_energy_and_free_energy_corrections"),
    )
)

GAUSSIAN_BINDING = tuple(
    f"Gas_{species}_{index}_{suffix}.ipynb"
    for species in ("component", "dimer")
    for index, suffix in (
        (1, "generate_Gaussian_inputfile"),
        (2, "opt+freq_calculation"),
        (3, "opt+freq_failure_correction"),
        (4, "opt+freq_imaginary_frequencies"),
        (5, "energy_calculation"),
        (6, "energy_failure_correction"),
        (7, "Extracting_energy_and_free_energy_corrections"),
    )
) + ("Data_processing .ipynb",)

GAUSSIAN_PKA = tuple(
    f"pkb_DFT_{index}_{suffix}.ipynb"
    for index, suffix in (
        (1, "generate_Gaussian_inputfile"),
        (2, "opt+freq_calculation"),
        (3, "opt+freq_failure_correction"),
        (4, "opt+freq_imaginary_frequencies"),
        (5, "energy_calculation"),
        (6, "energy_failure_correction"),
        (7, "Extracting_energy_and_free_energy_corrections"),
    )
)

GAUSSIAN_OX_RED = tuple(
    f"ox_red_{index}_{suffix}.ipynb"
    for index, suffix in (
        (1, "generate_Gaussian_inputfile"),
        (2, "opt+freq_calculation"),
        (3, "opt+freq_failure_correction"),
        (4, "opt+freq_imaginary_frequencies"),
        (5, "energy_calculation"),
        (6, "energy_failure_correction"),
        (7, "Extracting_energy_and_free_energy_corrections"),
    )
)

GAUSSIAN_REACTION_THERMO = tuple(
    f"reaction_thermo_{index}_{suffix}.ipynb"
    for index, suffix in (
        (1, "generate_Gaussian_inputfile"),
        (2, "opt+freq_calculation"),
        (3, "opt+freq_failure_correction"),
        (4, "opt+freq_imaginary_frequencies"),
        (5, "energy_calculation"),
        (6, "Extracting_energy_and_free_energy_corrections"),
    )
)

GAUSSIAN_GLOBAL_REACTION = tuple(
    f"reaction_{index}_{suffix}.ipynb"
    for index, suffix in (
        (1, "generate_Gaussian_inputfile"),
        (2, "opt+freq_calculation"),
        (3, "opt+freq_failure_correction"),
        (4, "opt+freq_imaginary_frequencies"),
        (5, "energy_calculation"),
        (6, "Extracting_energy_and_free_energy_corrections"),
    )
)

ORCA_SINGLE_POINT = tuple(
    f"ORCA_Gas_{index}_{suffix}.ipynb"
    for index, suffix in (
        (1, "generate_ORCA_inputfile"),
        (2, "opt+freq_calculation"),
        (3, "opt+freq_imaginary_frequencies"),
        (4, "energy_calculation"),
        (5, "Extracting_energy_and_free_energy_corrections"),
    )
)

ORCA_BINDING = tuple(
    f"ORCA_Gas_{species}_{index}_{suffix}.ipynb"
    for species in ("component", "dimer")
    for index, suffix in (
        (1, "generate_ORCA_inputfile"),
        (2, "opt+freq_calculation"),
        (3, "opt+freq_imaginary_frequencies"),
        (4, "energy_calculation"),
        (5, "Extracting_energy_and_free_energy_corrections"),
    )
)

ORCA_OX_RED = tuple(
    f"ORCA_ox_red_{index}_{suffix}.ipynb"
    for index, suffix in (
        (1, "generate_ORCA_inputfile"),
        (2, "opt+freq_calculation"),
        (3, "opt+freq_imaginary_frequencies"),
        (4, "energy_calculation"),
        (5, "Extracting_energy_and_free_energy_corrections"),
    )
)

ORCA_MANUAL_OPT_FREQ = (
    "ORCA_Gas_2_opt+freq_calculation.ipynb",
    "ORCA_Gas_3_opt+freq_imaginary_frequencies.ipynb",
    "ORCA_Gas_4_energy_calculation.ipynb",
    "ORCA_Gas_5_Extracting_energy_and_free_energy_corrections.ipynb",
)

ORCA_MANUAL_ENERGY = (
    "ORCA_Gas_1_energy_calculation.ipynb",
    "ORCA_Gas_2_Extracting_energy.ipynb",
)

POLYMER_GENERATION_NOTEBOOKS = (
    "1_Polymer_RESP_repeat_unit.ipynb",
    "2_Polymer_chg_and_Polymer_creation_Linear_polymer.ipynb",
    "3_create_Polymer_itp_top.ipynb",
)


def _entry(
    task_type: str,
    source_dir: str,
    notebooks: Tuple[str, ...],
    runner: str,
    dependencies: Tuple[str, ...],
) -> Dict[str, object]:
    """
    功能目的：构造统一的公开算法登记项。
    输入参数：任务类型、源码目录、顺序 notebook、执行函数和外部依赖。
    返回值：可供校验器和文档读取的字典。
    关键流程：保持 notebook 元组顺序，顺序即实际执行顺序。
    可能报错或边界情况：登记项本身不访问文件，文件存在性由发布校验器检查。
    """
    return {
        "task_type": task_type,
        "source_dir": source_dir,
        "notebooks": notebooks,
        "runner": runner,
        "dependencies": dependencies,
    }


WORKFLOW_GROUPS = (
    _entry("MDCoumpute", "autocompute/static/MDAutocompute_programe", STANDARD_MD_NOTEBOOKS, "autocompute.remote_utils.run_Gromacs_MD_notebook_tasks_remote", ("Gaussian 16", "GROMACS", "Sobtop", "Multiwfn", "Open Babel", "VMD")),
    _entry("MDCoumpute_ORCA", "autocompute/static/MDAutocompute_programe_ORCA", ORCA_MD_NOTEBOOKS, "autocompute.run_MD_QC_utils.run_Gromacs_MD_notebook_tasks_ORCA", ("ORCA", "GROMACS", "Sobtop", "Multiwfn", "Open Babel", "Open MPI", "VMD")),
    _entry("HTQC_single_point_energy", "autocompute/static/QcAutocompute_programe/HTQC_single_point_energy", GAUSSIAN_SINGLE_POINT, "autocompute.remote_utils.run_Gaussian_single_point_energy_notebook_tasks_remote", ("Gaussian 16", "Multiwfn")),
    _entry("HTQC_binding_energy", "autocompute/static/QcAutocompute_programe/HTQC_binding_energy", GAUSSIAN_BINDING, "autocompute.remote_utils.run_Gaussian_binding_energy_notebook_tasks_remote", ("Gaussian 16", "Multiwfn")),
    _entry("HTQC_pka_pkb_calculation", "autocompute/static/QcAutocompute_programe/HTQC_pka_pkb", GAUSSIAN_PKA, "autocompute.remote_utils.run_Gaussian_pka_pkb_notebook_tasks_remote", ("Gaussian 16", "Multiwfn")),
    _entry("HTQC_ox_red_calculation", "autocompute/static/QcAutocompute_programe/HTQC_ox_red", GAUSSIAN_OX_RED, "autocompute.remote_utils.run_Gaussian_ox_red_notebook_tasks_remote", ("Gaussian 16", "Multiwfn")),
    _entry("HTQC_reaction_thermo_properties_calculation", "autocompute/static/QcAutocompute_programe/HTQC_reaction_thermo", GAUSSIAN_REACTION_THERMO, "autocompute.remote_utils.run_Gaussian_reaction_thermo_notebook_tasks_remote", ("Gaussian 16", "Multiwfn")),
    _entry("HTQC_global_reaction_properties_descriptors_calculation", "autocompute/static/QcAutocompute_programe/HTQC_global_reaction_descriptors_calculation", GAUSSIAN_GLOBAL_REACTION, "autocompute.remote_utils.run_Gaussian_global_reaction_properties_notebook_tasks_remote", ("Gaussian 16", "Multiwfn")),
    _entry("HTQC_single_point_energy_orca", "autocompute/static/QcAutocompute_programe/ORCA_HTQC_single_point_energy", ORCA_SINGLE_POINT, "autocompute.remote_utils.run_ORCA_single_point_energy_notebook_tasks_remote", ("ORCA", "Open MPI", "Multiwfn")),
    _entry("HTQC_binding_energy_orca", "autocompute/static/QcAutocompute_programe/ORCA_HTQC_binding_energy", ORCA_BINDING, "autocompute.remote_utils.run_ORCA_binding_energy_notebook_tasks_remote", ("ORCA", "Open MPI", "Multiwfn")),
    _entry("HTQC_ox_red_calculation_orca", "autocompute/static/QcAutocompute_programe/ORCA_HTQC_ox_red", ORCA_OX_RED, "autocompute.remote_utils.run_ORCA_ox_red_notebook_tasks_remote", ("ORCA", "Open MPI", "Multiwfn")),
    _entry("Manual_Mode_QCcompute", "autocompute/static/QcAutocompute_programe/ORCA_manual_mode_opt+freq_energy", ORCA_MANUAL_OPT_FREQ, "autocompute.remote_utils.run_ORCA_manual_notebook_tasks_remote", ("ORCA", "Open MPI", "Multiwfn")),
    _entry("Manual_Mode_QCcompute_energy", "autocompute/static/QcAutocompute_programe/ORCA_manual_mode_energy", ORCA_MANUAL_ENERGY, "autocompute.remote_utils.run_ORCA_manual_notebook_tasks_remote_energy", ("ORCA", "Open MPI")),
    _entry("DrawESP", "autocompute/static/drawESP", ("auto_draw_ESP.ipynb",), "autocompute.remote_utils.run_draw_ESP_notebook_tasks_remote", ("Gaussian 16", "Multiwfn", "VMD")),
    _entry("DrawESP_remote", "autocompute/static/drawESP", ("auto_draw_ESP_gbw.ipynb",), "autocompute.remote_utils.run_draw_ESP_notebook_tasks_gbw_remote", ("ORCA", "Multiwfn", "VMD")),
    _entry("Draw_HOMO_LUMO_orb", "autocompute/static/draw_HOMO_LUMO_orb", ("draw_HOMO_LUMO_orb.ipynb",), "autocompute.remote_utils.run_draw_HOMO_LUMO_orb_notebook_tasks_remote", ("Multiwfn", "VMD")),
    _entry("NCI_analysis", "autocompute/static/NCIanalysis", ("NCI_analysis.ipynb",), "autocompute.remote_utils.run_NCI_SCF_analysis_notebook_tasks_remote", ("Gaussian 16", "Multiwfn", "VMD")),
    _entry("NCI_promolecular_analysis", "autocompute/static/NCI_analysis_promolecular", ("NCI_analysis_promolecular.ipynb",), "autocompute.remote_utils.run_NCI_promolecular_analysis_notebook_tasks_remote", ("Multiwfn", "VMD")),
    _entry("From_SMILES_to_Name", "autocompute/static/query_SMILES", ("query_simliar_monomer.ipynb",), "autocompute.run_MD_QC_utils.run_query_name_CAS_tasks", ("Open Babel",)),
    *(
        _entry(
            f"Generate_{geometry}_{composition}",
            f"polymer/static/programe/generate_{'cyclic_' if geometry == 'cyclic' else ''}{composition}",
            POLYMER_GENERATION_NOTEBOOKS,
            "polymer.remote_utils.generate_polymer_run_notebook_tasks_remote",
            ("Gaussian 16", "GROMACS", "Sobtop", "Multiwfn", "Open Babel"),
        )
        for geometry in ("linear", "cyclic")
        for composition in ("homopolymer", "random_copolymer", "block_copolymer")
    ),
)

INFERENCE_NOTEBOOKS = (
    "ionic_liquid/static/model/prediction_model.ipynb",
    "ionic_liquid/static/program/predict_IL_properties_SMILES_single/1_IL_predict_with_xgboost.ipynb",
    "ionic_liquid/static/program/predict_IL_properties_excel_batch/1_IL_predict_with_xgboost.ipynb",
    "polymer/static/programe/predict_copolymer_property/1_predict_copolymer_property.ipynb",
    "polymer/static/programe/predict_polymer_properties/predict_polymer_property.ipynb",
)

WORKFLOW_HELPER_MODULES = (
    "autocompute/static/MDAutocompute_programe/md_qc_database_utils.py",
    "autocompute/static/QcAutocompute_programe/HTQC_binding_energy/qc_database_utils.py",
    "autocompute/static/QcAutocompute_programe/HTQC_global_reaction_descriptors_calculation/qc_database_utils.py",
    "autocompute/static/QcAutocompute_programe/HTQC_ox_red/qc_database_utils.py",
    "autocompute/static/QcAutocompute_programe/HTQC_pka_pkb/qc_database_utils.py",
    "autocompute/static/QcAutocompute_programe/HTQC_reaction_thermo/qc_database_utils.py",
    "autocompute/static/QcAutocompute_programe/HTQC_single_point_energy/qc_database_utils.py",
    "autocompute/static/QcAutocompute_programe/ORCA_HTQC_binding_energy/qc_database_utils.py",
    "autocompute/static/QcAutocompute_programe/ORCA_HTQC_ox_red/qc_database_utils.py",
    "autocompute/static/QcAutocompute_programe/ORCA_HTQC_single_point_energy/qc_database_utils.py",
    "polymer/static/programe/predict_copolymer_property/utils.py",
    "polymer/static/programe/predict_polymer_properties/utils.py",
)


def iter_workflow_notebooks() -> Iterable[str]:
    """
    功能目的：按登记顺序生成全部计算工作流 notebook 路径。
    输入参数：无。
    返回值：相对仓库根目录的路径迭代器。
    关键流程：拼接每组 source_dir 和 notebook 文件名。
    可能报错或边界情况：重复路径会在模块级断言中被拒绝。
    """
    for group in WORKFLOW_GROUPS:
        source_dir = str(group["source_dir"])
        for notebook in group["notebooks"]:
            yield f"{source_dir}/{notebook}"


WORKFLOW_NOTEBOOKS = tuple(iter_workflow_notebooks())
ACTIVE_NOTEBOOKS = WORKFLOW_NOTEBOOKS + INFERENCE_NOTEBOOKS

if len(WORKFLOW_NOTEBOOKS) != 118 or len(set(WORKFLOW_NOTEBOOKS)) != 118:
    raise RuntimeError("The public workflow inventory must contain 118 unique notebooks.")
if len(ACTIVE_NOTEBOOKS) != 123 or len(set(ACTIVE_NOTEBOOKS)) != 123:
    raise RuntimeError("The public algorithm inventory must contain 123 unique notebooks.")
