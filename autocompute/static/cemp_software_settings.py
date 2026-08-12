"""CEMP 科学计算工作流的共享软件路径配置。"""

from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import Dict, Optional


ENVIRONMENT_KEYS = {
    "gaussian16_bin": "CEMP_GAUSSIAN16_BIN",
    "gaussian16_formchk": "CEMP_GAUSSIAN16_FORMCHK",
    "gaussian_database_path": "CEMP_GAUSSIAN_DATABASE_PATH",
    "orca_path": "CEMP_ORCA_PATH",
    "orca_2mkl_path": "CEMP_ORCA_2MKL_PATH",
    "orca_database_path": "CEMP_ORCA_DATABASE_PATH",
    "gmx_bin": "CEMP_GMX_BIN",
    "multiwfn_exe": "CEMP_MULTIWFFN_EXE",
    "sobtop_home": "CEMP_SOBTOP_HOME",
    "openmpi_bin": "CEMP_OPENMPI_BIN",
    "openmpi_lib": "CEMP_OPENMPI_LIB",
    "vmd_exe": "CEMP_VMD_BIN",
    "workflow_state_dir": "CEMP_WORKFLOW_STATE_DIR",
}


def _read_ini_values(config_path: Optional[str]) -> Dict[str, str]:
    """
    功能目的：读取可选的 CEMPsettings.ini，并兼容不同节名。
    输入参数：config_path 为显式配置文件；为空时读取 CEMP_SETTINGS_FILE 或系统默认路径。
    返回值：扁平化且键名为小写的配置字典。
    关键流程：按节遍历全部键值，后出现的同名键覆盖前值。
    可能报错或边界情况：文件不存在时返回空字典；格式错误时由 configparser 抛出明确异常。
    """
    selected = config_path or os.environ.get("CEMP_SETTINGS_FILE", "")
    if not selected:
        default_path = Path("/etc/cemp/CEMPsettings.ini")
        selected = str(default_path) if default_path.is_file() else ""
    if not selected:
        return {}

    path = Path(selected).expanduser()
    if not path.is_file():
        return {}

    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    values: Dict[str, str] = {key.lower(): value.strip() for key, value in parser.defaults().items()}
    for section in parser.sections():
        for key, value in parser.items(section):
            values[key.lower()] = value.strip()
    return values


def _prepend_environment_path(variable: str, value: str) -> None:
    """
    功能目的：把外部软件目录加入 PATH 或 LD_LIBRARY_PATH，且避免重复。
    输入参数：variable 为环境变量名，value 为待加入的目录。
    返回值：无；直接更新当前进程环境。
    关键流程：展开路径并置于现有搜索路径之前。
    可能报错或边界情况：空值不会修改环境；路径是否存在由调用工作流按需校验。
    """
    if not value:
        return
    normalized = str(Path(value).expanduser())
    current = [item for item in os.environ.get(variable, "").split(os.pathsep) if item]
    if normalized not in current:
        os.environ[variable] = os.pathsep.join([normalized, *current])


def _executable_parent(value: str) -> str:
    """当配置值是路径时返回其目录；仅给出命令名时不修改 PATH。"""
    if not value or os.path.sep not in value:
        return ""
    return str(Path(value).expanduser().parent)


def load_and_apply_settings(config_path: Optional[str] = None) -> Dict[str, str]:
    """
    功能目的：统一解析并应用 CEMP notebook 所需的科学软件路径。
    输入参数：config_path 为可选 INI 文件路径；环境变量始终具有最高优先级。
    返回值：包含规范键及历史兼容别名的字符串字典。
    关键流程：读取 INI、叠加环境变量、推导同目录工具，再更新 PATH 和 LD_LIBRARY_PATH。
    可能报错或边界情况：本函数不要求所有可选软件都存在；具体任务在启动前检查其必需项。
    """
    ini_values = _read_ini_values(config_path)
    result: Dict[str, str] = {}
    for key, environment_key in ENVIRONMENT_KEYS.items():
        result[key] = os.environ.get(environment_key, "").strip() or ini_values.get(key, "")

    gaussian_bin = result["gaussian16_bin"]
    if gaussian_bin and not result["gaussian16_formchk"]:
        result["gaussian16_formchk"] = str(Path(gaussian_bin).expanduser().with_name("formchk"))

    orca_path = result["orca_path"]
    if orca_path and not result["orca_2mkl_path"]:
        result["orca_2mkl_path"] = str(Path(orca_path).expanduser().with_name("orca_2mkl"))

    # 旧 notebook 使用 g16/gaussian16_exe；保留别名可避免改变计算主体。
    result["g16"] = result["gaussian16_bin"]
    result["gaussian16_exe"] = result["gaussian16_bin"]

    _prepend_environment_path("PATH", result["openmpi_bin"])
    _prepend_environment_path("LD_LIBRARY_PATH", result["openmpi_lib"])
    for executable_key in (
        "gaussian16_bin",
        "gaussian16_formchk",
        "orca_path",
        "orca_2mkl_path",
        "gmx_bin",
        "multiwfn_exe",
        "vmd_exe",
    ):
        _prepend_environment_path("PATH", _executable_parent(result[executable_key]))
    _prepend_environment_path("PATH", result["sobtop_home"])

    state_dir = result["workflow_state_dir"]
    if state_dir:
        Path(state_dir).expanduser().mkdir(parents=True, exist_ok=True)

    return result
