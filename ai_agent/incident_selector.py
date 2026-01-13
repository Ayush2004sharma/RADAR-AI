from datetime import datetime
from typing import List, Dict


# ============================================================
# 🔹 PRIORITY WEIGHTS (v1 – deterministic)
# ============================================================

SERVICE_WEIGHT = {
    "backend": 40,
    "auth": 30,
    "worker": 20,
}

SEVERITY_WEIGHT = {
    "crash": 30,
    "exception": 30,
    "failed": 30,
    "error": 20,
    "warning": 10,
}


# ============================================================
# 🔹 INTERNAL HELPERS
# ============================================================

def _service_score(service: str) -> int:
    return SERVICE_WEIGHT.get(service.lower(), 10)


def _severity_score(message: str) -> int:
    msg = message.lower()
    for key, score in SEVERITY_WEIGHT.items():
        if key in msg:
            return score
    return 5


def _frequency_score(count: int) -> int:
    # Higher count → higher priority (capped)
    return min(count * 5, 25)


def _recency_score(last_seen: str) -> int:
    try:
        last = datetime.fromisoformat(last_seen)
        minutes_ago = (datetime.utcnow() - last).total_seconds() / 60

        if minutes_ago < 10:
            return 25
        elif minutes_ago < 60:
            return 20
        elif minutes_ago < 360:
            return 10
        else:
            return 5
    except Exception:
        return 0


# ============================================================
# 🧠 INCIDENT PRIORITIZATION AGENT
# ============================================================

def prioritize_incidents(incidents: List[Dict]) -> Dict:
    """
    Returns ALL ACTIVE incidents sorted by priority (desc),
    with numeric scores and a recommended incident.
    """

    active_incidents = [
        i for i in incidents if i.get("status") == "ACTIVE"
    ]

    prioritized: List[Dict] = []

    for inc in active_incidents:
        score = 0
        reasons = []

        # 1️⃣ Frequency
        freq_score = _frequency_score(inc.get("count", 0))
        score += freq_score
        if freq_score > 0:
            reasons.append("high frequency")

        # 2️⃣ Recency
        rec_score = _recency_score(inc.get("last_seen", ""))
        score += rec_score
        if rec_score >= 20:
            reasons.append("very recent")

        # 3️⃣ Service criticality
        service = inc.get("service", "unknown")
        svc_score = _service_score(service)
        score += svc_score
        reasons.append(f"{service} service")

        # 4️⃣ Message severity
        sev_score = _severity_score(inc.get("message", ""))
        score += sev_score
        if sev_score >= 20:
            reasons.append("severe error")

        prioritized.append({
            "incident_id": str(inc.get("id")),
            "priority_score": score,
            "reason": ", ".join(reasons),
        })

    # 🔽 Sort by highest priority first
    prioritized.sort(
        key=lambda x: x["priority_score"],
        reverse=True,
    )

    return {
        "recommended_incident_id": prioritized[0]["incident_id"]
        if prioritized else None,
        "prioritized_incidents": prioritized,
    }
