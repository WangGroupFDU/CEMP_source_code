import importlib.util
import sys
from pathlib import Path

from rdkit import RDConfig


def load_sascorer():
    """
    功能目的：
    加载 RDKit Contrib 中的 SA_Score 计算模块，兼容不同 RDKit 发行包的目录布局。

    输入参数：
    无。

    返回值：
    返回可调用 `calculateScore(mol)` 的 sascorer 模块对象。

    关键流程：
    优先使用 `rdkit.Contrib.SA_Score` 标准导入；如果当前 RDKit 未把 Contrib
    暴露为 Python 包，则从 `RDConfig.RDContribDir/SA_Score/sascorer.py` 直接加载。

    可能报错或边界情况：
    如果 RDKit 安装包不包含 SA_Score 文件，会抛出清晰的 `ModuleNotFoundError`。
    """
    try:
        from rdkit.Contrib.SA_Score import sascorer

        return sascorer
    except ImportError:
        pass

    contrib_dir = getattr(RDConfig, "RDContribDir", None)
    if not contrib_dir:
        raise ModuleNotFoundError("RDKit Contrib directory is unavailable; cannot load SA_Score.")

    sascorer_path = Path(contrib_dir) / "SA_Score" / "sascorer.py"
    if not sascorer_path.exists():
        raise ModuleNotFoundError("RDKit SA_Score module was not found under RDConfig.RDContribDir.")

    module_name = "rdkit_sa_scorer"
    spec = importlib.util.spec_from_file_location(module_name, str(sascorer_path))
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError("RDKit SA_Score module could not be loaded from file.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
