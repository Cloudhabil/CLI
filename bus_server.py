import anyio
from fastapi import FastAPI
from pydantic import BaseModel
from collections import defaultdict, deque
from kb import add_entry
import os

app = FastAPI()
queues = defaultdict(lambda: {'cond': anyio.Condition(), 'messages': deque()})

class PubReq(BaseModel):
    topic: str
    sender: str
    text: str

@app.get('/health')
async def health():
    return {'status': 'ok'}

@app.post('/publish')
async def publish(req: PubReq):
    q = queues[req.topic]
    async with q['cond']:
        q['messages'].append({'sender': req.sender, 'text': req.text})
        q['cond'].notify_all()
    add_entry('bus_message', req.topic, f"{req.sender}: {req.text}")
    return {'status': 'ok'}

@app.get('/get/{topic}')
async def get_topic(topic: str):
    q = queues[topic]
    async with q['cond']:
        while not q['messages']:
            await q['cond'].wait()
        msg = q['messages'].popleft()
    return msg


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=os.environ.get('BUS_HOST','127.0.0.1'), port=int(os.environ.get('BUS_PORT','7088')))
