#!/usr/bin/env python3
"""
CAWNCADE AI — Bootstrap Script
Cross-platform setup for development and deployment.
Run: python bootstrap.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run(cmd, cwd=None):
    """Run a shell command and print output."""
    print(f"\n[>] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(
        cmd, shell=isinstance(cmd, str), cwd=cwd,
        capture_output=False, text=True
    )
    if result.returncode != 0:
        print(f"[!] Command failed with code {result.returncode}")
    return result.returncode


def main():
    root = Path(__file__).parent
    print("=" * 60)
    print("  CAWNCADE AI — Bootstrap Setup")
    print("  Context Aware Watch News Confirmation Authenticity Detection Engine")
    print("=" * 60)

    # Step 1: Backend setup
    print("\n[1/4] Setting up backend...")
    backend_dir = root / "backend"

    env_file = backend_dir / ".env"
    env_example = backend_dir / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("  Created .env from .env.example")
        print("  ⚠  EDIT backend/.env and add your HUGGINGFACE_API_TOKEN")

    # Check Python version
    py_version = sys.version_info
    print(f"  Python {py_version.major}.{py_version.minor}.{py_version.micro}")

    # Install backend dependencies
    req_file = backend_dir / "requirements.txt"
    if req_file.exists():
        print("  Installing Python dependencies...")
        run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], cwd=backend_dir)

    # Step 2: Frontend setup
    print("\n[2/4] Setting up frontend...")
    frontend_dir = root / "frontend"

    npm = "npm"
    if shutil.which("npm") is None:
        npm = "yarn" if shutil.which("yarn") else None
        if npm is None:
            print("  ⚠  Neither npm nor yarn found. Skipping frontend setup.")
            print("  Install Node.js from https://nodejs.org/")
        else:
            print(f"  Using {npm}")

    if npm:
        run([npm, "install"], cwd=frontend_dir)

    # Step 3: Database init
    print("\n[3/4] Initializing database...")
    run([sys.executable, "-c", "from app.db.session import init_db; init_db(); print('Database created!')"], cwd=backend_dir)

    # Step 4: Summary
    print("\n[4/4] Setup complete!")
    print("\n" + "=" * 60)
    print("  NEXT STEPS:")
    print("=" * 60)
    print()
    print("  1. Edit backend/.env — set your HUGGINGFACE_API_TOKEN")
    print()
    print("  2. Start backend:")
    print("     cd backend && uvicorn app.main:app --reload --port 8000")
    print()
    print("  3. Start frontend (new terminal):")
    print(f"     cd frontend && {npm} run dev")
    print()
    print("  4. Open http://localhost:5173")
    print()
    print("  OR use Docker:")
    print("     docker-compose up -d")
    print()
    print("  API docs: http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    main()
