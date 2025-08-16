# Security Guide

## Authentication
- **Message bus**: protect `/publish` and `/get` with a bearer token set in the `BUS_TOKEN` env var.
  - Example: `curl "$BUS_URL/health" -H "Authorization: Bearer $BUS_TOKEN"`
- **Agent server**: require `AGENT_SHARED_SECRET` for all requests.
  - Example: `curl http://127.0.0.1:8000/health -H "Authorization: Bearer $AGENT_SHARED_SECRET"`
- Store secrets in environment variables and rotate them regularly.

## Authorization
- The CEO policy engine (`admin_policy.py`) enforces high-level rules over agent actions.
- PowerShell allow/deny lists restrict which commands can be executed by scripts.

## Hardening
- Run services behind TLS and limit network exposure.
- Use long, random tokens and change them periodically.
- Log and monitor `auth_failure` events from the knowledge base.
- Keep dependencies patched and apply the principle of least privilege for file and process permissions.
