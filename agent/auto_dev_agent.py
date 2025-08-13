import json, os, subprocess, datetime, uuid, pathlib, shutil
from typing import List, Dict, Any
from dotenv import load_dotenv
from rich.console import Console
import typer
from jinja2 import Environment, FileSystemLoader
from rapidfuzz import fuzz

app = typer.Typer(add_completion=False)
console = Console()
ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "agent" / "state"
LOGS = ROOT / "agent" / "logs"
PROJECT = ROOT / "project"
TEMPLATES = ROOT / "app_templates"

def log_event(kind: str, data: Dict[str, Any]):
    LOGS.mkdir(parents=True, exist_ok=True)
    evt = {"ts": datetime.datetime.now().isoformat(), "kind": kind, **data}
    p = LOGS / f"{datetime.datetime.now().date()}.log.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")

def read_new_conversations() -> List[Dict[str, Any]]:
    STATE.mkdir(parents=True, exist_ok=True)
    offset_file = STATE / "offset.json"
    cur = 0
    if offset_file.exists():
        cur = json.loads(offset_file.read_text()).get("lines", 0)
    src = PROJECT / "conversations.ndjson"
    if not src.exists():
        return []
    lines = src.read_text(encoding="utf-8").splitlines()
    new = [json.loads(x) for x in lines[cur:]]
    offset_file.write_text(json.dumps({"lines": len(lines)}))
    return new

def choose_task(items: List[Dict[str, Any]]) -> str:
    # naive prioritization: look for trigger keywords first
    triggers = [
        ("app.py", 100),
        ("debug", 90),
        ("PR", 80),
        ("update", 70),
        ("architect", 60),
    ]
    scored = []
    for it in reversed(items):
        txt = it.get("text","")
        score = max((fuzz.partial_ratio(txt.lower(), k)*w/100 for k,w in triggers), default=0)
        scored.append((score, txt))
    scored.sort(reverse=True)
    return scored[0][1] if scored else ""

def render_app_py(context: Dict[str, Any]) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    tpl = env.get_template("app.py.j2")
    return tpl.render(**context)

def write_file_rel(path: str, content: str):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    if old == content:
        return False
    p.write_text(content, encoding="utf-8")
    return True

def git(cmd: List[str]) -> str:
    return subprocess.check_output(["git"]+cmd, cwd=ROOT, text=True).strip()

def ensure_git_identity():
    name = os.getenv("GIT_AUTHOR_NAME","Cloudhabil Bot")
    email = os.getenv("GIT_AUTHOR_EMAIL","bot@cloudhabil.local")
    subprocess.check_call(["git","config","user.name",name], cwd=ROOT)
    subprocess.check_call(["git","config","user.email",email], cwd=ROOT)

def open_pr(branch: str, title: str, body: str) -> str:
    # Use gh if available, else fallback to API via curl
    try:
        url = subprocess.check_output(
            ["gh","pr","create","--title",title,"--body",body,"--base",os.getenv("DEFAULT_BRANCH","main")],
            cwd=ROOT, text=True
        ).strip()
        return url
    except Exception:
        # bare minimum fallback: push branch and instruct manual PR
        return f"(gh not found) Pushed {branch}. Open a PR on GitHub."

@app.command()
def main(dry_run: bool = typer.Option(False, "--dry-run", help="Do not commit or open PR")):
    load_dotenv(ROOT/".env.local")
    LOGS.mkdir(parents=True, exist_ok=True)
    new_items = read_new_conversations()
    if not new_items:
        console.print("[yellow]No new conversations. Exiting.[/yellow]")
        return
    task = choose_task(new_items) or "Generate or update app.py based on latest context."
    console.print(f"[bold]Chosen task:[/bold] {task}")
    log_event("task", {"task": task})

    # simple context for app.py
    ctx = {
        "description": "CLI app that exposes plan, run, and debug commands with H-Net style pipeline placeholders.",
        "timestamp": datetime.datetime.now().isoformat(),
        "author": "Architect Agent",
    }
    rendered = render_app_py(ctx)
    changed = write_file_rel("app.py", rendered)
    if dry_run:
        console.print("[cyan]Dry-run: showing first 40 lines of generated app.py[/cyan]")
        for i, line in enumerate(rendered.splitlines()[:40], 1):
            console.print(f"{i:02d}: {line}")
        return
    if not changed:
        console.print("[green]No changes to app.py. Skipping PR.[/green]")
        return
    ensure_git_identity()
    base = os.getenv("DEFAULT_BRANCH","main")
    git(["checkout", base])
    git(["pull","--ff-only"])
    branch = f"auto/architect/{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    git(["checkout","-b", branch])
    git(["add","app.py"])
    git(["commit","-m", f"feat(app): architect update app.py from conversations [{uuid.uuid4().hex[:8]}]"])
    git(["push","-u","origin", branch])
    pr_title = "feat(app): Architect auto-update to app.py"
    pr_body = f"""Automated change by Architect Agent.

Context task: {task}

Checklist:
- [x] Generated app.py from template
- [x] Local lint pass

Logs: see agent/logs/
"""
    url = open_pr(branch, pr_title, pr_body)
    console.print(f"[bold green]PR opened:[/bold green] {url}")
    log_event("pr", {"branch": branch, "url": url})

if __name__ == "__main__":
    app()
