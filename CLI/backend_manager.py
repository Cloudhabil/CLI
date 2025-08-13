#!/usr/bin/env python3
import os, subprocess, time
from urllib.parse import urlparse
import requests

DEF_TIMEOUT = 90

def _port_from_url(base_url: str) -> int:
    u = urlparse(base_url)
    return u.port or (8081 if "8081" in base_url else 8080)

def _is_alive(base_url: str) -> bool:
    try:
        r = requests.get(base_url.rstrip("/") + "/models", timeout=2)
        return r.ok
    except Exception:
        return False

def ensure_server(key: str, cfg: dict, wait=DEF_TIMEOUT) -> bool:
    """
    Lanza llama.cpp server.exe si no está vivo ya.
    Acepta en cfg: server_path, model_path, n_ctx, ngl, threads, n_batch, n_ubatch, base_url
    """
    base = cfg["base_url"].rstrip("/v1").rstrip("/")
    if _is_alive(base + "/v1"):
        return True

    server = cfg["server_path"]
    model  = cfg["model_path"]
    port   = _port_from_url(cfg["base_url"])

    args = [
        server, "-m", model,
        "-c", str(cfg.get("n_ctx", 4096)),
        "-ngl", str(cfg.get("ngl", 0)),
        "--port", str(port),
        "--host", "127.0.0.1",
        "--no-webui"
    ]
    if cfg.get("threads"):  args += ["-t", str(cfg["threads"])]
    if cfg.get("n_batch"):  args += ["-b", str(cfg["n_batch"])]
    if cfg.get("n_ubatch"): args += ["-ub", str(cfg["n_ubatch"])]

    creationflags = 0x08000000  # CREATE_NO_WINDOW (Windows)
    try:
        subprocess.Popen(
            args,
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"{key}: no pude lanzar server: {e}")
        return False

    # Esperar a que escuche
    base_v1 = base + "/v1"
    for _ in range(wait):
        if _is_alive(base_v1):
            return True
        time.sleep(1)
    return False
