#!/usr/bin/env python3
"""
CAWNCADE AI — Package Script
Creates a clean ZIP archive for easy transfer and deployment.
Strips development artifacts, includes only production-ready files.
Run: python package.py
"""

import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime


def should_include(path: Path) -> bool:
    """Determine if a file should be included in the package."""
    name = path.name

    # Exclude patterns
    exclude_dirs = {
        "__pycache__", "node_modules", ".git", ".idea", ".vscode",
        "dist", "build", ".venv", "venv", "env", ".pytest_cache",
        "htmlcov", "data", "models", ".mypy_cache",
    }
    exclude_files = {
        ".DS_Store", "Thumbs.db", "*.pyc", "*.pyo", "*.db",
        "*.sqlite", "*.sqlite3", "*.log", ".env",
    }
    exclude_extensions = {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".log"}

    # Check directory exclusion
    for part in path.parts:
        if part in exclude_dirs or part.startswith("."):
            return False

    # Check file exclusion
    if any(name == pattern or name.endswith(ext) for pattern in exclude_files for ext in exclude_extensions):
        return False

    return True


def create_package():
    root = Path(__file__).parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"CAWNCADE-AI-{timestamp}"
    output_path = root.parent / f"{package_name}.zip"

    print("=" * 60)
    print("  CAWNCADE AI — Packaging for Deployment")
    print("=" * 60)
    print(f"\n  Source: {root}")
    print(f"  Output: {output_path}")

    included_files = []
    total_size = 0

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for file_path in sorted(root.rglob("*")):
            if not file_path.is_file():
                continue

            rel_path = file_path.relative_to(root)

            if not should_include(rel_path):
                continue

            arcname = f"{package_name}/{rel_path}"
            zf.write(file_path, arcname)

            size = file_path.stat().st_size
            total_size += size
            included_files.append(str(rel_path))

            print(f"  + {rel_path} ({size:,} bytes)")

    zip_size = output_path.stat().st_size

    print(f"\n{'=' * 60}")
    print(f"  PACKAGE CREATED SUCCESSFULLY")
    print(f"{'=' * 60}")
    print(f"  Files included: {len(included_files)}")
    print(f"  Uncompressed:   {total_size / 1024:.1f} KB")
    print(f"  ZIP size:       {zip_size / 1024:.1f} KB")
    print(f"  Compression:    {(1 - zip_size / max(total_size, 1)) * 100:.1f}%")
    print(f"  Location:       {output_path}")
    print(f"\n  Deploy by:")
    print(f"    unzip {package_name}.zip")
    print(f"    cd {package_name}")
    print(f"    python bootstrap.py")
    print(f"    docker-compose up -d")
    print(f"{'=' * 60}")

    return output_path


if __name__ == "__main__":
    create_package()
