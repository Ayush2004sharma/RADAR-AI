from fastapi import APIRouter, Body, Depends, HTTPException
from bson import ObjectId
from bson.errors import InvalidId
from ai_agent.incident_selector import prioritize_incidents

from .db import db
from .auth_guard import get_current_user

# 🔹 ORIGINAL imports (unchanged)
from ai_agent.file_priority import (
    rank_files,                  # legacy
    rank_files_for_incident,      # NEW
)
from ai_agent.filesystem import list_project_files, read_project_file
from ai_agent.retriever import (
    retrieve_logs,               # legacy
    retrieve_incident_logs,       # NEW
)
from ai_agent.llm import (
    suggest_fix_for_file,        # legacy
    suggest_fix_for_incident_file,  # NEW
    generate_diagnosis_with_llm, # legacy
    generate_incident_diagnosis, # NEW
)

router = APIRouter()


# ============================================================
# 🔹 SHARED UTILS (ORIGINAL STYLE)
# ============================================================
def parse_object_id(value: str, name: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {name} format"
        )


# ============================================================
# 🔹 LIST ACTIVE INCIDENTS (UNCHANGED)
# ============================================================
@router.get("/incidents")
def list_incidents(project_id: str, user=Depends(get_current_user)):
    project = db.projects.find_one({
        "_id": ObjectId(project_id),
        "user_id": user["_id"]
    })
    if not project:
        raise HTTPException(403, "Forbidden")

    incidents = db.incidents.find(
        {"project_id": project["_id"], "status": "ACTIVE"}
    ).sort("last_seen", -1)

    return [
        {
            "id": str(i["_id"]),
            "service": i.get("service"),
            "message": i.get("message"),
            "file": i.get("file"),
            "line": i.get("line"),
            "count": i.get("count", 0),
            "last_seen": i.get("last_seen"),
            "status": i.get("status", "ACTIVE"),
        }
        for i in incidents
    ]


# ============================================================
# 🆕 INCIDENT DIAGNOSIS (ADDITIVE)
# ============================================================
@router.post("/incidents/diagnose")
def diagnose_incident(payload: dict = Body(...), user=Depends(get_current_user)):
    incident_id = parse_object_id(payload.get("incident_id"), "incident_id")
    project_id = parse_object_id(payload.get("project_id"), "project_id")

    incident = db.incidents.find_one({"_id": incident_id})
    if not incident:
        raise HTTPException(404, "Incident not found")

    project = db.projects.find_one({
        "_id": project_id,
        "user_id": user["_id"]
    })
    if not project:
        raise HTTPException(403, "Forbidden")

    # 🔒 INCIDENT-SCOPED LOGS
    logs = retrieve_incident_logs(str(project_id), incident_id)

    diagnosis = generate_incident_diagnosis(incident, logs)

    return {
        "incident_id": str(incident_id),
        "problem_statement": diagnosis,
        "log_count": len(logs),
    }


# ============================================================
# 🔹 PRIORITIZED FILES (LEGACY + INCIDENT SAFE)
# ============================================================
@router.post("/incidents/files/priority")
def get_prioritized_files(payload: dict = Body(...), user=Depends(get_current_user)):
    incident_id = parse_object_id(payload.get("incident_id"), "incident_id")
    project_id = parse_object_id(payload.get("project_id"), "project_id")

    incident = db.incidents.find_one({"_id": incident_id})
    if not incident:
        raise HTTPException(404, "Incident not found")

    project = db.projects.find_one({
        "_id": project_id,
        "user_id": user["_id"]
    })
    if not project:
        raise HTTPException(403, "Forbidden")

    files = list_project_files(max_files=300)

    # 🔹 Prefer INCIDENT logs if present
    logs = retrieve_incident_logs(str(project_id), incident_id)

    if logs:
        ranked = rank_files_for_incident(
            files=files,
            logs=logs,
            incident=incident,
            max_files=5,
        )
    else:
        # 🔁 fallback (legacy, no behavior loss)
        logs = retrieve_logs(
            project_id=str(project["_id"]),
            project_secret=project["project_secret"],
            service=incident.get("service"),
        )
        ranked = rank_files(
            files=files,
            logs=logs,
            service=incident.get("service"),
            max_files=5,
        )

    return {
        "incident_id": str(incident_id),
        "files": ranked,
    }


