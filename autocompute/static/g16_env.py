


import os, subprocess, shlex, textwrap, signal

def load_gaussian_env(
    g16root="/root/Gaussian16_Linux_AVX2/tar",
    timeout_sec=10
):
    profile = f"{g16root}/g16/bsd/g16.profile"
    if not os.path.exists(profile):
        raise FileNotFoundError(f"{profile} not found")

    
    bash_cmd = [
        "bash", "--noprofile", "--norc", "-c",
        f"source {shlex.quote(profile)} && env"
    ]
    
    env = os.environ.copy()
    env["g16root"] = g16root                      
    
    env["GAUSS_SCRDIR"] = f"{g16root}/g16/scratch"

    
    try:
        env_text = subprocess.check_output(
            bash_cmd,
            timeout=timeout_sec, 
            env=env
        ).decode()
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"Loading Gaussian env timed-out after {timeout_sec}s "
            "(suspect profile hang)."
        )

    
    for line in env_text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ[k] = v

    
    g16_bin = f"{g16root}/g16"
    os.environ["PATH"] = g16_bin + os.pathsep + os.environ["PATH"]

    
    import shutil
    g16_path = shutil.which("g16")
    if g16_path:
        print("✅ Gaussian16 environment loaded:")
        print("   g16 =", g16_path)
        print("   GAUSS_EXEDIR =", os.getenv("GAUSS_EXEDIR"))
    else:
        raise RuntimeError("g16 still not found in PATH")