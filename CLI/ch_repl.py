#!/usr/bin/env python3
import os, sys, re, time, uuid, argparse, subprocess
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from ui_texts import load_texts

# Reusamos la config y los callers de tu CLI
from ch_cli import CFG, call_router, call_http, SYS_ROUTER, SYS_QWEN, SYS_DEEPSEEK, slugify, ensure_task_dir

console = Console()
TEXTS = load_texts(os.environ.get("LANG", "en"))

BANNER = r"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘ âŒ–â›¨âŒ–  â–£â–£â–£  CHEVRON â–¸â–¸â–¸  â”ƒâš™ RIVETS âš™â”ƒ  â—‚â—‚â—‚ â–£â–£â–£  âŒ–â›¨âŒ–   â–²â–²  Tactical Frame  â–¼â–¼   âŒ–â›¨âŒ–  â–£â–£â–£  â”ƒâš™â”ƒ  âŒ–â›¨âŒ–  â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘ â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“ â•‘
â•‘ â–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–šâ–š â–‘â•‘
â•‘                                                                                                          â•‘
â•‘      â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•— â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•— â–ˆâ–ˆâ•—     â–ˆâ–ˆâ•—                                                       â•‘
â•‘      â•šâ•â•â–ˆâ–ˆâ–ˆâ•”â•â–ˆâ–ˆâ•”â•â•â•â–ˆâ–ˆâ•—â–ˆâ–ˆâ•”â•â•â•â–ˆâ–ˆâ•—â–ˆâ–ˆâ•”â•â•â–ˆâ–ˆâ•—â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•‘                                                       â•‘
â•‘        â–ˆâ–ˆâ–ˆâ•”â• â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•‘                                                       â•‘
â•‘       â–ˆâ–ˆâ–ˆâ•”â•  â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘   â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•”â•â•â–ˆâ–ˆâ•‘â–ˆâ–ˆâ•‘     â–ˆâ–ˆâ•‘                                                       â•‘
â•‘      â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â•šâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•”â•â•šâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•”â•â–ˆâ–ˆâ•‘  â–ˆâ–ˆâ•‘â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ•—                                                  â•‘
â•‘      â•šâ•â•â•â•â•â•â• â•šâ•â•â•â•â•â•  â•šâ•â•â•â•â•â• â•šâ•â•  â•šâ•â•â•šâ•â•â•â•â•â•â•â•šâ•â•â•â•â•â•â•                                                  â•‘
â•‘                                                                                      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â•‘
â•‘                                   O  R  C  A  I                                     â”‚  STENCIL CUTS   â”‚ â•‘
â•‘                              â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€                               â”‚  MIDâ€“SECTION    â”‚ â•‘
â•‘                                                                                      â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â•‘
â•‘ â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â––â–– â–—â•‘
â•‘ â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“â–“ â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•¦â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•¦â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘ â—¥â—£ Hazard â–°â–°â–°    â•‘  â— L â–·  â— R â–·  â— U â–·  â— D â–·  chevrons & rivets everywhere     â•‘   â–°â–°â–° Barricade â—¢â—¤ â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•©â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•©â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
"""

HELP = """\
Commands:
/help                   Muestra esta ayuda
/model [router|qwen|deepseek]
                        Cambia el backend activo (por defecto: router = CodeGemma in-process)
