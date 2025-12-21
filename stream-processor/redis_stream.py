import redis
import os
from dotenv import load_dotenv

load_dotenv()

STREAM_KEY = "logs-stream"

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)

def push_log(log: dict):
    """Push a log event to Redis Stream."""
    redis_client.xadd(STREAM_KEY, log)

def read_logs(last_id="0-0", block=5000):
    """Read log events from Redis Stream."""
    return redis_client.xread(
        {STREAM_KEY: last_id},
        block=block
    )
