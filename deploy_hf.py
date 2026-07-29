from huggingface_hub import HfApi
import os
import sys

def deploy():
    token = os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    api = HfApi(token=token)
    
    # 1. Get username
    user_info = api.whoami()
    username = user_info["name"]
    repo_id = f"{username}/cawncade-ai"
    
    print(f"User: {username}")
    print(f"Creating repository: {repo_id}...")
    
    # 2. Create repo (equivalent to huggingface-cli repo create)
    repo_url = api.create_repo(
        repo_id=repo_id, 
        repo_type="space", 
        space_sdk="docker", 
        exist_ok=True
    )
    print(f"Repo created/exists at: {repo_url}")
    
    # 3. Upload folder (equivalent to git init/add/commit/push)
    print("Uploading files... This may take a few minutes.")
    root_folder = os.path.dirname(os.path.abspath(__file__))
    
    api.upload_folder(
        folder_path=root_folder,
        repo_id=repo_id,
        repo_type="space",
        commit_message="Deploy: Decoupled Multi-Tier Fact Checker Core",
        ignore_patterns=[
            ".git", 
            "backend/venv", 
            "frontend/node_modules", 
            "db", 
            ".DS_Store", 
            "__pycache__", 
            "*.pyc",
            "frontend/dist" # We compile in Docker, but if we have it locally we can ignore it to save bandwidth
        ]
    )
    print("✅ Deployment successful!")

if __name__ == "__main__":
    deploy()
