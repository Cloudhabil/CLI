import argparse, json, os, re, sys, time, queue, threading, subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

# Minimal allowlist policy. Expand as needed.
ALLOW_PREFIXES = [
    "pip ", "python ", "py ", "poetry ",
    "docker ", "docker-compose ", "kubectl ", "helm ",
    "pwsh ", "powershell ", "git ", "curl ", "Invoke-WebRequest ",
    "dir", "ls", "echo ", "type ", "cat ", "where ", "whoami", "set ", "Get-ChildItem"
]

DENY_PATTERNS = [
    r"rm -rf /", r"Format-Volume", r"Remove-Item\s+-Recurse\s+-Force\s+C:\\",
    r"shutdown", r"reboot", r"Disable", r"Initialize-Disk"
]

LOG_DIR = os.path.join(os.getcwd(), ".agent_logs")
os.makedirs(LOG_DIR, exist_ok=True)
TRANSCRIPT = os.path.join(LOG_DIR, f"transcript_{int(time.time())}.log")
JSONL = os.path.join(LOG_DIR, f"events_{int(time.time())}.jsonl")

def log_event(event: Dict):
    event["ts"] = time.time()
    with open(JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def append_transcript(line: str):
    with open(TRANSCRIPT, "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")

def policy_allows(cmd: str) -> Tuple[bool, str]:
    for pat in DENY_PATTERNS:
        if re.search(pat, cmd, flags=re.IGNORECASE):
            return False, f"Command blocked by deny pattern: {pat}"
    if any(cmd.strip().lower().startswith(pfx.strip().lower()) for pfx in ALLOW_PREFIXES):
        return True, "allowed by prefix"
    return False, "not in allowlist"

class PowerShellSession:
    def __init__(self):
        # Start a persistent PowerShell
        # -NoLogo/-NoProfile for speed and determinism
        self.proc = subprocess.Popen(
            ["powershell", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "-"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )
        # Unique prompt markers to split command outputs
        self.marker = f"__AGENT_MARKER__{int(time.time())}"

    def run(self, cmd: str, timeout: int = 600) -> Tuple[int, str]:
        if self.proc.poll() is not None:
            raise RuntimeError("PowerShell process is not running")
        # Send the command followed by exit code and marker
        script = f"{cmd}\n$__e=$LASTEXITCODE; echo \"{self.marker} $__e\""
        self.proc.stdin.write(script + "\n")
        self.proc.stdin.flush()
        # Read until marker appears
        lines = []
        start = time.time()
        while True:
            line = self.proc.stdout.readline()
            if not line and self.proc.poll() is not None:
                break
            if line:
                lines.append(line)
                if line.strip().startswith(self.marker):
                    break
            if time.time() - start > timeout:
                raise TimeoutError(f"Command timed out after {timeout}s: {cmd}")
        # Parse exit code marker
        exit_line = lines[-1].strip()
        try:
            _, code = exit_line.split(" ", 1)
            rc = int(code)
            output = "".join(lines[:-1])
            return rc, output
        except Exception:
            return 1, "".join(lines)

    def close(self):
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.stdin.write("exit\n")
                self.proc.stdin.flush()
                self.proc.terminate()
        except Exception:
            pass

def default_planner(goal: str) -> List[str]:
    # Simple rule-based planner for local dev; replace with LLM later.
    g = goal.lower()
    steps: List[str] = []
    if "install" in g or "deps" in g or "dependencies" in g:
        steps.append("pip install -r requirements.txt")
    if "docker compose" in g or "docker-compose" in g or "start" in g:
        steps.append("docker compose up -d")
    if "health" in g:
        # Windows curl alias is fine; use both variants
        steps.append("curl http://localhost:8000/health")
    if not steps:
        # Fallback: at least list directory
        steps = ["pwd", "dir"]
    return steps

def run_agent(goal: str, dry_run: bool = False) -> int:
    append_transcript(f"# Goal: {goal}")
    log_event({"type": "goal", "goal": goal})
    steps = default_planner(goal)
    append_transcript(f"# Plan: {steps}")
    log_event({"type": "plan", "steps": steps})

    if dry_run:
        print("[DRY RUN] Planned steps:")
        for s in steps:
            print(" -", s)
        return 0

    ps = PowerShellSession()
    try:
        for idx, step in enumerate(steps, start=1):
            ok, reason = policy_allows(step)
            append_transcript(f"\n> Step {idx}: {step}  [{reason}]")
            log_event({"type": "policy_check", "cmd": step, "allowed": ok, "reason": reason})
            if not ok:
                print(f"[BLOCKED] {step} -> {reason}")
                append_transcript(f"[BLOCKED] {step} -> {reason}")
                return 2
            print(f"[EXEC] {step}")
            rc, out = ps.run(step)
            append_transcript(out)
            log_event({"type": "exec", "cmd": step, "rc": rc})
            if rc != 0:
                print(f"[ERROR] rc={rc} on: {step}")
                # naive recovery example: pip retry with --break-system-packages
                if step.startswith("pip "):
                    retry = step + " --break-system-packages"
                    print(f"[RETRY] {retry}")
                    append_transcript(f"[RETRY] {retry}")
                    rc2, out2 = ps.run(retry)
                    append_transcript(out2)
                    log_event({"type": "exec_retry", "cmd": retry, "rc": rc2})
                    if rc2 == 0:
                        continue
                return rc
        print("[DONE] Goal reached.")
        append_transcript("\n[DONE] Goal reached.")
        return 0
    finally:
        ps.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--goal", required=True, help="Natural language objective to execute")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    code = run_agent(args.goal, dry_run=args.dry_run)
    sys.exit(code)
