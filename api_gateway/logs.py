from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
import hashlib
import re

from .db import db   # ✅ SHARED DB (IMPORTANT)

router = APIRouter()

# -------- Schema --------

class LogIngestRequest(BaseModel):
    project_id: str
    project_secret: str
    service: str
    level: str
    message: str
    file: str | None = None
    line: int | None = None

# -------- Helpers --------

def normalize_message(msg: str) -> str:
    msg = msg.lower()
    msg = re.sub(r"\d+", "", msg)
    msg = re.sub(r"\s+", " ", msg)
    return msg.strip()

# -------- Route --------
@router.post("/logs/ingest")
def ingest_log(data: LogIngestRequest):
    # 1️⃣ Validate project
    try:
        project_oid = ObjectId(data.project_id)
    except InvalidId:
        raise HTTPException(401, "Invalid project_id format")

    project = db.projects.find_one({
        "_id": project_oid,
        "project_secret": data.project_secret,
    })

    if not project:
        raise HTTPException(401, "Invalid project credentials")

    now = datetime.utcnow()
    incident_id = None

    # 2️⃣ INCIDENT ENGINE (ERROR only)
    if data.level.upper() == "ERROR":
        normalized_message = normalize_message(data.message)

        fingerprint = hashlib.sha256(
            f"{project_oid}:{data.service}:{normalized_message}:{data.file}:{data.line}".encode()
        ).hexdigest()

        incident = db.incidents.find_one({
            "project_id": project_oid,
            "fingerprint": fingerprint,
            "status": "ACTIVE",
        })

        if incident:
            incident_id = incident["_id"]
            db.incidents.update_one(
                {"_id": incident_id},
                {
                    "$set": {"last_seen": now},
                    "$inc": {"count": 1},
                },
            )
        else:
            res = db.incidents.insert_one({
                "project_id": project_oid,
                "service": data.service,
                "fingerprint": fingerprint,
                "message": normalized_message,
                "file": data.file,
                "line": data.line,
                "status": "ACTIVE",
                "count": 1,
                "first_seen": now,
                "last_seen": now,
            })
            incident_id = res.inserted_id

    # 3️⃣ Store raw log (LINKED TO INCIDENT)
    db.logs.insert_one({
        "project_id": project_oid,
        "incident_id": incident_id,
        "service": data.service,
        "level": data.level,
        "message": data.message,
        "file": data.file,
        "line": data.line,
        "timestamp": now,
    })

    return {"status": "success"}
