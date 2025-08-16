#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
import requests
import yaml

ROOT = Path(__file__).resolve().parent
CFG = yaml.safe_load((ROOT / "configs" / "models.yaml").read_text(encoding="utf-8"))


def load_prompt(path):
    return (ROOT / "prompts" / path).read_text(encoding="utf-8")


SYS_ROUTER = load_prompt("system_router.md")
SYS_QWEN = load_prompt("system_qwen.md")
SYS_DEEPSEEK = load_prompt("system_deepseek.md")

# --- llama_cpp availability (in-process router) --------------------------------
try:
    from llama_cpp import Llama
    _HAVE_LLAMA_RAW = True
except Exception:
    Llama = None
    _HAVE_LLAMA_RAW = False


def _truthy_env(name, default=False):
    v = os.getenv(name, "")
    if not v:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")

# Force HTTP router if:
# - CH_FORCE_ROUTER_HTTP is truthy, OR
# - ROUTER_BASE_URL is provided in the environment, OR
# - CFG["router"]["model_path"] is missing/nonexistent.


def _should_use_http_router():
    if _truthy_env("CH_FORCE_ROUTER_HTTP", False):
        return True
    if os.getenv("ROUTER_BASE_URL"):
        return True
    r = CFG.get("router", {})
    mp = r.get("model_path")
    if not mp or not Path(mp).exists():
        return True
    return False


HAVE_LLAMA = _HAVE_LLAMA_RAW and not _should_use_http_router()
_ROUTER_LLM = None

# --- Config with environment overrides ----------------------------------------


def _cfg_with_env(key: str) -> dict:
    """
    Returns model config merged with environment overrides.
    Supported envs:
      Router:   ROUTER_BASE_URL,   ROUTER_MODEL,   ROUTER_API_KEY
      Qwen:     QWEN_BASE_URL,     QWEN_MODEL,     QWEN_API_KEY
      DeepSeek: DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, DEEPSEEK_API_KEY
    Back-compat API keys:
      CH_CLI_API_KEY_QWEN, CH_CLI_API_KEY_DEEPSEEK
    """
    c = dict(CFG.get(key, {}))  # shallow copy

    env_prefix = None
    if key == "router":
        env_prefix = "ROUTER"
    elif key == "generator_primary":   # qwen
        env_prefix = "QWEN"
    elif key == "assistant_qc":        # deepseek
        env_prefix = "DEEPSEEK"

    def _ovr(name_env, name_cfg):
        v = os.getenv(name_env)
        if v:
            c[name_cfg] = v

    if env_prefix:
        _ovr(f"{env_prefix}_BASE_URL", "base_url")
        _ovr(f"{env_prefix}_MODEL",    "model_id")
        _ovr(f"{env_prefix}_API_KEY",  "api_key")

    # Back-compat API key envs
    if key == "generator_primary" and not c.get("api_key"):
        c["api_key"] = os.getenv("CH_CLI_API_KEY_QWEN", c.get("api_key", ""))
    if key == "assistant_qc" and not c.get("api_key"):
        c["api_key"] = os.getenv("CH_CLI_API_KEY_DEEPSEEK", c.get("api_key", ""))

    # Ensure params dict exists
    c["params"] = dict(c.get("params", {}))
    return c

# --- Router (in-process via llama_cpp) -----------------------------------------


def _get_router():
    global _ROUTER_LLM
    if _ROUTER_LLM is None:
        r = _cfg_with_env("router")
        model_path = r.get("model_path")
        if not model_path or not Path(model_path).exists():
            raise RuntimeError(f"Router model not found at: {model_path}")
        _ROUTER_LLM = Llama(
            model_path=model_path,
            n_ctx=r.get("n_ctx", 8192),
            n_threads=r.get("threads", None),
            logits_all=False,
            embedding=False
        )
    return _ROUTER_LLM


def _make_url(base_url: str) -> str:
    """
    Normalize to OpenAI-compatible /v1/chat/completions.
    If base_url already ends with /v{n}, we only append /chat/completions.
    """
    b = (base_url or "").rstrip("/")
    if re.search(r"/v\d+/?$", b):
        return f"{b}/chat/completions"
    return f"{b}/v1/chat/completions"

# --- HTTP calls ----------------------------------------------------------------


