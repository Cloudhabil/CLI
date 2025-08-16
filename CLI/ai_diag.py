# ai_diag.py
# Herramienta de diagnóstico minimalista para CLIs/IA
from __future__ import annotations
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import textwrap
import traceback
from datetime import datetime
from pathlib import Path

DEF_CACHE = Path(".cache/diag")
DEF_CACHE.mkdir(parents=True, exist_ok=True)
PENDING = DEF_CACHE / "pending.json"          # marca de error sin resolver
RESUMEN = DEF_CACHE / "last_error_summary.txt"


def _nowstamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _writeln(fp, s=""):
    fp.write(s.rstrip("\n") + "\n")


def _section(fp, title):
    _writeln(fp, f"\n== {title} ==")


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return p.returncode, out, err


def _collect_sistema(fp):
    _section(fp, "SISTEMA")
    _writeln(fp, f"OS: {platform.platform()}")
    _writeln(fp, f"Python: {sys.version.split()[0]}")
    _writeln(fp, f"Exe: {sys.executable}")
    _writeln(fp, f"Arch: {platform.machine()}  ({platform.processor()})")


def _collect_proyecto(fp, root: Path):
    _section(fp, "ARBOL DEL PROYECTO")
    try:
        # Árbol corto (2 niveles) para no generar archivos gigantes
        for base, dirs, files in os.walk(root):
            rel = Path(base).relative_to(root)
            if len(rel.parts) > 2:
                # No profundizar demasiado
                dirs[:] = []
                continue
            _writeln(fp, str(rel) if rel != Path('.') else '.')
            for f in sorted(files):
                _writeln(fp, f"  - {f}")
    except Exception as e:
        _writeln(fp, f"(falló el tree: {e})")


def _collect_archivos_interes(fp, root: Path):
    _section(fp, "SNIPPETS")
    targets = [
        ("configs/models.yaml", 200),
        ("scripts/setup_and_run.ps1", 160),
        ("backend_manager.py", 140),
        ("ch_cli.py", 160),
        ("requirements.txt", 400),
    ]
    for rel, n in targets:
        p = root / rel
        _writeln(fp, f"\n-- {rel} --")
        if p.exists():
            try:
                with p.open("r", encoding="utf-8", errors="ignore") as rf:
                    for i, line in enumerate(rf):
                        if i >= n:
                            break
                        fp.write(line)
            except Exception as e:
                _writeln(fp, f"(no se pudo leer: {e})")
        else:
            _writeln(fp, "(no existe)")


def _collect_python_env(fp):
    _section(fp, "PYTHON ENV")
    try:
        rc, out, err = _run([sys.executable, "-m", "pip", "freeze"])
        _writeln(fp, out.strip() or "(sin salida)")
        if err.strip():
            _writeln(fp, "\n[pip stderr]")
            _writeln(fp, err.strip())
    except Exception as e:
        _writeln(fp, f"(pip freeze falló: {e})")


def _collect_puertos(fp, ports=(8081, 8082, 8083)):
    _section(fp, "PUERTOS")
    info = []
    # 1) psutil si está disponible
    try:
        import psutil  # opcional
        conns = psutil.net_connections()
        for c in conns:
            if c.laddr and c.laddr.port in ports:
                info.append(f"{c.type} {c.laddr.ip}:{c.laddr.port} -> {c.raddr if c.raddr else ''} {c.status}")
    except Exception:
        # 2) netstat como fallback
        try:
            rc, out, _ = _run(["cmd", "/c", "netstat -ano"])
            for line in out.splitlines():
                for p in ports:
                    if f":{p} " in line:
                        info.append(line.strip())
        except Exception as e:
            _writeln(fp, f"(no se pudieron enumerar puertos: {e})")
    if info:
        for line in info:
            _writeln(fp, line)
    else:
        _writeln(fp, "(sin coincidencias)")