/file <ruta>            Carga el archivo y lo envÃ­a como mensaje (Ãºtil para contexto)
/task <slug>            Cambia/crea la tarea actual (se guardan outputs como en la CLI)
/exec                   Ejecuta el primer bloque ```python``` del Ãºltimo output de la tarea
/clear                  Limpia la consola
/exit                   Salir
"""

STYLE = Style.from_dict({
    "prompt": "bold",
    "meta": "italic ansibrightblack",
})

def system_for(key: str) -> str:
    if key == "generator_primary":
        return SYS_QWEN
    if key == "assistant_qc":
        return SYS_DEEPSEEK
    # router en modo chat (no clasificamos aquÃ­; para clasificar usa la CLI normal)
    return "Eres un asistente tÃ©cnico conciso. Responde claro y breve."

def send_message(model_key: str, text: str) -> str:
    if model_key == "router":
        return call_router(system_for("router"), text, CFG["router"].get("params", {}))
    return call_http(model_key, system_for(model_key), text)

def extract_first_code(md_text: str, lang: str = "python"):
    m = re.search(rf"```{lang}\s*([\s\S]*?)```", md_text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"```([\s\S]*?)```", md_text)
    return m.group(1).strip() if m else None

def run_exec_for_task(slug: str):
    tdir = Path(__file__).resolve().parent / "tasks" / slug
    outs = sorted((tdir / "outputs").glob("*.md"))
    if not outs:
        console.print(f"[yellow]{TEXTS.get('no_outputs', 'No hay salidas para ejecutar.')}[/yellow]")
        return
    last = outs[-1].read_text(encoding="utf-8")
    code = extract_first_code(last, "python")
    if not code:
        console.print(f"[yellow]{TEXTS.get('no_code_block', 'No encontr\u00e9 bloque ```python``` en el \u00faltimo output.')}[/yellow]")
        return
    scratch = tdir / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    script = scratch / "main.py"
    script.write_text(code, encoding="utf-8")
    console.print(f"[bold]{TEXTS.get('exec_running', '\u25B6 Ejecutando')}[/bold] {script}")
    proc = subprocess.run([sys.executable, str(script)], cwd=scratch, capture_output=True, text=True, timeout=45)
    console.rule("STDOUT")
    console.print(proc.stdout or "")
    console.rule("STDERR")
    console.print(proc.stderr or "")

def main():
    parser = argparse.ArgumentParser(description="REPL tipo Gemini usando CodeGemma/Qwen/DeepSeek")
    parser.add_argument("--model", choices=["router","qwen","deepseek"], default="router")
    parser.add_argument("--task", default=f"repl-{time.strftime('%Y%m%d-%H%M%S')}")
    args = parser.parse_args()

    model_key = {"router":"router","qwen":"generator_primary","deepseek":"assistant_qc"}[args.model]
    slug = slugify(args.task)
    tdir = ensure_task_dir(slug)

    console.print(Panel.fit(Text(BANNER, justify="left"), border_style="magenta"))
    console.print(f"[dim]Using: task [bold]{slug}[/bold]   env: no sandbox   model: [bold]{CFG[model_key]['name']}[/bold][/dim]")
    console.print(f"[dim]{TEXTS.get('tip', 'Tip: escribe texto o usa comandos como /file, /model, /exec, /help')}[/dim]\n")

    history = InMemoryHistory()
    completer = WordCompleter(["/help","/model","/file","/task","/exec","/agent","/clear","/exit"], ignore_case=True)
    session = PromptSession(history=history, completer=completer)

    while True:
        try:
            user = session.prompt("> ", style=STYLE)
        except (KeyboardInterrupt, EOFError):
            console.print("\n" + TEXTS.get('exiting', 'Saliendoâ€¦'))
            break

        if not user.strip():
            continue

        # Comandos
        if user.startswith("/"):
            parts = user.strip().split()
            cmd = parts[0].lower()

            if cmd == "/exit":
                break
            if cmd == "/agent":
                import shlex, subprocess
                agent_parts = shlex.split(user)
                goal = " ".join(agent_parts[1:]) or "Show directory"
                console.print(f"[agent] goal = {goal}")
                rc = subprocess.call([sys.executable, "agent.py", "--goal", goal])
                console.print(f"[agent] exit code: {rc}")
                continue
            if cmd == "/help":
                console.print(HELP)
                continue
            if cmd == "/clear":
                console.clear()
                console.print(Panel.fit(Text(BANNER, justify="left"), border_style="magenta"))
                continue
            if cmd == "/model":
                if len(parts) < 2 or parts[1] not in ["router","qwen","deepseek"]:
                    console.print("[yellow]Uso: /model router|qwen|deepseek[/yellow]")
                    continue
                model_key = {"router":"router","qwen":"generator_primary","deepseek":"assistant_qc"}[parts[1]]
                console.print(f"âœ” Modelo activo: [bold]{CFG[model_key]['name']}[/bold]")
                continue
            if cmd == "/task":
                if len(parts) < 2:
                    console.print("[yellow]Uso: /task <slug>[/yellow]")
                    continue
                slug = slugify(parts[1])
                tdir = ensure_task_dir(slug)
                console.print(f"âœ” Tarea actual: [bold]{slug}[/bold]")
                continue
            if cmd == "/file":
                if len(parts) < 2:
                    console.print("[yellow]Uso: /file <ruta>[/yellow]")
                    continue
                path = Path(" ".join(parts[1:])).expanduser()
                if not path.exists():
                    console.print(f"[red]No existe:[/red] {path}")
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                payload = f"# Archivo: {path}\n\n```text\n{text}\n```"
                reply = send_message(model_key, payload)
                ts = time.strftime("%Y%m%d-%H%M%S")
                out = tdir/"outputs"/f"{ts}-{CFG[model_key]['name']}.md"
                out.write_text(reply, encoding="utf-8")
                console.print(Panel(reply, title=f"Response â€” {CFG[model_key]['name']}", border_style="cyan"))
                continue
            if cmd == "/exec":
                run_exec_for_task(slug)
                continue

            console.print(f"[yellow]{TEXTS.get('unrecognized_command', 'Comando no reconocido. /help para ver opciones.')}[/yellow]")
            continue

        # Mensaje normal -> envÃ­a al modelo activo
        reply = send_message(model_key, user)
        ts = time.strftime("%Y%m%d-%H%M%S")
        out = tdir/"outputs"/f"{ts}-{CFG[model_key]['name']}.md"
        out.write_text(reply, encoding="utf-8")
        console.print(Panel(reply, title=f"Response â€” {CFG[model_key]['name']}", border_style="cyan"))

if __name__ == "__main__":
    main()



