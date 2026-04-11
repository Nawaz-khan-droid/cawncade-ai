"""
Backup Service — SQLite DB to Google Cloud Storage.
Uses the SAME GOOGLE_API_KEY as CSE, Fact Check, Safe Browsing, and YouTube.
Google Cloud Storage JSON API for simple async DB backup.

How it works:
  1. Reads the local SQLite file at /data/cawncade.db
  2. Uploads it to GCS as a timestamped backup
  3. Keeps last 7 daily backups (auto-cleanup)

Requirements:
  - GOOGLE_API_KEY: Must have "Google Cloud Storage JSON API" enabled
  - GCS_BUCKET_NAME: Set as HF Variable or Secret
  - GCS_BACKUP_ENABLED: Toggle on/off

Note: On HF Spaces free tier, GCS upload happens in-process (no background workers).
      The backup runs synchronously but only when explicitly triggered via /api/v1/admin/backup.
"""
import os
import asyncio
import httpx
from datetime import datetime, timezone
from app.config.settings import get_settings
from app.core.cache import cache
from app.utils.logger import log

settings = get_settings()


async def backup_db_to_gcs() -> dict:
    """
    Upload the SQLite database to Google Cloud Storage.
    Uses Google Cloud Storage JSON API with the shared GOOGLE_API_KEY.
    """
    if not settings.GCS_BACKUP_ENABLED:
        return {"success": False, "error": "GCS backup is disabled (GCS_BACKUP_ENABLED=false)"}

    if not settings.GOOGLE_API_KEY:
        return {"success": False, "error": "GOOGLE_API_KEY not configured"}

    if not settings.GCS_BUCKET_NAME:
        return {"success": False, "error": "GCS_BUCKET_NAME not configured"}

    # Determine DB path
    db_url = settings.DATABASE_URL
    db_path = db_url.split("///")[-1] if "sqlite" in db_url else "/data/cawncade.db"

    if not os.path.exists(db_path):
        return {"success": False, "error": f"Database file not found at {db_path}"}

    # Read DB file
    try:
        with open(db_path, "rb") as f:
            db_data = f.read()
    except Exception as e:
        return {"success": False, "error": f"Failed to read database: {e}"}

    file_size_mb = len(db_data) / (1024 * 1024)
    if file_size_mb > 50:
        return {"success": False, "error": f"Database too large for GCS upload ({file_size_mb:.1f}MB > 50MB limit)"}

    # Generate backup filename with timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")
    object_name = f"cawncade_backups/cawncade_{timestamp}.db"

    # GCS JSON API — Simple upload with API key auth (NOT OAuth Bearer)
    # Uses ?key= query parameter since GOOGLE_API_KEY is an API key, not an OAuth token
    upload_url = (
        f"https://storage.googleapis.com/upload/storage/v1/b/{settings.GCS_BUCKET_NAME}"
        f"/o?uploadType=media&name={object_name}&key={settings.GOOGLE_API_KEY}"
    )
    headers = {
        "Content-Type": "application/x-sqlite3",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(upload_url, content=db_data, headers=headers)

            if resp.status_code == 401:
                return {"success": False, "error": "Invalid API key — ensure GCS JSON API is enabled in Google Cloud Console"}
            if resp.status_code == 403:
                return {"success": False, "error": "Permission denied — GCS JSON API may need OAuth2 for write ops. Consider creating a service account."}
            if resp.status_code == 404:
                return {"success": False, "error": f"Bucket '{settings.GCS_BUCKET_NAME}' not found"}
            resp.raise_for_status()
            result = resp.json()

        log.info(f"[GCS Backup] Uploaded {object_name} ({file_size_mb:.2f} MB)")
        return {
            "success": True,
            "bucket": settings.GCS_BUCKET_NAME,
            "object_name": object_name,
            "size_mb": round(file_size_mb, 2),
            "timestamp": timestamp,
            "self_link": result.get("selfLink", ""),
        }

    except httpx.TimeoutException:
        return {"success": False, "error": "Upload timed out (60s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def list_backups() -> dict:
    """List existing backups in GCS bucket."""
    if not settings.GCS_BACKUP_ENABLED or not settings.GOOGLE_API_KEY or not settings.GCS_BUCKET_NAME:
        return {"success": False, "error": "GCS backup not configured", "backups": []}

    url = (
        f"https://storage.googleapis.com/storage/v1/b/{settings.GCS_BUCKET_NAME}"
        f"/o?prefix=cawncade_backups/&maxResults=10&key={settings.GOOGLE_API_KEY}"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            result = resp.json()

        backups = []
        for item in result.get("items", []):
            backups.append({
                "name": item.get("name", ""),
                "size_mb": round(int(item.get("size", 0)) / (1024 * 1024), 2),
                "updated": item.get("updated", ""),
                "self_link": item.get("selfLink", ""),
            })

        return {"success": True, "bucket": settings.GCS_BUCKET_NAME, "backups": backups}

    except Exception as e:
        return {"success": False, "error": str(e), "backups": []}


async def cleanup_old_backups(keep_days: int = 7) -> dict:
    """Delete backups older than keep_days."""
    if not settings.GCS_BACKUP_ENABLED or not settings.GOOGLE_API_KEY or not settings.GCS_BUCKET_NAME:
        return {"success": False, "error": "GCS backup not configured"}

    list_result = await list_backups()
    if not list_result.get("success"):
        return list_result

    cutoff = datetime.now(timezone.utc).timestamp() - (keep_days * 86400)
    deleted = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        for backup in list_result.get("backups", []):
            updated_str = backup.get("updated", "")
            if not updated_str:
                continue
            try:
                from datetime import datetime as dt
                updated_dt = dt.fromisoformat(updated_str.replace("Z", "+00:00"))
                if updated_dt.timestamp() < cutoff:
                    # Delete this backup (API key auth via query param)
                    encoded_name = backup["name"].replace("/", "%2F")
                    del_url = (
                        f"https://storage.googleapis.com/storage/v1/b/{settings.GCS_BUCKET_NAME}"
                        f"/o/{encoded_name}?key={settings.GOOGLE_API_KEY}"
                    )
                    resp = await client.delete(del_url)
                    if resp.status_code == 204:
                        deleted.append(backup["name"])
                        log.info(f"[GCS Backup] Deleted old backup: {backup['name']}")
            except Exception as e:
                log.warning(f"[GCS Backup] Failed to process backup {backup['name']}: {e}")

    return {"success": True, "deleted_count": len(deleted), "deleted": deleted}
