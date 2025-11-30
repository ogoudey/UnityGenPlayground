# Author: Michael Gold


# This script creates a new env that fully contains python and any required libraries.
# The resulting env can be transferred to new windows machines for zero-install running.
# Requires conda and conda-pack to be installed to run this script.
# Does not require conda on the machine that runs the resulting env!

# To run:
# `conda activate <conda-env-name>`
# `python build_env.py`

# After this runs, you get:
# `py_env_win.zip`

# This zip contains:
# - `python.exe`
# - full stdlib
# - all libraries
# - activation scripts
# - relocatable paths (thanks to conda-pack)

# How the target machine uses it (no installs):
# `cd <path\to\AcroGen>`
# `tar -xf py_env_win.zip`
# `.\py_env\python.exe <whatever_script.py>`

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ENV_DIR = REPO_ROOT / "py_env"
ZIP_PATH = REPO_ROOT / "py_env_win.zip"
REQUIREMENTS = REPO_ROOT.parent / "requirements.txt"

def run(cmd, **kwargs):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True, text=True, **kwargs)
    return result

def main():
    # Step 1 — Create conda env inside repo
    if ENV_DIR.exists():
        print(f"[INFO] Removing existing env at {ENV_DIR}")
        import shutil
        shutil.rmtree(ENV_DIR)

    print("[STEP] Creating conda environment...")
    run([
        "conda", "create",
        "-p", str(ENV_DIR),
        "python",
        "-y"
    ])

    # Step 2 — Install requirements into this env
    print("[STEP] Installing requirements...")
    run(["conda", "run", "-p", str(ENV_DIR), "pip", "install", "-r", str(REQUIREMENTS)])

    # Step 3 — Ensure conda-pack is installed (in base env)
    print("[STEP] Ensuring conda-pack is installed...")
    try:
        run(["conda-pack", "--version"])
    except:
        run(["conda", "install", "-n", "base", "conda-pack", "-y"])

    # Step 4 — Pack env
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    print("[STEP] Packing environment to py_env_win.zip...")
    run([
        "conda-pack",
        "-p", str(ENV_DIR),
        "-o", str(ZIP_PATH)
    ])

    print("\n============================================")
    print("Environment successfully packed!")
    print(f"Created: {ZIP_PATH}")
    print("============================================")

if __name__ == "__main__":
    main()
