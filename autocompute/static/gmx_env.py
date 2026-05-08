"""
gromacs_env.py
========================================
Utility for injecting GROMACS (gmx) command-line tools into the current
Python process / Jupyter kernel by prepending the GROMACS *bin* directory
to the PATH.  Designed for cases where Jupyter does not inherit the user's
~/.bashrc and therefore cannot find the `gmx` executable.

Author  : ChatGPT (OpenAI)
License : MIT
----------------------------------------------------------------------
Basic usage inside a notebook
-----------------------------
from gromacs_env import load_gromacs_env
load_gromacs_env("/home/fwtop/apps/gromacs-2018.8/bin")   # optional arg

!gmx --version
"""

import os
import shutil
from pathlib import Path
from typing import Union

__all__ = ["load_gromacs_env"]

def load_gromacs_env(
    gmx_bin: Union[str, Path] = "/home/fwtop/apps/gromacs-2018.8/bin"
) -> None:
    """
    Prepend *gmx_bin* to ``$PATH`` so that the GROMACS command-line tool
    `gmx` can be invoked from Python / Jupyter.

    Parameters
    ----------
    gmx_bin : str or pathlib.Path, optional
        Directory that contains the `gmx` executable.  Default is
        ``/home/fwtop/apps/gromacs-2018.8/bin``.

    Raises
    ------
    FileNotFoundError
        If *gmx_bin* does not exist or is not a directory.
    RuntimeError
        If `gmx` still cannot be located after PATH injection.

    Notes
    -----
    * The function is idempotent; calling it multiple times is harmless.
    * It intentionally avoids reading the user's shell start-up files,
      making it very fast and predictable inside notebook environments.
    """

    gmx_bin = Path(gmx_bin).expanduser().resolve()

    if not gmx_bin.is_dir():
        raise FileNotFoundError(f"{gmx_bin} is not a valid directory")

    
    current_path = os.environ.get("PATH", "")
    path_parts = current_path.split(os.pathsep)

    gmx_str = str(gmx_bin)
    if gmx_str not in path_parts:
        os.environ["PATH"] = gmx_str + os.pathsep + current_path

    
    gmx_exec = shutil.which("gmx")
    if gmx_exec is None:
        raise RuntimeError(
            "`gmx` executable still not found after PATH modification. "
            f"Check contents of {gmx_bin}."
        )

    print("✅ GROMACS environment loaded successfully")
    print("   gmx executable :", gmx_exec)
    print("   PATH head      :", os.environ['PATH'].split(os.pathsep)[0])