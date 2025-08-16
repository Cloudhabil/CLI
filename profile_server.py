from pathlib import Path
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml

app = FastAPI()
CONFIG = yaml.safe_load(open("config/ui_options.yaml"))
PROFILE_DIR = Path("profiles")
PROFILE_DIR.mkdir(exist_ok=True)

class Settings(BaseModel):
    ui_type: str
    lang: str


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.patch("/profile/{user_id}/settings")
async def update_settings(user_id: str, settings: Settings):
    if settings.ui_type not in CONFIG.get("types", []):
        raise HTTPException(status_code=400, detail="invalid ui_type")
    if settings.lang not in CONFIG.get("languages", []):
        raise HTTPException(status_code=400, detail="unsupported language")
    with open(PROFILE_DIR / f"{user_id}.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(settings.dict(), f)
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7099))
    uvicorn.run("profile_server:app", host="0.0.0.0", port=port)
