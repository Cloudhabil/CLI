#!/usr/bin/env python3
from ch_cli import CFG
try:
    from ch_cli import HAVE_LLAMA, _get_router
except Exception:
    HAVE_LLAMA = False

from backend_manager import ensure_server

def main():
    if HAVE_LLAMA:
        try:
            _get_router()
            print("router: OK (in-process)")
        except Exception as e:
            print(f"router: FAIL ({e})")
    else:
        ok = ensure_server("router", CFG["router"], wait=90)
        print(f"router-http: {'OK' if ok else 'FAIL'}")

    for key in ["generator_primary", "assistant_qc"]:
        try:
            ok = ensure_server(key, CFG[key], wait=90)
            print(f"{key}: {'OK' if ok else 'FAIL'}")
        except Exception as e:
            print(f"{key}: ERROR {e}")

if __name__ == "__main__":
    main()