def _auth_headers(model_key: str) -> dict:
    cfg = _cfg_with_env(model_key)
    api_key = cfg.get("api_key") or ""
    if not api_key:
        # Final fallback: legacy mapping by model_key name
        legacy_env = {
            "generator_primary": "CH_CLI_API_KEY_QWEN",
            "assistant_qc":     "CH_CLI_API_KEY_DEEPSEEK",
            "router":           "ROUTER_API_KEY",
        }.get(model_key, "")
        api_key = os.getenv(legacy_env, "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def call_http(model_key: str, system_prompt: str, user_prompt: str) -> str:
    cfg = _cfg_with_env(model_key)

    # Only spawn if the YAML explicitly asks for it
    try:
        from backend_manager import ensure_server
    except Exception:
        ensure_server = None

    if cfg.get("spawn", False) and ensure_server:
        ensure_server(model_key, cfg, wait=60)

    url = _make_url(cfg["base_url"])
    payload = {
        "model": cfg["model_id"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": cfg["params"].get("temperature", 0.2),
        "top_p":       cfg["params"].get("top_p", 0.9),
        "max_tokens":  cfg["params"].get("max_tokens", 1024),
        "stream": False
    }
    r = requests.post(url, json=payload, headers=_auth_headers(model_key), timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

# Router caller that prefers in-process llama if available, else HTTP


def call_router(system_prompt: str, user_prompt: str, params: dict) -> str:
    if HAVE_LLAMA:
        llm = _get_router()
        out = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=params.get("temperature", 0.2),
            top_p=params.get("top_p", 0.9),
            max_tokens=params.get("max_tokens", 512),
        )
        return out["choices"][0]["message"]["content"]
    # HTTP fallback (Ollama/OpenAI-compatible)
    return call_http("router", system_prompt, user_prompt)

# --- Task utils ----------------------------------------------------------------


def ensure_task_dir(slug):
    tdir = ROOT / "tasks" / slug
    (tdir / "inputs").mkdir(parents=True, exist_ok=True)
    (tdir / "outputs").mkdir(parents=True, exist_ok=True)
    return tdir


def slugify(s):
    s = re.sub(r"[^\w\-]+", "-", s.lower()).strip("-")
    return s or f"tarea-{uuid.uuid4().hex[:6]}"


def build_user_prompt(context, task, constraints, format_hint=True):
    parts = []
    if context:
        parts.append(f"# Contexto\n{context}")
    if task:
        parts.append(f"# Tarea\n{task}")
    if constraints:
        parts.append(f"# Restricciones\n{constraints}")
    if format_hint:
        parts.append("# Formato de salida\nDiff unificado y verificación breve.")
    return "\n\n".join(parts)

# --- Routing -------------------------------------------------------------------


def route(task_text):
    router_cfg = _cfg_with_env("router")
    try:
        plan_json = call_router(SYS_ROUTER, task_text, router_cfg.get("params", {}))
        meta = json.loads(plan_json)
    except Exception:
        lower = task_text.lower()
        if any(k in lower for k in ["refactor", "migr", "test", "integr"]):
            return "generator_primary", {"tipo": "heuristica", "tam": "M", "criticidad": "media"}
        if any(k in lower for k in ["coment", "doc", "snippet", "fix menor", "peque"]):
            return "assistant_qc", {"tipo": "heuristica", "tam": "S", "criticidad": "baja"}
        return "generator_primary", {"tipo": "desconocido", "tam": "M", "criticidad": "media"}
    tipo = meta.get("tipo", "desconocido")
    if tipo in ["refactor", "integracion", "tests", "migracion"]:
        return "generator_primary", meta
    if tipo in ["snippet", "comentado", "fix_menor", "doc"]:
        return "assistant_qc", meta
    return "generator_primary", meta

# --- Commands ------------------------------------------------------------------


def cmd_new(args):
    slug = slugify(args.name)
    tdir = ensure_task_dir(slug)
    (tdir/"inputs"/"context.md").write_text(args.context or "", encoding="utf-8")
    (tdir/"inputs"/"tarea.md").write_text(args.task or "", encoding="utf-8")
    (tdir/"inputs"/"restricciones.md").write_text(args.constraints or "", encoding="utf-8")
    print(f"✅ Tarea creada: tasks/{slug}")


def _run_to_model(key, user_prompt, tdir, meta, system):
    model_cfg = _cfg_with_env(key)
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_path = tdir/"outputs"/f"{ts}-{model_cfg.get('name', key)}.md"
    print(f"➡️  Modelo: {model_cfg.get('name', key)} | Motivo: {meta.get('tipo', 'n/a')} | Tam: {meta.get('tam', '?')}")

    content = call_http(key, system, user_prompt)
    out_path.write_text(content, encoding="utf-8")
    print(f"💾 Guardado: {out_path}")

    m = re.search(r"```diff([\s\S]*?)```", content)
    if m:
        patch = m.group(1).strip()
        patch_path = tdir/"outputs"/f"{ts}.patch"
        patch_path.write_text(patch, encoding="utf-8")
        print(f"🧩 Diff extraído: {patch_path}")


def cmd_run(args):
    slug = slugify(args.name)
    tdir = ensure_task_dir(slug)
    context = (tdir/"inputs"/"context.md").read_text(encoding="utf-8") if (tdir/"inputs"/"context.md").exists() else ""
    task = (tdir/"inputs"/"tarea.md").read_text(encoding="utf-8") if (tdir /
                                                                      "inputs"/"tarea.md").exists() else args.task or ""
    constraints = (tdir/"inputs"/"restricciones.md").read_text(encoding="utf-8") if (tdir /
                                                                                     "inputs"/"restricciones.md").exists() else args.constraints or ""
    user_prompt = build_user_prompt(context, task, constraints)

    if args.model in ["qwen", "deepseek"]:
        key = {"qwen": "generator_primary", "deepseek": "assistant_qc"}[args.model]
        meta = {"tipo": "forzado", "tam": "S", "criticidad": "media"}
    else:
        key, meta = route(task)

    system = SYS_QWEN if key == "generator_primary" else SYS_DEEPSEEK
    _run_to_model(key, user_prompt, tdir, meta, system)


def cmd_qa(args):
    tdir = ROOT/"tasks"/args.slug
    outs = sorted((tdir/"outputs").glob("*.md"))
    if not outs:
        print("No hay salidas para revisar.")
        return
    last = outs[-1].read_text(encoding="utf-8")
    review_prompt = f"# Salida previa\n\n{last}\n\n# Instruccion\nRevisa de forma concisa y sugiere cambios mínimos."
    _run_to_model("assistant_qc", review_prompt, tdir, {"tipo": "qa", "tam": "S"}, SYS_DEEPSEEK)


def cmd_apply(args):
    tdir = ROOT/"tasks"/args.slug
    patches = sorted((tdir/"outputs").glob("*.patch"))
    if not patches:
        print("No hay parche para aplicar.")
        return
    last_patch = patches[-1]
    print("Sugerencia para aplicar en tu repo (desde la raíz del proyecto destino):")
    print(f"git apply \"{last_patch}\"")


def cmd_doctor(args):
    print("🔍 ch-cli doctor: comprobando router y subservers...")
    # Router
    if HAVE_LLAMA:
        try:
            _get_router()
            print(" - router (llama_cpp in-process): OK")
        except Exception as e:
            print(f" - router (llama_cpp in-process): FAIL ({e})")
    else:
        try:
            from backend_manager import _is_alive
        except Exception:
            _is_alive = None
        r_cfg = _cfg_with_env("router")
        if _is_alive:
            ok = _is_alive(r_cfg.get("base_url", ""))
            print(f" - router (HTTP): {'OK' if ok else 'DOWN'} @ {r_cfg.get('base_url', '')}")
        else:
            print(f" - router (HTTP): base_url={r_cfg.get('base_url', '')} (no _is_alive helper)")

    # Subservers
    try:
        from backend_manager import _is_alive
    except Exception:
        _is_alive = None
    for key in ["generator_primary", "assistant_qc"]:
        cfg = _cfg_with_env(key)
        if _is_alive:
            ok = _is_alive(cfg.get("base_url", ""))
            print(f" - {cfg.get('name', key)}: {'OK' if ok else 'DOWN'} @ {cfg.get('base_url', '')}")
        else:
            print(f" - {cfg.get('name', key)}: base_url={cfg.get('base_url', '')} (no _is_alive helper)")


def main():
    p = argparse.ArgumentParser(prog="ch-cli", description="Cloudhabil Dev CLI")
    sub = p.add_subparsers()

    p_new = sub.add_parser("new", help="Crea una tarea")
    p_new.add_argument("--name", required=True)
    p_new.add_argument("--context", default="")
    p_new.add_argument("--task", default="")
    p_new.add_argument("--constraints", default="")
    p_new.set_defaults(func=cmd_new)

    p_run = sub.add_parser("run", help="Ejecuta routing y generación")
    p_run.add_argument("--name", required=True, help="Slug de tarea (se crea si no existe)")
    p_run.add_argument("--task", default="")
    p_run.add_argument("--constraints", default="")
    p_run.add_argument("--model", choices=["auto", "qwen", "deepseek"], default="auto")
    p_run.set_defaults(func=cmd_run)

    p_qa = sub.add_parser("qa", help="Revisión con DeepSeek")
    p_qa.add_argument("--slug", required=True)
    p_qa.set_defaults(func=cmd_qa)

    p_apply = sub.add_parser("apply", help="Imprime comando git apply para el último patch")
    p_apply.add_argument("--slug", required=True)
    p_apply.set_defaults(func=cmd_apply)

    p_doctor = sub.add_parser("doctor", help="Comprueba router y subservers")
    p_doctor.set_defaults(func=cmd_doctor)

    args = p.parse_args()
    if not hasattr(args, "func"):
        p.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
