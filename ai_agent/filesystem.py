import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

from api_gateway.agent_state import (
    FILE_STRUCTURE_CACHE,
    FILE_REQUEST_CACHE,
    FILE_CONTENT_CACHE,
)

load_dotenv()

# ============================================================
# 🔒 LOCAL FILESYSTEM CONFIG (DEV / FALLBACK ONLY)
# ============================================================

PROJECT_ROOT = os.path.realpath(os.getenv("PROJECT_ROOT", "").strip() or ".")

DENY_DIR_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
}

DENY_FILE_NAMES = {
    ".env",
    ".env.local",
    "secrets.json",
    "secrets.yaml",
    "id_rsa",
    "id_rsa.pub",
}

DENY_FILE_EXTENSIONS = {
    ".pem",
    ".key",
    ".crt",
    ".p12",
    ".pfx",
}

ALLOW_FILE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".md",
}

# ============================================================
# 🔒 INTERNAL HELPERS (LOCAL MODE)
# ============================================================

def _is_path_under_root(abs_path: str) -> bool:
    root = os.path.realpath(PROJECT_ROOT)
    abs_path = os.path.realpath(abs_path)
    return os.path.commonpath([root, abs_path]) == root


def _is_sensitive_file(abs_path: str) -> bool:
    name = os.path.basename(abs_path)
    _, ext = os.path.splitext(name)

    return (
        name in DENY_FILE_NAMES
        or ext.lower() in DENY_FILE_EXTENSIONS
    )


def _is_allowed_file(abs_path: str) -> bool:
    if _is_sensitive_file(abs_path):
        return False
    _, ext = os.path.splitext(abs_path)
    return ext.lower() in ALLOW_FILE_EXTENSIONS


# ============================================================
# 🌐 FILE AGENT HELPERS (PRODUCTION MODE)
# ============================================================

def _use_file_agent(project: Optional[dict]) -> bool:
    return bool(project and project.get("file_agent_url"))


def _agent_headers(project: dict) -> Dict:
    # optional protection (future)
    return {
        "X-Project-Secret": project.get("project_secret", "")
    }


# ============================================================
# 📂 LIST PROJECT FILES
# ============================================================

def list_project_files(
    max_files: int = 200,
    project: Optional[dict] = None,
) -> List[Dict]:
    if not project:
        return []

    project_id = str(project["_id"])

    entry = FILE_STRUCTURE_CACHE.get(project_id)
    if not entry:
        return []

    files = entry.get("files", [])
    return files[:max_files]
# ============================================================
# 📄 READ PROJECT FILE CONTENT
# ============================================================
def read_project_file(
    relative_path: str,
    project: Optional[dict] = None,
) -> Optional[str]:

    if not project or not relative_path:
        return None

    project_id = str(project["_id"])

    # 1️⃣ REQUEST FILE FROM WATCHER
    FILE_REQUEST_CACHE[project_id] = {
        "path": relative_path,
        "status": "WAITING",
    }

    # 2️⃣ WAIT FOR WATCHER RESPONSE (POLL MEMORY)
    for _ in range(30):  # ~3 seconds
        entry = FILE_CONTENT_CACHE.get(project_id)
        if entry and entry.get("path") == relative_path:
            return entry.get("content")

    return None