# Configuration

Model backends are defined in `configs/models.yaml`.
Each model entry supports the following fields:

- `kind` – backend type. Supported values are `ollama` and `openai`.
- `endpoint` – HTTP endpoint for the chat API.
- `model` – identifier of the model to use.

For the `openai` backend an API key must be supplied via the `OPENAI_API_KEY`
environment variable. The default endpoint for OpenAI is
`https://api.openai.com/v1/chat/completions`.

Example configuration:

```yaml
models:
  local_llm:
    kind: ollama
    endpoint: http://127.0.0.1:11434/api/chat
    model: llama3.1:latest
  gpt4o:
    kind: openai
    endpoint: https://api.openai.com/v1/chat/completions
    model: gpt-4o-mini
```