# ============================================================
# 🔹 FIX FILE FOR INCIDENT (LEGACY + INCIDENT SAFE)
# ============================================================
@router.post("/incidents/file/fix")
def fix_file_for_incident(payload: dict = Body(...), user=Depends(get_current_user)):
    incident_id = parse_object_id(payload.get("incident_id"), "incident_id")
    project_id = parse_object_id(payload.get("project_id"), "project_id")
    path = payload.get("path")

    if not path:
        raise HTTPException(400, "path is required")

    incident = db.incidents.find_one({
        "_id": incident_id,
        "status": "ACTIVE"
    })
    if not incident:
        raise HTTPException(404, "Active incident not found")

    project = db.projects.find_one({
        "_id": project_id,
        "user_id": user["_id"]
    })
    if not project:
        raise HTTPException(403, "Forbidden")

    # 🔒 Prefer incident logs
    logs = retrieve_incident_logs(str(project_id), incident_id)

    content = read_project_file(path)
    if content is None:
        raise HTTPException(400, "File not accessible")

    if logs:
        fixed_code, explanation = suggest_fix_for_incident_file(
            incident=incident,
            logs=logs,
            path=path,
            content=content,
        )
    else:
        # 🔁 fallback legacy behavior
        legacy_logs = retrieve_logs(
            project_id=str(project["_id"]),
            project_secret=project["project_secret"],
            service=incident.get("service"),
        )
        fixed_code, explanation = suggest_fix_for_file(
            service=incident.get("service"),
            logs=legacy_logs,
            path=path,
            content=content,
        )

    return {
        "incident_id": str(incident_id),
        "path": path,
        "original": content,
        "fixed": fixed_code,
        "explanation": explanation,
    }


# ============================================================
# 🔹 RESOLVE / RETRY INCIDENT (UNCHANGED)
# ============================================================
@router.post("/incidents/resolve")
def resolve_incident(payload: dict = Body(...), user=Depends(get_current_user)):
    incident_id = parse_object_id(payload.get("incident_id"), "incident_id")
    project_id = parse_object_id(payload.get("project_id"), "project_id")
    file_path = payload.get("file_path")
    resolved = payload.get("resolved")

    incident = db.incidents.find_one({"_id": incident_id})
    if not incident:
        raise HTTPException(404, "Incident not found")

    project = db.projects.find_one({
        "_id": project_id,
        "user_id": user["_id"]
    })
    if not project:
        raise HTTPException(403, "Forbidden")

    if resolved:
        db.incidents.update_one(
            {"_id": incident["_id"]},
            {"$set": {
                "status": "RESOLVED",
                "resolved_by": file_path,
                "resolution_type": "user_confirmed",
            }},
        )
    else:
        db.incidents.update_one(
            {"_id": incident["_id"]},
            {"$addToSet": {
                "attempted_files": file_path,
            }},
        )

    return {"status": "ok"}


# ============================================================
# 🆕 INCIDENT PRIORITY API (READ-ONLY, SAFE)
# ============================================================
@router.get("/incidents/priority")
def get_prioritized_incidents(project_id: str, user=Depends(get_current_user)):
    # 🔐 Project access check
    project = db.projects.find_one({
        "_id": ObjectId(project_id),
        "user_id": user["_id"]
    })
    if not project:
        raise HTTPException(403, "Forbidden")

    # 🔹 Fetch ACTIVE incidents ONLY
    incidents = list(db.incidents.find({
        "project_id": project["_id"],
        "status": "ACTIVE"
    }))

    # 🔹 Normalize for agent input
    incident_payload = [
        {
            "id": str(i["_id"]),
            "service": i.get("service"),
            "message": i.get("message"),
            "file": i.get("file"),
            "line": i.get("line"),
            "count": i.get("count", 0),
            "last_seen": i.get("last_seen"),
            "status": i.get("status", "ACTIVE"),
        }
        for i in incidents
    ]

    # 🧠 PRIORITY DECISION (AGENT)
    priority_result = prioritize_incidents(incident_payload)

    return priority_result
