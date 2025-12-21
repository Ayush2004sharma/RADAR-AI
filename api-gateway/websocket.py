import asyncio
import os
from fastapi import APIRouter, WebSocket
from redis import Redis
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

redis = Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)

@router.websocket("/ws/metrics")
async def metrics_ws(websocket: WebSocket):
    await websocket.accept()

    while True:
        keys = redis.keys("errors:*")
        data = {
            key.replace("errors:", ""): int(redis.get(key))
            for key in keys
        }

        await websocket.send_json(data)
        await asyncio.sleep(2)
