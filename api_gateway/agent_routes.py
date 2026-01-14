from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId

from .db import db
from .agent_state import (
    FILE_STRUCTURE_CACHE,
    FILE_REQUEST_CACHE,
    FILE_CONTENT_CACHE,
)

router = APIRouter()
@router.post("/agent/structure")
def receive_structure(payload: dict):
    project_id = payload.get("project_id")
    project_secret = payload.get("project_secret")
    files = payload.get("files", [])

    project = db.projects.find_one({
        "_id": ObjectId(project_id),
        "project_secret": project_secret
    })
    if not project:
        raise HTTPException(403, "Invalid project")

    FILE_STRUCTURE_CACHE[project_id] = {
        "files": files,
        "updated_at": datetime.utcnow()
    }

    return {"status": "structure_received", "count": len(files)}


@router.post("/agent/request-file")
def request_file(payload: dict):
    project_id = payload.get("project_id")
    path = payload.get("path")

    FILE_REQUEST_CACHE[project_id] = {
        "path": path,
        "status": "WAITING"
    }

    return {"status": "requested", "path": path}
@router.get("/agent/poll")
def poll(project_id: str, project_secret: str):
    project = db.projects.find_one({
        "_id": ObjectId(project_id),
        "project_secret": project_secret
    })
    if not project:
        raise HTTPException(403, "Invalid project")

    req = FILE_REQUEST_CACHE.get(project_id)
    if not req or req["status"] != "WAITING":
        return {"file": None}

    return {"file": req["path"]}


@router.post("/agent/file-content")
def receive_file(payload: dict):
    project_id = payload.get("project_id")
    project_secret = payload.get("project_secret")
    path = payload.get("path")
    content = payload.get("content")

    project = db.projects.find_one({
        "_id": ObjectId(project_id),
        "project_secret": project_secret
    })
    if not project:
        raise HTTPException(403, "Invalid project")

    FILE_CONTENT_CACHE[project_id] = {
        "path": path,
        "content": content,
        "received_at": datetime.utcnow()
    }

    if project_id in FILE_REQUEST_CACHE:
        FILE_REQUEST_CACHE[project_id]["status"] = "RECEIVED"

    return {"status": "file_received"}
