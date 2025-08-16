# Sesamawake

Prereqs: Python 3.11, Ollama with models `codegemma`, `llama3.1`, `qwen2.5-coder`, Stripe webhook secret, Google OAuth client id/secret.

First run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
./sesamawake
```

Admin TUI examples:

- `chat CEO :: Outline next 90 days`
- `check CEO :: Decision summary`
- `kb memo :: strategy || Focus DACH mid-market`

Weekly report:

```powershell
python ./kb_report.py
```

Gmail prospecting (dry-run):

```powershell
python ./prospect.py
```
