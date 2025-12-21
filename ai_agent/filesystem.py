import os
from typing import List, Dict, Optional
from dotenv import load_dotenv


load_dotenv()

# Absolute root of the project RADAR-AI is allowed to read.
# Example in .env:
# PROJECT_ROOT=/home/user/projects/ecommerce
PROJECT_ROOT = os.path.realpath(os.getenv("PROJECT_ROOT", "").strip() or ".")

# Directories that should never be traversed (even if under PROJECT_ROOT)
DENY_DIR_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
}

# File basenames that are always forbidden
DENY_FILE_NAMES = {
    ".env",
    ".env.local",
    "secrets.json",
    "secrets.yaml",
    "id_rsa",
    "id_rsa.pub",
}

# File extensions that are considered sensitive and never read
DENY_FILE_EXTENSIONS = {
    ".pem",
    ".key",
    ".crt",
    ".p12",
    ".pfx",
}

# File extensions that are allowed for reading (code/text)
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


def _is_path_under_root(abs_path: str) -> bool:
    """
    Ensure abs_path is inside PROJECT_ROOT (prevents ../ traversal).
    """
    root = PROJECT_ROOT
    # Normalize both paths
    root = os.path.realpath(root)
    abs_path = os.path.realpath(abs_path)
    return os.path.commonpath([root, abs_path]) == root


def _is_sensitive_file(abs_path: str) -> bool:
    """
    Check if a file is considered sensitive and must never be read.
    """
    name = os.path.basename(abs_path)
    _, ext = os.path.splitext(name)

    if name in DENY_FILE_NAMES:
        return True

    if ext.lower() in DENY_FILE_EXTENSIONS:
        return True

    return False


def _is_allowed_file(abs_path: str) -> bool:
    """
    Check if a file extension is within the allowed text/code types.
    """
    if _is_sensitive_file(abs_path):
        return False

    _, ext = os.path.splitext(abs_path)
    return ext.lower() in ALLOW_FILE_EXTENSIONS


def list_project_files(max_files: int = 200) -> List[Dict]:
    """
    List up to max_files project files under PROJECT_ROOT
    that are safe to show as options to the user.

    Returns a list of dicts:
    [
        {"path": "src/auth/routes.py", "size": 1234},
        ...
    ]
    """
    files: List[Dict] = []

    if not os.path.isdir(PROJECT_ROOT):
        return files

    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        # Filter out denied directories in-place
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

            files.append(
                {
                    "path": rel_path.replace("\\", "/"),
                    "size": int(size),
                }
            )

            if len(files) >= max_files:
                return files

    return files


def read_project_file(relative_path: str) -> Optional[str]:
    """
    Safely read a file under PROJECT_ROOT.

    - Only reads files inside PROJECT_ROOT.
    - Rejects sensitive names/extensions.
    - Only allows text/code files as per ALLOW_FILE_EXTENSIONS.
    - Returns file content as UTF-8 text, or None if not allowed / missing.
    """
    if not relative_path:
        return None

    # Normalize and build absolute path
    rel = relative_path.lstrip("/").replace("\\", "/")
    abs_path = os.path.realpath(os.path.join(PROJECT_ROOT, rel))

    # Ensure path stays inside PROJECT_ROOT
    if not _is_path_under_root(abs_path):
        return None

    # Ensure this is a regular file and not sensitive
    if not os.path.isfile(abs_path):
        return None

    if not _is_allowed_file(abs_path):
        return None

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        # In production, you could log this internally
        return None
