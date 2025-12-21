from fastapi import FastAPI, Body
from redis import Redis
from dotenv import load_dotenv
import os
import threading
from contextlib import asynccontextmanager

from ai_agent.agent import run_agent
from .websocket import router as websocket_router
from ai_agent.filesystem import list_project_files, read_project_file
from ai_agent.llm import suggest_related_files, suggest_fix_for_file
from ai_agent.retriever import retrieve_logs
from fastapi.middleware.cors import CORSMiddleware
from stream_processor.consumer import start_consumer

load_dotenv()


# -------------------- LIFESPAN --------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    consumer_thread = threading.Thread(
        target=start_consumer,
        daemon=True
    )
    consumer_thread.start()
    print("Background consumer started")

    yield  # App runs here

    # Shutdown (optional cleanup)
    print("Shutting down API...")


# -------------------- APP --------------------
app = FastAPI(
    title="RADAR-AI API Gateway",
    lifespan=lifespan
)


# -------------------- REDIS --------------------
redis = Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)


# -------------------- MIDDLEWARE --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket_router)


# -------------------- ROUTES --------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics/errors")
def get_error_metrics():
    keys = redis.keys("errors:*")
    return {
        key.replace("errors:", ""): int(redis.get(key) or 0)
        for key in keys
    }


@app.post("/diagnose")
def diagnose(payload: dict = Body(...)):
    project_id = payload.get("project_id")
    project_secret = payload.get("project_secret")
    service = payload.get("service")

    if not project_id or not project_secret or not service:
        return {
            "status": "failed",
            "reason": "project_id, project_secret and service are required",
        }

    return run_agent(project_id, project_secret, service)


@app.post("/diagnose/files")
def diagnose_with_files(payload: dict = Body(...)):
    project_id = payload.get("project_id")
    project_secret = payload.get("project_secret")
    service = payload.get("service")

    if not project_id or not project_secret or not service:
        return {
            "status": "failed",
            "reason": "project_id, project_secret and service are required",
        }

    diag_result = run_agent(project_id, project_secret, service)

    if diag_result.get("status") != "success":
        return diag_result

    files = list_project_files(max_files=200)
    logs = retrieve_logs(project_id, project_secret, service)
    suggestions = suggest_related_files(service, logs, files)

    return {
        "status": "success",
        "project_id": project_id,
        "service": service,
        "diagnosis": diag_result.get("diagnosis"),
        "attempt": diag_result.get("attempt"),
        "confidence": diag_result.get("confidence"),
        "files": suggestions,
    }


@app.get("/project/files")
def list_files():
    return {"files": list_project_files(max_files=200)}


@app.post("/project/file")
def get_file_content(payload: dict = Body(...)):
    path = payload.get("path")
    if not path:
        return {"status": "failed", "reason": "File path is required"}

    content = read_project_file(path)
    if content is None:
        return {"status": "failed", "reason": "File not accessible"}

    return {"status": "success", "path": path, "content": content}


@app.post("/diagnose/file/fix")
def diagnose_and_fix_file(payload: dict = Body(...)):
    project_id = payload.get("project_id")
    project_secret = payload.get("project_secret")
    service = payload.get("service")
    path = payload.get("path")

    if not all([project_id, project_secret, service, path]):
        return {
            "status": "failed",
            "reason": "project_id, project_secret, service and path are required",
        }

    logs = retrieve_logs(project_id, project_secret, service)
    if not logs:
        return {"status": "failed", "reason": "No logs found"}

    content = read_project_file(path)
    if content is None:
        return {"status": "failed", "reason": "File not accessible"}

    fixed_code, explanation = suggest_fix_for_file(
        service, logs, path, content
    )

    return {
        "status": "success",
        "project_id": project_id,
        "service": service,
        "path": path,
        "original": content,
        "fixed": fixed_code,
        "explanation": explanation,
    }
