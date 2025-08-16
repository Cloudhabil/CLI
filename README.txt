# 3Agenteers CLI

## Overview
The CLI orchestrates a local network of agents connected through a message bus and shared knowledge base. It ships with an admin TUI and integration hooks for external services.

```
+---------------+       +-------------+
| Orchestrator  |<---->| Message Bus |
| (admin TUI)   |       +-------------+
+-------+-------+               |
        |                       v
        |             +------------------+
        +------------>|   Agents         |
                      +------------------+
                           |
                           v
                      +------------------+
                      | Knowledge Base  |
                      +------------------+
```

## Prerequisites
- Python 3.11
- Local Ollama models (e.g., `codegemma`, `llama3.1`, `qwen2.5-coder`)
- Environment variables configured (see table below)
- Optional: OpenVINO NPU support for embedding acceleration

## Installation & Setup
```bash
git clone <repo-url>
cd CLI
pip install -r requirements.txt
cp .env.example .env  # edit values
```

## Quick Start
Launch the orchestrator:
```bash
python orchestrator.py
```
On Windows PowerShell:
```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\sesamawake
```

Admin TUI commands:
- `chat CEO :: Outline next 90 days`
- `check CEO :: spend proposal`
- `kb last :: 5`
- `kb search :: invoice`

## Integrations
- Gmail and Google Drive APIs for email and storage
- Stripe webhook server
- Social hooks and automated prospecting (`prospect.py`)

## Security
- PowerShell allow/deny lists for command execution
- CEO policy engine governs agent permissions
- Bearer token auth for bus and agent servers

## Development & Testing
Run linting and tests before committing:
```bash
flake8
pytest
```
The CI workflow repeats these checks on each pull request.

## Roadmap
- H-Net dynamic chunking for hierarchical memory management
- OpenVINO-based embedding acceleration on supported NPUs

## Environment Variables
| Variable | Description | Default |
|---|---|---|
| `BUS_URL` | Base URL for the message bus | `http://127.0.0.1:7088` |
| `BUS_TOKEN` | Bearer token for message bus auth | *(none)* |
| `MODEL_KIND` | LLM backend (`ollama`, etc.) | `ollama` |
| `GOOGLE_CLIENT_ID` | OAuth client ID | *(none)* |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret | *(none)* |
| `STRIPE_WEBHOOK_SECRET` | Stripe signature secret | *(none)* |
| `PROSPECT_SENDER_NAME` | Outreach sender name | `Cloudhabil` |
| `PROSPECT_SENDER_EMAIL` | Outreach sender email | `obe@cloudhabil` |
| `PROSPECT_DRY_RUN` | Do not send real emails when `true` | `true` |
| `PROSPECT_RATE_LIMIT_PER_MIN` | Prospecting throttle | `12` |
| `GDRIVE_PARENT_FOLDER_ID` | Google Drive folder for uploads | *(none)* |

## Sample Workflows
Weekly knowledge report:
```bash
python kb_report.py
```

Gmail prospecting (dry run by default):
```bash
python prospect.py
```

Message bus publish/get:
```bash
curl -X POST "$BUS_URL/publish" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BUS_TOKEN" \
  -d '{"topic": "demo", "data": {"text": "hello"}}'

curl "$BUS_URL/get?topic=demo" \
  -H "Authorization: Bearer $BUS_TOKEN"
```

## Contributing
- Follow [PEP 8](https://peps.python.org/pep-0008/) and keep commits concise
- Use descriptive commit messages (e.g., `fix:`, `feat:`, `docs:`)
- Run `flake8` and `pytest` before submitting pull requests
