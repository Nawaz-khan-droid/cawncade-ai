"""
Admin API Routes.
Includes DB backup to Google Cloud Storage (uses single GOOGLE_API_KEY).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import TrustedSource
from app.utils.logger import log

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/sources")
async def list_sources(region: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(TrustedSource)
    if region:
        query = query.filter(TrustedSource.region == region)
    if category:
        query = query.filter(TrustedSource.category == category)
    sources = query.all()
    return {"sources": [{"id": s.id, "domain": s.domain, "source_name": s.source_name, "credibility_score": s.credibility_score, "region": s.region, "category": s.category, "is_active": s.is_active} for s in sources], "total": len(sources)}


@router.get("/system/health")
async def system_health():
    return {"service": "CAWNCADE AI", "version": "3.0.0", "status": "operational"}


@router.get("/system/stats")
async def system_stats(db: Session = Depends(get_db)):
    from app.db.models import AnalysisRequest, User
    return {"total_users": db.query(User).count(), "total_requests": db.query(AnalysisRequest).count(), "total_sources": db.query(TrustedSource).count()}


# ── GCS Backup Endpoints (uses single GOOGLE_API_KEY) ──

@router.post("/backup")
async def trigger_backup():
    """Manually trigger a SQLite DB backup to Google Cloud Storage."""
    from app.services.backup_service import backup_db_to_gcs
    result = await backup_db_to_gcs()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Backup failed"))
    return result


@router.get("/backup/list")
async def list_backups():
    """List existing backups in GCS."""
    from app.services.backup_service import list_backups as get_backups
    result = await get_backups()
    return result


@router.delete("/backup/cleanup")
async def cleanup_backups(keep_days: int = 7):
    """Delete backups older than keep_days days."""
    from app.services.backup_service import cleanup_old_backups
    result = await cleanup_old_backups(keep_days=keep_days)
    return result
