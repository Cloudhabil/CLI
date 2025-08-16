from fastapi import FastAPI
from pydantic import BaseModel
import anyio
from collections import defaultdict, deque
from typing import Dict, Deque
from kb import add_entry

app = FastAPI()
queues: Dict[str, Deque[dict]] = defaultdict(deque)
conds: Dict[str, anyio.Condition] = defaultdict(anyio.Condition)


class PublishReq(BaseModel):
    topic: str
    data: dict


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/publish")
async def publish(req: PublishReq):
    queues[req.topic].append(req.data)
    async with conds[req.topic]:
        conds[req.topic].notify(1)
    add_entry(kind="bus_message", topic=req.topic, payload=req.data)
    return {"status": "ok"}


@app.get("/get")
async def get(topic: str):
    while not queues[topic]:
        async with conds[topic]:
            await conds[topic].wait()
    data = queues[topic].popleft()
    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bus_server:app", host="0.0.0.0", port=7088)
