from datetime import datetime, timedelta
import time

from .db import db   # ✅ SAME SHARED DB

RESOLVE_AFTER_MINUTES = 200

def run_resolver():
    while True:
        cutoff = datetime.utcnow() - timedelta(minutes=RESOLVE_AFTER_MINUTES)

        db.incidents.update_many(
            {
                "status": "ACTIVE",
                "last_seen": {"$lt": cutoff}
            },
            {
                "$set": {
                    "status": "RESOLVED",
                    "resolved_at": datetime.utcnow()
                }
            }
        )

        time.sleep(60)  # every 1 minute