def _write_diag(task: str, cmd: list[str] | None, stdout: str, stderr: str, exc: Exception | None) -> Path:
    path = DEF_CACHE / f"diag-{_nowstamp()}.txt"
    root = Path(".").resolve()
    with path.open("w", encoding="utf-8") as fp:
        _writeln(fp, f"### Cloudhabil DIAGNOSTICO {_nowstamp()}")
        _writeln(fp, f"TASK: {task}")
        if cmd:
            _writeln(fp, "CMD : " + " ".join(cmd))
        _collect_sistema(fp)
        _collect_proyecto(fp, root)
        _collect_archivos_interes(fp, root)
        _collect_python_env(fp)
        _collect_puertos(fp)
        _section(fp, "STDOUT")
        _writeln(fp, stdout or "(vacío)")
        _section(fp, "STDERR")
        _writeln(fp, stderr or "(vacío)")
        if exc:
            _section(fp, "EXCEPCION")
            _writeln(fp, "".join(traceback.format_exception(exc)))
    return path


def _save_pending(task: str, diag_path: Path, err_summary: str):
    data = {"task": task, "diag": str(diag_path), "when": _nowstamp(), "summary": err_summary.strip()[:800]}
    PENDING.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _cleanup_on_success(task: str):
    if not PENDING.exists():
        return
    try:
        data = json.loads(PENDING.read_text(encoding="utf-8"))
        diag = Path(data.get("diag", ""))
        summary = textwrap.dedent(f"""
        Último error (resuelto): {data.get('when')}
        Task : {data.get('task')}
        Nota : {data.get('summary', '(sin resumen)')}
        """).strip()
        RESUMEN.write_text(summary + "\n", encoding="utf-8")
        if diag.exists():
            try:
                diag.unlink()
            except Exception:
                # Si no podemos borrar, al menos comprimimos
                zip_path = diag.with_suffix(".zip")
                shutil.make_archive(zip_path.with_suffix(""), "zip", diag.parent, diag.name)
                # y marcamos para borrar en arranque futuro
        PENDING.unlink(missing_ok=True)
    except Exception:
        # No bloquear la ejecución por limpieza
        pass


def run_with_diag(task: str, cmd: list[str]) -> int:
    """Ejecuta un comando; si falla, guarda diagnóstico completo y deja marca 'pending'."""
    rc, out, err = _run(cmd)
    if rc != 0:
        # resumen corto para el marcador
        head = (err or out or f"rc={rc}").strip().splitlines()[:5]
        diag_path = _write_diag(task, cmd, out, err, None)
        _save_pending(task, diag_path, "\n".join(head))
    else:
        _cleanup_on_success(task)
    return rc


def wrap_callable_with_diag(task: str, fn, *args, **kwargs) -> int:
    """Para envolver funciones Python directamente."""
    try:
        ret = fn(*args, **kwargs) or 0
    except Exception as e:
        diag_path = _write_diag(task, cmd=None, stdout="", stderr="", exc=e)
        _save_pending(task, diag_path, repr(e))
        raise
    else:
        _cleanup_on_success(task)
        return int(ret)


def _main():
    ap = argparse.ArgumentParser(description="AI diag helper (guarda logs en .cache/diag)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Ejecuta un comando y captura diagnóstico si falla")
    r.add_argument("--task", required=True)
    r.add_argument("command", nargs=argparse.REMAINDER,
                   help="Comando a ejecutar (usa -- para separar).")

    c = sub.add_parser("cleanup", help="Forzar limpieza si había errores pendientes")
    c.add_argument("--task", required=False, default="(manual)")

    args = ap.parse_args()

    if args.cmd == "run":
        # args.command incluye el separador '--', quitarlo si aparece
        cmd = args.command
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]
        if not cmd:
            print("Nada que ejecutar. Usa: ai_diag.py run --task X -- <cmd> ...", file=sys.stderr)
            return 2
        rc = run_with_diag(args.task, cmd)
        return rc
    elif args.cmd == "cleanup":
        _cleanup_on_success(args.task)
        print("Limpieza realizada (si había pendiente).")
        return 0


if __name__ == "__main__":
    sys.exit(_main())
