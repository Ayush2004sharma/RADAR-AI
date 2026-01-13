import os
from typing import List, Dict, Tuple

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)


# ============================================================
# 🔹 SHARED UTILITY (ORIGINAL)
# ============================================================
def _format_logs_for_prompt(logs: List[Dict]) -> str:
    lines = []
    for l in logs:
        level = l.get("level", "UNKNOWN")
        ts = l.get("timestamp", "")
        msg = l.get("message", "")
        lines.append(f"[{level}] {ts} - {msg}")
    return "\n".join(lines)


# ============================================================
# 🔹 ORIGINAL — SERVICE-BASED DIAGNOSIS (UNCHANGED)
# ============================================================
def generate_diagnosis_with_llm(service: str, logs: List[Dict]) -> str:
    """
    LLM generates diagnosis ONLY from provided logs.
    """
    log_text = _format_logs_for_prompt(logs)

    prompt = f"""
You are a senior backend engineer helping diagnose production incidents.

You MUST strictly follow these rules:
- ONLY use the logs provided below as evidence.
- If the logs are insufficient, ambiguous, or do not clearly indicate a root cause,
  you MUST say that you cannot determine the exact root cause from the logs.
- Do NOT speculate about configuration, code, or infrastructure that is not visible in the logs.
- Do NOT invent services, files, or errors that are not in the logs.
- Keep the answer grounded in specific log messages or patterns.

Service: {service}

Logs:
{log_text}

Task:
1. Briefly state the most likely root cause OR clearly state that the logs are insufficient.
2. Mention at least one specific log pattern or message that supports your conclusion.

Answer in 1–3 short sentences.
"""

    response = _llm.invoke(prompt)
    return response.content.strip()


# ============================================================
# 🔹 ORIGINAL — FILE SUGGESTION (UNCHANGED)
# ============================================================
def suggest_related_files(
    service: str,
    logs: List[Dict],
    files: List[Dict]
) -> List[Dict]:
    """
    Use the LLM to suggest a small list of likely-related files
    based on error logs and project file names.
    """
    if not logs or not files:
        return []

    log_text = _format_logs_for_prompt(logs)
    file_list_text = "\n".join(f"- {f['path']}" for f in files)

    prompt = f"""
You are helping debug a backend service based on its logs and the project directory.

Service: {service}

Error-focused logs:
{log_text}

Project files (relative paths):
{file_list_text}

Rules:
- ONLY suggest files that appear in the list above.
- Base your suggestions on obvious string matches from logs.
- If you are not reasonably confident, return an empty list.
- Do NOT invent file paths.

Return ONLY valid JSON.
"""

    response = _llm.invoke(prompt)
    text = response.content.strip()

    try:
        import json

        suggestions = json.loads(text)
        result: List[Dict] = []
        allowed_paths = {f["path"] for f in files}

        if isinstance(suggestions, list):
            for item in suggestions:
                if not isinstance(item, dict):
                    continue
                path = item.get("path")
                reason = item.get("reason", "")
                if path in allowed_paths:
                    result.append({"path": path, "reason": reason})
        return result
    except Exception:
        return []


# ============================================================
# 🔹 ORIGINAL — FILE FIX (UNCHANGED)
# ============================================================
def suggest_fix_for_file(
    service: str,
    logs: List[Dict],
    path: str,
    content: str,
) -> Tuple[str, str]:
    """
    Use the LLM to propose a fixed version of the file,
    using ONLY the given logs + file content.
    """
    log_text = _format_logs_for_prompt(logs)

    prompt = f"""
You are a senior backend engineer.

Service name: {service}
File path: {path}

Error logs:
{log_text}

Current file content:
{content}

Instructions:
- Use ONLY the logs and the file content above.
- Do NOT guess about other files.
- If logs do NOT clearly show a bug, return the same code.

Format:
EXPLANATION:
...

UPDATED_FILE:
...
"""

    response = _llm.invoke(prompt)
    text = response.content.strip()

    explanation = ""
    fixed_code = content

    if "UPDATED_FILE:" in text:
        parts = text.split("UPDATED_FILE:", 1)
        explanation_part = parts[0]
        file_part = parts[1]

        if "EXPLANATION:" in explanation_part:
            explanation = explanation_part.split("EXPLANATION:", 1)[1].strip()
        else:
            explanation = explanation_part.strip()

        fixed_code = file_part.strip()

    return fixed_code, explanation


# ============================================================
# 🆕 NEW — INCIDENT-BASED DIAGNOSIS (ADDITIVE)
# ============================================================
def generate_incident_diagnosis(
    incident: Dict,
    logs: List[Dict],
) -> str:
    """
    Incident-scoped diagnosis.
    Uses incident metadata instead of service.
    """
    log_text = _format_logs_for_prompt(logs)

    prompt = f"""
You are diagnosing a SINGLE INCIDENT.

Incident ID: {incident.get("_id")}
Incident message: {incident.get("message")}

Rules:
- Use ONLY the logs below.
- Do NOT assume anything outside this incident.

Logs:
{log_text}

Task:
State the most likely root cause OR say logs are insufficient.
"""

    response = _llm.invoke(prompt)
    return response.content.strip()


# ============================================================
# 🆕 NEW — INCIDENT-BASED FILE FIX (ADDITIVE)
# ============================================================
def suggest_fix_for_incident_file(
    incident: Dict,
    logs: List[Dict],
    path: str,
    content: str,
) -> Tuple[str, str]:
    """
    Incident-scoped fix suggestion.
    """
    log_text = _format_logs_for_prompt(logs)

    prompt = f"""
You are fixing code for a SINGLE INCIDENT.

Incident ID: {incident.get("_id")}
Incident message: {incident.get("message")}
File path: {path}

Logs:
{log_text}

File content:
{content}

Rules:
- Use ONLY the logs + this file.
- Do NOT reference other files.

Format:
EXPLANATION:
...

UPDATED_FILE:
...
"""

    response = _llm.invoke(prompt)
    text = response.content.strip()

    explanation = ""
    fixed_code = content

    if "UPDATED_FILE:" in text:
        parts = text.split("UPDATED_FILE:", 1)
        explanation_part = parts[0]
        file_part = parts[1]

        if "EXPLANATION:" in explanation_part:
            explanation = explanation_part.split("EXPLANATION:", 1)[1].strip()
        else:
            explanation = explanation_part.strip()

        fixed_code = file_part.strip()

    return fixed_code, explanation
