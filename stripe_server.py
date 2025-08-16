import os
import stripe
from fastapi import FastAPI, Request, HTTPException
from kb import add_entry
import requests

app = FastAPI()
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
BUS_URL = os.environ.get("BUS_URL", "http://127.0.0.1:7088")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/stripe/webhook")
async def webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    add_entry(kind="stripe_event", type=event.get("type"))
    for role in ["CFO", "COO", "CEO", "CMO", "CPO"]:
        requests.post(f"{BUS_URL}/publish", json={"topic": role, "data": {"stripe_event": event.get("type")}})
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("stripe_server:app", host=os.environ.get("STRIPE_BIND", "0.0.0.0"),
                port=int(os.environ.get("STRIPE_PORT", 7077)))
