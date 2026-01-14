from bson import ObjectId
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import secrets

from .db import db                     # ✅ SHARED DB
from .auth_guard import get_current_user
from ai_agent.filesystem import list_project_files, read_project_file

router = APIRouter()

# -------- Schema --------

class CreateProjectRequest(BaseModel):
    name: str

# -------- Routes --------

@router.post("/projects")
def create_project(
    data: CreateProjectRequest,
    user=Depends(get_current_user),
):
    project = {
        "user_id": user["_id"],
        "name": data.name,
        "project_secret": secrets.token_hex(16),
        "created_at": datetime.utcnow(),
    }

    result = db.projects.insert_one(project)

    return {
        "project_id": str(result.inserted_id),
        "project_secret": project["project_secret"],
    }


@router.get("/projects")
def list_projects(user=Depends(get_current_user)):
    projects = db.projects.find({"user_id": user["_id"]})

    return [
        {
            "id": str(p["_id"]),
            "name": p["name"],
            "project_secret": p["project_secret"],
            "created_at": p.get("created_at"),
        }
        for p in projects
    ]


@router.get("/project/files")
def get_project_files(project_id: str, user=Depends(get_current_user)):
    project = db.projects.find_one({
        "_id": ObjectId(project_id),
        "user_id": user["_id"],
    })

    if not project:
        raise HTTPException(403, "Forbidden")

    files = list_project_files(max_files=300)
    return {"files": files}


@router.post("/project/file")
def read_project_file_api(
    payload: dict = Body(...),
    user=Depends(get_current_user),
):
    project_id = payload.get("project_id")
    path = payload.get("path")

    if not project_id or not path:
        raise HTTPException(400, "project_id and path required")

    project = db.projects.find_one({
        "_id": ObjectId(project_id),
        "user_id": user["_id"],
    })

    if not project:
        raise HTTPException(403, "Forbidden")

    content = read_project_file(path)
    if content is None:
        raise HTTPException(400, "File not accessible")

    return {
        "path": path,
        "content": content,
    }
