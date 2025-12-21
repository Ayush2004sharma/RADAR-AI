import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)

def increment_error(service: str):
    key = f"errors:{service}"
    redis_client.incr(key)

def get_all_errors():
    keys = redis_client.keys("errors:*")
    return {
        key.replace("errors:", ""): int(redis_client.get(key))
        for key in keys
    }
