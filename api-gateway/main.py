from fastapi import FastAPI, Body
from redis import Redis
from dotenv import load_dotenv
import os


from ai_agent.agent import run_agent
from .websocket import router as websocket_router
from ai_agent.filesystem import list_project_files, read_project_file
from ai_agent.llm import suggest_related_files
from ai_agent.retriever import retrieve_logs  # moved import to top
from ai_agent.llm import suggest_fix_for_file  # new function you will add
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
from stream_processor.consumer import run_consumer



load_dotenv()


app = FastAPI(title="RADAR-AI API Gateway")
@app.on_event("startup")
def start_consumer():
    t = Thread(target=run_consumer, daemon=True)
    t.start()


redis = Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)



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



# WebSocket routes
app.include_router(websocket_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    result = run_agent(project_id, project_secret, service)
    return result


@app.post("/diagnose/files")
def diagnose_with_files(payload: dict = Body(...)):
    """
    Run diagnosis and then suggest likely-related project files
    based on logs + PROJECT_ROOT directory listing.
    """
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
    """
    List safe project files so the UI can show them to the user.
    """
    files = list_project_files(max_files=200)
    return {"files": files}



@app.post("/project/file")
def get_file_content(payload: dict = Body(...)):
    """
    Read ONE file under PROJECT_ROOT, only after user consent.
    """
    path = payload.get("path")
    if not path:
        return {
            "status": "failed",
            "reason": "File path is required",
        }


    content = read_project_file(path)
    if content is None:
        return {
            "status": "failed",
            "reason": "File is not accessible or not allowed",
        }


    return {
        "status": "success",
        "path": path,
        "content": content,
    }


@app.post("/diagnose/file/fix")
def diagnose_and_fix_file(payload: dict = Body(...)):
    
    """
    After the user selects a file that looks related,
    send logs + current file content to LLM and get a suggested fixed version.
    """
    project_id = payload.get("project_id")
    project_secret = payload.get("project_secret")
    service = payload.get("service")
    path = payload.get("path")

    if not project_id or not project_secret or not service or not path:
        return {
            "status": "failed",
            "reason": "project_id, project_secret, service and path are required",
        }

    logs = retrieve_logs(project_id, project_secret, service)
    if not logs:
        return {
            "status": "failed",
            "reason": "No logs found for this project/service",
        }

    content = read_project_file(path)
    if content is None:
        return {
            "status": "failed",
            "reason": "File is not accessible or not allowed",
        }

    fixed_code, explanation = suggest_fix_for_file(service, logs, path, content)

    return {
        "status": "success",
        "project_id": project_id,
        "service": service,
        "path": path,
        "original": content,
        "fixed": fixed_code,
        "explanation": explanation,
    }

    """
    After the user selects a file that looks related,
    send logs + current file content to LLM and get a suggested fixed version.
    """
    service = payload.get("service")
    path = payload.get("path")


    if not service or not path:
        return {
            "status": "failed",
            "reason": "Service name and file path are required",
        }


    # 1) Get recent logs for this service
    logs = retrieve_logs(service)
    if not logs:
        return {
            "status": "failed",
            "reason": "No logs found for this service",
        }


    # 2) Read file content from PROJECT_ROOT
    content = read_project_file(path)
    if content is None:
        return {
            "status": "failed",
            "reason": "File is not accessible or not allowed",
        }


    # 3) Ask LLM to propose a fixed version of this file
    fixed_code, explanation = suggest_fix_for_file(service, logs, path, content)


    return {
        "status":  "success",
        "service": service,
        "path": path,
        "original": content,
        "fixed": fixed_code,
        "explanation": explanation,
    }