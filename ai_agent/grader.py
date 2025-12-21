from typing import List, Dict

MIN_LOGS = 5

def grade_logs(logs: List[Dict]) -> bool:
    """
    Decide if logs are good enough to attempt an AI diagnosis.

    Requirements:
    - At least MIN_LOGS logs.
    - At least one ERROR log.
    - If there are many logs, try to avoid cases where all messages are identical.
    """
    if not logs:
        return False

    if len(logs) < MIN_LOGS:
        return False

    error_logs = [l for l in logs if l.get("level") == "ERROR"]
    if not error_logs:
        return False

    # Only apply noise filter when there are a lot of logs.
    # For small batches (e.g. 5–20) it's okay if messages are identical.
    if len(logs) >= 20:
        messages = [str(l.get("message", "")) for l in logs]
        unique_messages = {m for m in messages if m}
        if len(unique_messages) <= 1:
            return False

    return True
