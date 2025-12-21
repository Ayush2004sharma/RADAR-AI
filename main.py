from fastapi import FastAPI
import logging
import time
import os

import redis
from dotenv import load_dotenv


load_dotenv()

STREAM_KEY = "logs-stream"  # must match RADAR-AI stream-processor

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    username=os.getenv("REDIS_USERNAME") or None,
    password=os.getenv("REDIS_PASSWORD") or None,
    decode_responses=True,
)


class RadarRedisHandler(logging.Handler):
    """
    Duplicates logs to Redis Stream for RADAR-AI,
    while normal handlers still print to terminal.
    """

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_entry = {
                "service": self.service_name,
                "level": record.levelname,
                "message": self.format(record),
                "timestamp": str(time.time()),
            }
            redis_client.xadd(STREAM_KEY, log_entry)
        except Exception:
            # Never break the service if Redis/logging fails
            pass


# ---- logging setup ----
SERVICE_NAME = "radar-monitored-service"  # choose your final name

logger = logging.getLogger(SERVICE_NAME)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

radar_handler = RadarRedisHandler(service_name=SERVICE_NAME)
radar_handler.setLevel(logging.INFO)
radar_handler.setFormatter(logging.Formatter("%(message)s"))

# avoid duplicate handlers on reload
if not any(isinstance(h, RadarRedisHandler) for h in logger.handlers):
    logger.addHandler(console_handler)
    logger.addHandler(radar_handler)


# ---- FastAPI app ----
app = FastAPI(title="RADAR Monitored Service")


@app.get("/health")
def health():
    logger.info("Health check requested")
    return {"status": "ok"}


@app.get("/demo-error")
def demo_error():
    logger.error("Example error: something failed in RADAR monitored service")
    return {"status": "error simulated"}
