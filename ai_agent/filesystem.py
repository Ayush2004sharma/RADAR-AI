import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

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
    """
    Returns:
    [
      {"path": "server.js", "size": 1329},
      ...
    ]
    """

    # 🌐 PRODUCTION: CALL USER FILE AGENT
    if _use_file_agent(project):
        try:
            res = requests.get(
                f"{project['file_agent_url']}/files",
                headers=_agent_headers(project),
                timeout=5,
            )
            res.raise_for_status()

            files = res.json().get("files", [])
            return files[:max_files]

        except Exception as e:
            print("⚠️ File agent error:", e)
            return []

    # 🖥️ LOCAL FALLBACK (DEV ONLY)
    files: List[Dict] = []

    if not os.path.isdir(PROJECT_ROOT):
        return files

    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        dirnames[:] = [d for d in dirnames if d not in DENY_DIR_NAMES]

        for filename in filenames:
            abs_path = os.path.join(dirpath, filename)

            if not _is_path_under_root(abs_path):
                continue
            if not _is_allowed_file(abs_path):
                continue

            rel_path = os.path.relpath(abs_path, PROJECT_ROOT)
            try:
                size = os.path.getsize(abs_path)
            except OSError:
                size = 0

            files.append({
                "path": rel_path.replace("\\", "/"),
                "size": int(size),
            })

            if len(files) >= max_files:
                return files

    return files


# ============================================================
# 📄 READ PROJECT FILE CONTENT
# ============================================================

def read_project_file(
    relative_path: str,
    project: Optional[dict] = None,
) -> Optional[str]:

    if not relative_path:
        return None

    # 🌐 PRODUCTION: CALL USER FILE AGENT
    if _use_file_agent(project):
        try:
            res = requests.post(
                f"{project['file_agent_url']}/file",
                headers=_agent_headers(project),
                json={"path": relative_path},
                timeout=5,
            )
            res.raise_for_status()
            return res.json().get("content")
        except Exception as e:
            print("⚠️ File read error:", e)
            return None

    # 🖥️ LOCAL FALLBACK (DEV ONLY)
    rel = relative_path.lstrip("/").replace("\\", "/")
    abs_path = os.path.realpath(os.path.join(PROJECT_ROOT, rel))

    if not _is_path_under_root(abs_path):
        return None
    if not os.path.isfile(abs_path):
        return None
    if not _is_allowed_file(abs_path):
        return None

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None
