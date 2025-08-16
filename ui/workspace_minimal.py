from typing import Callable
from rich.console import Console
from ui_texts import load_texts


def main(
    route: Callable[[str, str, str], None],
    check_ceo: Callable[[str], str],
    lang: str = "en",
) -> None:
    """Minimal interactive workspace.

    Supports only basic actions: chatting with agents and checking the CEO
    decision policy. This is a lean alternative to the full admin TUI.
    """
    texts = load_texts(lang)
    console = Console()

    while True:
        try:
            line = console.input(texts.get("prompt", "admin> "))
        except (EOFError, KeyboardInterrupt):
            break
        if not line.strip():
            continue

        if line.startswith("chat "):
            # Format: chat agent::message
            _, rest = line.split(" ", 1)
            agent, msg = rest.split("::", 1)
            route("admin", agent.strip(), msg.strip())
        elif line.startswith("check "):
            # Format: check CEO::summary
            _, rest = line.split(" ", 1)
            agent, msg = rest.split("::", 1)
            if agent.strip().upper() == "CEO":
                verdict = check_ceo(msg.strip())
                console.print(f"{texts.get('policy', 'policy')}: {verdict}")
        else:
            console.print(texts.get("unknown_command", "unknown command"))
