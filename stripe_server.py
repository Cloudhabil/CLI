import os
import requests
from fastapi import FastAPI, Request, HTTPException
import stripe
from kb import add_entry

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
BUS_URL = f"http://{os.environ.get('BUS_HOST','127.0.0.1')}:{os.environ.get('BUS_PORT','7088')}"

app = FastAPI()

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.post('/stripe/webhook')
async def webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    add_entry('stripe_event', event['type'], event.get('id',''))
    for role in ['CFO', 'COO', 'CEO', 'CMO', 'CPO']:
        requests.post(f"{BUS_URL}/publish", json={'topic': role, 'sender': 'STRIPE', 'text': event['type']}, timeout=5)
    return {'status': 'ok'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=os.environ.get('STRIPE_BIND','127.0.0.1'), port=int(os.environ.get('STRIPE_PORT','7077')))
