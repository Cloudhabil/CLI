import json
import sys
from pathlib import Path
from agents import (
    agent_generate_ideas, agent_explain_concepts, agent_optimize_code,
    agent_resolve_problems, agent_best_practices, agent_write_docs,
    agent_code_review, agent_prototype
)

CONFIG_PATH = Path("config/instructions.json")

def load_config():
    if not CONFIG_PATH.exists():
        print(f"Config not found: {CONFIG_PATH}")
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

def prompt_yes_no(msg: str) -> bool:
    try:
        ans = input(f"{msg} (y/n): ").strip().lower()
        return ans == "y"
    except EOFError:
        return False

def run_interactive(instruction_set):
    idx = 0
    while True:
        task = instruction_set[idx]
        print(f"\n🟢 Next mission [{idx+1}/{len(instruction_set)}]: {task}")
        if not prompt_yes_no("Approve this mission?"):
            print("⏭️  Skipped.")
        else:
            dispatch(task)
            print("✅ Mission completed.")
        idx = (idx + 1) % len(instruction_set)

def dispatch(task: str):
    title = task.split(":")[0].strip().lower()

    if title.startswith("generate ideas"):
        print(agent_generate_ideas(context={}))
    elif title.startswith("explain concepts"):
        topic = input("Concept to explain (free text): ").strip() or "architecture layering"
        print(agent_explain_concepts(topic))
    elif title.startswith("optimize code"):
        print("Paste code below. End with a single line containing only 'EOF'.")
        code = read_block_until_eof()
        print(agent_optimize_code(code))
    elif title.startswith("resolve problems"):
        symptoms = input("Describe bug/logic symptoms: ").strip()
        print(agent_resolve_problems(symptoms))
    elif title.startswith("learn best practices"):
        scope = input("Area (e.g., backend, DevOps, data): ").strip() or "backend"
        print(agent_best_practices(scope))
    elif title.startswith("write documentation"):
        doc_title = input("Doc title: ").strip() or "cloudhabil_cli_notes"
        body = input("Doc body (short ok): ").strip() or "Auto-generated notes."
        path = agent_write_docs(doc_title, body)
        print(f"📝 Documentation saved to: {path}")
    elif title.startswith("simulate code review"):
        print("Paste code for review. End with 'EOF'.")
        code = read_block_until_eof()
        print(agent_code_review(code))
    elif title.startswith("rapidly prototype ideas"):
        desc = input("Prototype description (what should it do?): ").strip() or "health endpoint + TODO marker"
        print(agent_prototype(desc))
    else:
        print("⚠️ Unrecognized mission; no-op.")

def read_block_until_eof() -> str:
    lines = []
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        if line.strip() == "EOF":
            break
        lines.append(line)
    return "".join(lines)

def main():
    cfg = load_config()
    mode = cfg.get("mode", "interactive")
    instruction_set = cfg.get("instruction_set", [])
    if not instruction_set:
        print("No instructions found.")
        sys.exit(1)
    if mode != "interactive":
        print(f"Mode '{mode}' not supported in this script. Forcing interactive.")
    run_interactive(instruction_set)

if __name__ == "__main__":
    main()
