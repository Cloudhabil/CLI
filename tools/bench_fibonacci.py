from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
from typing import List, Dict, Any
from budget_forcing import BudgetController

def run_cmd(cmd: str) -> int:
    print(f"[bench] exec: {cmd}", flush=True)
    completed = subprocess.run(cmd, shell=True)
    return completed.returncode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True,
                    help="Command template with {budget}. Example: python .\\infer_reasoning.py --max-think {budget} --min-think {budget} --force-continue Wait --evalset AIME24 --out runs\\aime_b{budget}.json")
    ap.add_argument("--budgets", nargs="*", type=int, default=None)
    ap.add_argument("--limit", type=int, default=100000)
    ap.add_argument("--out", default="runs/fib_summary.json")
    args = ap.parse_args()

    bc = BudgetController(limit=args.limit)
    budgets = args.budgets or bc.budgets()
    Path("runs").mkdir(parents=True, exist_ok=True)

    summary: List[Dict[str, Any]] = []
    for b in budgets:
        cmd = args.cmd.format(budget=b)
        rc = run_cmd(cmd)
        record: Dict[str, Any] = {"budget": b, "returncode": rc}
        guess = Path(f"runs/aime_b{b}.json")
        if guess.exists():
            try:
                data = json.loads(guess.read_text(encoding="utf-8"))
                for k in ["control", "scaling", "performance", "accuracy", "loss"]:
                    if k in data:
                        record[k] = data[k]
            except Exception as e:
                record["ingest_error"] = str(e)
        summary.append(record)

    Path(args.out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[bench] wrote {args.out}")

if __name__ == "__main__":
    main()
