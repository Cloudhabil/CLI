#!/usr/bin/env python3
import argparse, json, os, re, sys, time, uuid
from pathlib import Path
import requests, yaml

ROOT = Path(__file__).resolve().parent
CFG = yaml.safe_load((ROOT / "configs" / "models.yaml").read_text(encoding="utf-8"))

def load_prompt(path):
    return (ROOT / "prompts" / path).read_text(encoding="utf-8")

SYS_ROUTER   = load_prompt("system_router.md")
SYS_QWEN     = load_prompt("system_qwen.md")
SYS_DEEPSEEK = load_prompt("system_deepseek.md")

def call_chat(base_url, model_id, system_prompt, user_prompt, params):
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": params.get("temperature", 0.2),
        "top_p": params.get("top_p", 0.9),
        "max_tokens": params.get("max_tokens", 1024),
        "stream": False
    }
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

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
    if context: parts.append(f"# Contexto\n{context}")
    if task: parts.append(f"# Tarea\n{task}")
    if constraints: parts.append(f"# Restricciones\n{constraints}")
    if format_hint:
        parts.append("# Formato de salida\nDiff unificado y verificación breve.")
    return "\n\n".join(parts)

def route(task_text):
    router = CFG["router"]
    plan_json = call_chat(
        router["base_url"], router["model_id"], SYS_ROUTER, task_text, router["params"]
    )
    try:
        meta = json.loads(plan_json)
    except json.JSONDecodeError:
        # fallback robusto: si no es JSON válido, degrada por heurística
        lower = task_text.lower()
        if any(k in lower for k in ["refactor", "migr", "test", "integr"]):
            return "generator_primary", {"tipo":"heuristica","tam":"M","criticidad":"media"}
        if any(k in lower for k in ["coment", "doc", "snippet", "fix menor", "peque"]):
            return "assistant_qc", {"tipo":"heuristica","tam":"S","criticidad":"baja"}
        return "generator_primary", {"tipo":"desconocido","tam":"M","criticidad":"media"}
    # política simple de mapping:
    tipo = meta.get("tipo","desconocido")
    if tipo in ["refactor","integracion","tests","migracion"]:
        return "generator_primary", meta
    if tipo in ["snippet","comentado","fix_menor","doc"]:
        return "assistant_qc", meta
    return "generator_primary", meta

def cmd_new(args):
    slug = slugify(args.name)
    tdir = ensure_task_dir(slug)
    (tdir/"inputs"/"context.md").write_text(args.context or "", encoding="utf-8")
    (tdir/"inputs"/"tarea.md").write_text(args.task or "", encoding="utf-8")
    (tdir/"inputs"/"restricciones.md").write_text(args.constraints or "", encoding="utf-8")
    print(f"✅ Tarea creada: tasks/{slug}")

def cmd_run(args):
    slug = slugify(args.name)
    tdir = ensure_task_dir(slug)
    context = (tdir/"inputs"/"context.md").read_text(encoding="utf-8") if (tdir/"inputs"/"context.md").exists() else ""
    task = (tdir/"inputs"/"tarea.md").read_text(encoding="utf-8") if (tdir/"inputs"/"tarea.md").exists() else args.task or ""
    constraints = (tdir/"inputs"/"restricciones.md").read_text(encoding="utf-8") if (tdir/"inputs"/"restricciones.md").exists() else args.constraints or ""
    user_prompt = build_user_prompt(context, task, constraints)

    # Routing o override
    if args.model in ["router","qwen","deepseek"]:
        key = {"router":"router","qwen":"generator_primary","deepseek":"assistant_qc"}[args.model]
        meta = {"tipo":"forzado","tam":"S","criticidad":"media"}
    else:
        key, meta = route(task)

    model_cfg = CFG[key]
    system = SYS_QWEN if key=="generator_primary" else SYS_DEEPSEEK
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_path = tdir/"outputs"/f"{ts}-{model_cfg['name']}.md"

    print(f"➡️  Modelo: {model_cfg['name']} | Motivo: {meta.get('tipo','n/a')} | Tam: {meta.get('tam','?')}")
    content = call_chat(model_cfg["base_url"], model_cfg["model_id"], system, user_prompt, model_cfg["params"])
    out_path.write_text(content, encoding="utf-8")
    print(f"💾 Guardado: {out_path}")

    # si trae bloque ```diff, lo extraemos a .patch
    m = re.search(r"```diff([\s\S]*?)```", content)
    if m:
        patch = m.group(1).strip()
        patch_path = tdir/"outputs"/f"{ts}.patch"
        patch_path.write_text(patch, encoding="utf-8")
        print(f"🩹 Diff extraído: {patch_path}")

def cmd_qa(args):
    # QA siempre con DeepSeek sobre la última salida
    tdir = ROOT/"tasks"/args.slug
    outs = sorted((tdir/"outputs").glob("*.md"))
    if not outs:
        print("No hay salidas para revisar.")
        return
    last = outs[-1].read_text(encoding="utf-8")
    model_cfg = CFG["assistant_qc"]
    review_prompt = f"# Salida previa\n\n{last}\n\n# Instruccion\nRevisa de forma concisa y sugiere cambios mínimos."
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_path = tdir/"outputs"/f"{ts}-review-{model_cfg['name']}.md"
    content = call_chat(model_cfg["base_url"], model_cfg["model_id"], SYS_DEEPSEEK, review_prompt, model_cfg["params"])
    out_path.write_text(content, encoding="utf-8")
    print(f"🔎 QA guardado: {out_path}")

def cmd_apply(args):
    # Aplica el último .patch con `git apply` (solo imprime comandos para evitar efectos colaterales)
    tdir = ROOT/"tasks"/args.slug
    patches = sorted((tdir/"outputs").glob("*.patch"))
    if not patches:
        print("No hay parche para aplicar.")
        return
    last_patch = patches[-1]
    print("Sugerencia para aplicar en tu repo (desde la raíz del proyecto destino):")
    print(f"git apply \"{last_patch}\"")

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
    p_run.add_argument("--model", choices=["auto","router","qwen","deepseek"], default="auto")
    p_run.set_defaults(func=cmd_run)

    p_qa = sub.add_parser("qa", help="Revisión con DeepSeek")
    p_qa.add_argument("--slug", required=True)
    p_qa.set_defaults(func=cmd_qa)

    p_apply = sub.add_parser("apply", help="Imprime comando git apply para el último patch")
    p_apply.add_argument("--slug", required=True)
    p_apply.set_defaults(func=cmd_apply)

    args = p.parse_args()
    if not hasattr(args, "func"):
        p.print_help(); sys.exit(1)
    args.func(args)

if __name__ == "__main__":
    main()
