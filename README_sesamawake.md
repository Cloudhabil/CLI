# Sesamawake

## Prereqs
- Python 3.11
- Ollama with codegemma, llama3.1, qwen2.5-coder models
- Stripe webhook secret
- Google OAuth client id/secret

## First run
```
Set-ExecutionPolicy -Scope Process Bypass -Force
.\sesamawake
```

## Admin TUI examples
- `chat CEO :: Outline next 90 days`
- `check CEO :: spend proposal`
- `kb last :: 5`

## Weekly report
```
python .\kb_report.py
```

## Gmail prospecting (dry run)
```
python .\prospect.py
```
