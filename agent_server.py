import os
import threading
from fastapi import FastAPI
from pydantic import BaseModel
from models.backend import make_client
from bus_client import BusClient
from kb import add_entry

role = os.environ.get('AGENT_ROLE', 'AGENT')
model_kind = os.environ.get('MODEL_KIND', 'ollama')
model_endpoint = os.environ.get('MODEL_ENDPOINT')
model_name = os.environ.get('MODEL_NAME')
prompt_path = os.environ.get('AGENT_PROMPT')

client = make_client(model_kind, model_endpoint, model_name)
with open(prompt_path, 'r', encoding='utf-8') as f:
    system_prompt = f.read().strip()

history = [{'role': 'system', 'content': system_prompt}]
app = FastAPI()

bus_url = os.environ.get('BUS_URL')
bus_client = None
if bus_url:
    def handler(sender, text):
        history.append({'role': 'user', 'content': text})
        add_entry('bus_message', role, f"{sender}: {text}")
    bus_client = BusClient(bus_url, role, handler)

class ChatReq(BaseModel):
    text: str

class PublishReq(BaseModel):
    target: str
    text: str

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.post('/chat')
async def chat(req: ChatReq):
    history.append({'role': 'user', 'content': req.text})
    resp = client.chat(history)
    history.append({'role': 'assistant', 'content': resp})
    add_entry('agent_chat', role, f"{req.text} -> {resp}")
    return {'response': resp}

@app.post('/publish')
async def publish(req: PublishReq):
    if bus_client:
        bus_client.publish(req.target, role, req.text)
    add_entry('agent_publish', role, f"{req.target}: {req.text}")
    return {'status': 'ok'}

@app.post('/wake')
async def wake():
    add_entry('agent_wake', role, 'woke')
    return {'status': 'ok'}

@app.post('/handoff')
async def handoff(req: PublishReq):
    if bus_client:
        bus_client.publish(req.target, role, req.text)
    add_entry('agent_handoff', role, f"{req.target}: {req.text}")
    return {'status': 'ok'}
