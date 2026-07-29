import os
import json
import base64
import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = Path(__file__).parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

REPO_OWNER = "Nawaz-khan-droid"
REPO_NAME = "cawncade-ai"
BRANCH = "main"

# Read PAT token strictly from environment variable
PAT_TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_PAT") or os.getenv("GITHUB_PAT")

if not PAT_TOKEN:
    print("Error: GITHUB_TOKEN is not set in environment or backend/.env file.")
    sys.exit(1)

API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
HEADERS = {
    "Authorization": f"Bearer {PAT_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "CawncadeAI-Pusher"
}

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".pytest_cache", "__pycache__",
    "brain", ".system_generated", "dist", "build"
}

IGNORE_FILES = {
    "push_to_github.py", "push_log.txt", ".env", "backend/.env", "db/viral_claims_dictionary.json"
}

def is_ignored(path: Path, root_path: Path) -> bool:
    rel = path.relative_to(root_path)
    parts = rel.parts
    for p in parts:
        if p in IGNORE_DIRS or p.startswith(".git"):
            return True
    if rel.as_posix() in IGNORE_FILES:
        return True
    return False

def push_repository():
    sys.stdout.reconfigure(line_buffering=True)
    root_path = Path(__file__).parent.resolve()
    print(f"Uploading files from {root_path} to GitHub repo {REPO_OWNER}/{REPO_NAME}...", flush=True)

    with httpx.Client(headers=HEADERS, timeout=60.0) as client:
        # 1. Get branch ref
        ref_resp = client.get(f"{API_BASE}/git/ref/heads/{BRANCH}")
        parent_sha = None
        base_tree_sha = None

        if ref_resp.status_code == 200:
            parent_sha = ref_resp.json()["object"]["sha"]
            commit_resp = client.get(f"{API_BASE}/git/commits/{parent_sha}")
            if commit_resp.status_code == 200:
                base_tree_sha = commit_resp.json()["tree"]["sha"]

        tree_items = []

        # 2. Collect files and create blobs
        all_files = [p for p in root_path.rglob("*") if p.is_file() and not is_ignored(p, root_path)]
        print(f"Found {len(all_files)} project files to commit.", flush=True)

        for i, file_path in enumerate(all_files):
            rel_path = file_path.relative_to(root_path).as_posix()
            try:
                content_bytes = file_path.read_bytes()
                mode = "100755" if file_path.suffix in [".sh", ".bat", ".cmd", ".exe"] else "100644"

                try:
                    text_content = content_bytes.decode('utf-8')
                    blob_payload = {"content": text_content, "encoding": "utf-8"}
                except UnicodeDecodeError:
                    blob_payload = {"content": base64.b64encode(content_bytes).decode('ascii'), "encoding": "base64"}

                blob_resp = client.post(f"{API_BASE}/git/blobs", json=blob_payload)
                if blob_resp.status_code == 201:
                    sha = blob_resp.json()["sha"]
                    tree_items.append({
                        "path": rel_path,
                        "mode": mode,
                        "type": "blob",
                        "sha": sha
                    })
                    print(f"[{i+1}/{len(all_files)}] Prepared: {rel_path}", flush=True)
                else:
                    print(f"Failed to create blob for {rel_path}: {blob_resp.status_code} {blob_resp.text}", flush=True)
            except Exception as e:
                print(f"Error processing {rel_path}: {e}", flush=True)

        if not tree_items:
            print("No items to commit.", flush=True)
            return

        # 3. Post tree
        tree_payload = {"tree": tree_items}
        if base_tree_sha:
            tree_payload["base_tree"] = base_tree_sha

        tree_resp = client.post(f"{API_BASE}/git/trees", json=tree_payload)
        if tree_resp.status_code != 201:
            print(f"Failed to create tree: {tree_resp.status_code} {tree_resp.text}", flush=True)
            return

        new_tree_sha = tree_resp.json()["sha"]
        print(f"Created Git Tree SHA: {new_tree_sha}", flush=True)

        # 4. Post commit
        commit_msg = "v5.0 Production Ready: Publisher Unwrapping & Deterministic Verdict Engine"
        commit_payload = {
            "message": commit_msg,
            "tree": new_tree_sha,
            "parents": [parent_sha] if parent_sha else []
        }

        new_commit_resp = client.post(f"{API_BASE}/git/commits", json=commit_payload)
        if new_commit_resp.status_code != 201:
            print(f"Failed to create commit: {new_commit_resp.status_code} {new_commit_resp.text}", flush=True)
            return

        new_commit_sha = new_commit_resp.json()["sha"]
        print(f"Created Commit SHA: {new_commit_sha}", flush=True)

        # 5. Update ref
        if parent_sha:
            ref_payload = {"sha": new_commit_sha, "force": True}
            update_resp = client.patch(f"{API_BASE}/git/refs/heads/{BRANCH}", json=ref_payload)
        else:
            ref_payload = {"ref": f"refs/heads/{BRANCH}", "sha": new_commit_sha}
            update_resp = client.post(f"{API_BASE}/git/refs", json=ref_payload)

        if update_resp.status_code in (200, 201):
            print(f"\n[SUCCESS] Successfully pushed all files to GitHub repository {REPO_OWNER}/{REPO_NAME} on branch '{BRANCH}'!", flush=True)
            print(f"Commit SHA: {new_commit_sha}", flush=True)
        else:
            print(f"Failed to update ref: {update_resp.status_code} {update_resp.text}", flush=True)

if __name__ == "__main__":
    push_repository()
