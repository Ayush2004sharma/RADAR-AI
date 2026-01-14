import requests

def list_files(agent_url: str):
    r = requests.get(f"{agent_url}/files", timeout=5)
    r.raise_for_status()
    return r.json()["files"]

def read_file(agent_url: str, path: str):
    r = requests.post(
        f"{agent_url}/file",
        json={"path": path},
        timeout=5
    )
    r.raise_for_status()
    return r.json()["content"]
