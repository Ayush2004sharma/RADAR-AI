import os
from typing import List, Dict

from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING
from pymongo.errors import PyMongoError
from bson import ObjectId

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "radar_ai")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "logs")

_mongo_client = MongoClient(MONGO_URI)
_db = _mongo_client[MONGO_DB]
_logs_collection = _db[MONGO_COLLECTION]


# ============================================================
# 🟢 ORIGINAL FUNCTION — DO NOT REMOVE (0% LOSS)
# ============================================================
def retrieve_logs(
    project_id: str,
    project_secret: str,
    service: str,
    limit: int = 20,
) -> List[Dict]:
    """
    Fetch recent logs for a given project + service.

    Legacy / ingestion usage.
    NOT to be used for incident AI.
    """
    if not project_id or not project_secret or not service:
        return []

    try:
        cursor = (
            _logs_collection
            .find({
                "project_id": project_id,
                "project_secret": project_secret,
                "service": service,
            })
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )
        return list(cursor)
    except PyMongoError:
        return []


# ============================================================
# 🆕 NEW FUNCTION — INCIDENT SCOPED (ADDITIVE ONLY)
# ============================================================
def retrieve_incident_logs(
    project_id: str,
    incident_id: ObjectId,
    limit: int = 50,
) -> List[Dict]:
    """
    Fetch logs STRICTLY for a single incident.

    This is used by:
    - diagnosis
    - file priority
    - fix suggestion
    """
    if not project_id or not incident_id:
        return []

    try:
        cursor = (
            _logs_collection
            .find({
                "project_id": project_id,
                "incident_id": incident_id,
            })
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )
        return list(cursor)
    except PyMongoError:
        return []
