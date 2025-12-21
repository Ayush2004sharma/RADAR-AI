import os
from typing import List, Dict

from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING
from pymongo.errors import PyMongoError


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "radar_ai")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "logs")

_mongo_client = MongoClient(MONGO_URI)
_db = _mongo_client[MONGO_DB]
_logs_collection = _db[MONGO_COLLECTION]


def retrieve_logs(
    project_id: str,
    project_secret: str,
    service: str,
    limit: int = 20,
) -> List[Dict]:
    """
    Fetch recent logs for a given project + service.

    Fails safe:
    - On any DB error, returns an empty list so the grader can block diagnosis.
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
