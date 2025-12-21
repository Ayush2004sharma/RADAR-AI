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


def _format_logs_for_prompt(logs: List[Dict]) -> str:
    lines = []
    for l in logs:
        level = l.get("level", "UNKNOWN")
        ts = l.get("timestamp", "")
        msg = l.get("message", "")
        lines.append(f"[{level}] {ts} - {msg}")
    return "\n".join(lines)


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


def suggest_related_files(service: str, logs: List[Dict], files: List[Dict]) -> List[Dict]:
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
- Base your suggestions on:
  - route names, endpoints, or feature names mentioned in the logs,
  - error messages (e.g. function names, model names, modules),
  - and any other obvious string matches.
- If you are not reasonably confident about any file, return an empty list.
- Do NOT invent file paths that are not in the list.
- Keep the output short and structured.

Task:
From the file list, choose up to 3 files that are most likely related
to the error shown in the logs.

For each suggested file, provide:
- "path": the file path exactly as in the list,
- "reason": a short explanation referencing the logs.

Return ONLY valid JSON in the following format:

[
  {{ "path": "path/from/list.js", "reason": "..." }},
  ...
]
"""

    response = _llm.invoke(prompt)
    text = response.content.strip()

    # Very simple, safe JSON parsing; if it fails, return empty list
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
                if path in allowed_paths and isinstance(reason, str):
                    result.append({"path": path, "reason": reason})
        return result
    except Exception:
        return []


# ---------- NEW: fix selected file ----------
def suggest_fix_for_file(
    service: str,
    logs: List[Dict],
    path: str,
    content: str,
) -> Tuple[str, str]:
    """
    Use the LLM to propose a fixed version of the file,
    using ONLY the given logs + file content.

    Returns (fixed_code, short_explanation).
    """
    log_text = _format_logs_for_prompt(logs)

    prompt = f"""
You are a senior backend engineer.

Service name: {service}
File path: {path}

Error logs (only evidence you can use):
{log_text}

Current file content:
{content}

Instructions:
- Use ONLY the logs and the file content above as evidence.
- Do NOT guess about other files, configs, or services.
- If logs do NOT clearly show a bug in this file, say that and return the same code.
- If you see a clear bug related to the logs, return a fixed version of THIS file.
- Keep style similar to the existing code.

Tasks:
1. Briefly explain the bug and the change you will make (1–3 sentences).
2. Then output ONLY the full updated file content.

Format:
EXPLANATION:
<one short paragraph>

UPDATED_FILE:
<full updated file here>
```"""

    response = _llm.invoke(prompt)
    text = response.content.strip()

    explanation = ""
    fixed_code = content  # fallback to original

    if "UPDATED_FILE:" in text:
        parts = text.split("UPDATED_FILE:", 1)
        explanation_part = parts[0]
        file_part = parts[1]

        if "EXPLANATION:" in explanation_part:
            explanation = explanation_part.split("EXPLANATION:", 1)[1].strip()
        else:
            explanation = explanation_part.strip()

        if "```" in file_part:
            file_part = file_part.split("```", 1)[1]
            if "```" in file_part:
                file_part = file_part.split("```", 1)[0]

        fixed_code = file_part.strip()

    return fixed_code, explanation
