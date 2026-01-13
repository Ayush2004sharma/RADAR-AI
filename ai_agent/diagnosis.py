from typing import Dict, List


def diagnose_incident(incident: Dict, logs: List[Dict]) -> str:
    """
    Deterministic incident diagnosis.

    Rules:
    - Uses ONLY incident + its logs
    - No speculation
    - No LLM dependency
    - Always returns something user-readable
    """

    if not incident:
        return "Incident not found."

    if not logs:
        return (
            f"Incident '{incident.get('message')}' exists, "
            "but no logs are currently available for diagnosis."
        )

    # Take most recent logs
    recent_logs = logs[:5]

    messages = []
    for log in recent_logs:
        msg = log.get("message")
        if msg:
            messages.append(msg)

    if not messages:
        return (
            f"Incident '{incident.get('message')}' is active, "
            "but logs do not contain readable error messages."
        )

    # Clear, non-magical summary
    return (
        f"Incident '{incident.get('message')}' is recurring. "
        f"Recent occurrences include: "
        + " | ".join(messages)
    )
