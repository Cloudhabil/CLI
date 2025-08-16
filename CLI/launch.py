#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
PY = str((VENV / "Scripts" / "python.exe") if os.name == "nt" else (VENV / "bin" / "python"))


def run(cmd, **kw):
    print("$ " + " ".join(map(str, cmd)))
    return subprocess.run(cmd, check=True, **kw)


def ensure_venv():
    if not VENV.exists():
        run([sys.executable, "-m", "venv", str(VENV)])
    run([PY, "-m", "pip", "install", "--upgrade", "pip"])
    run([PY, "-m", "pip", "install", "-r", str(HERE / "requirements.txt")])


def main():
    os.chdir(HERE)
    print("== Cloudhabil Launcher ==")
    ensure_venv()
    run([PY, str(HERE / "ensure_servers.py")])
    run([PY, str(HERE / "ch_cli.py"), "doctor"])
    print("\n✔ Entorno listo. Abriendo REPL (CodeGemma in-process).")
    print("Consejos: /help  |  /model qwen  |  /model deepseek  |  /file <ruta>  |  /exec\n")
    time.sleep(1)
    run([PY, str(HERE / "ch_repl.py")])


if __name__ == "__main__":
    main()
