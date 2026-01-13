from typing import List, Dict
import os

IMPORTANT_DIR_KEYWORDS = [
    "service",
    "services",
    "controller",
    "route",
    "api",
    "handler",
    "model",
    "repo",
    "config",
]

IMPORTANT_EXTENSIONS = {".py", ".js", ".ts", ".tsx"}


# ============================================================
# 🔹 ORIGINAL — SERVICE-BASED SCORING (UNCHANGED)
# ============================================================
def score_file(file: Dict, error_text: str, service: str) -> int:
    """
    Deterministic score for how likely a file is related to an error.
    (Legacy / service-based)
    """
    score = 0
    path = file["path"].lower()
    name = os.path.basename(path)

    # 1️⃣ Filename match in error
    if name in error_text.lower():
        score += 50

    # 2️⃣ Folder relevance
    for key in IMPORTANT_DIR_KEYWORDS:
        if key in path:
            score += 10

    # 3️⃣ Service name hint
    if service.lower() in path:
        score += 15

    # 4️⃣ Code file extension
    _, ext = os.path.splitext(path)
    if ext in IMPORTANT_EXTENSIONS:
        score += 10

    # 5️⃣ Smaller files first (heuristic)
    size = file.get("size", 0)
    if size and size < 20_000:
        score += 5

    return score


def rank_files(
    files: List[Dict],
    logs: List[Dict],
    service: str,
    max_files: int = 5,
) -> List[Dict]:
    """
    Legacy ranking — service scoped.
    """
    error_text = " ".join(log.get("message", "") for log in logs)

    scored = []
    for f in files:
        s = score_file(f, error_text, service)
        if s > 0:
            scored.append({**f, "score": s})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:max_files]


# ============================================================
# 🆕 NEW — INCIDENT-BASED SCORING (ADDITIVE)
# ============================================================
def score_file_for_incident(
    file: Dict,
    error_text: str,
    incident: Dict,
) -> int:
    """
    Deterministic score for incident-scoped ranking.
    Uses incident metadata instead of free service input.
    """
    score = 0
    path = file["path"].lower()
    name = os.path.basename(path)

    # 1️⃣ Filename match in incident logs
    if name in error_text.lower():
        score += 50

    # 2️⃣ Folder relevance
    for key in IMPORTANT_DIR_KEYWORDS:
        if key in path:
            score += 10

    # 3️⃣ Incident service hint (safe, derived)
    service = incident.get("service", "")
    if service and service.lower() in path:
        score += 15

    # 4️⃣ Code file extension
    _, ext = os.path.splitext(path)
    if ext in IMPORTANT_EXTENSIONS:
        score += 10

    # 5️⃣ Smaller files first
    size = file.get("size", 0)
    if size and size < 20_000:
        score += 5

    return score


def rank_files_for_incident(
    files: List[Dict],
    logs: List[Dict],
    incident: Dict,
    max_files: int = 5,
) -> List[Dict]:
    """
    Incident-scoped file ranking.
    This should be used by:
    - /incidents/files/priority
    """
    error_text = " ".join(log.get("message", "") for log in logs)

    scored = []
    for f in files:
        s = score_file_for_incident(f, error_text, incident)
        if s > 0:
            scored.append({**f, "score": s})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:max_files]
