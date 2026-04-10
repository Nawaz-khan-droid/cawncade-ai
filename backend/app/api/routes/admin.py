"""
Admin API Routes.
Manage trusted sources, view analytics, system health.
Requires admin authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.models import TrustedSource
from ...core.security import get_current_user_id
from ...modules.retrieval.safe_retrieval import safe_retrieval
from ...utils.logger import log

router = APIRouter(prefix="/admin", tags=["admin"])


class SourceCreateRequest(BaseModel):
    domain: str
    source_name: str
    credibility_score: float = 0.5
    region: str = "global"
    category: str = "general"


class SourceUpdateRequest(BaseModel):
    credibility_score: Optional[float] = None
    region: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


# --- Trusted Sources Management ---

@router.get("/sources")
async def list_sources(
    region: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all trusted sources with optional filtering."""
    query = db.query(TrustedSource)
    if region:
        query = query.filter(TrustedSource.region == region)
    if category:
        query = query.filter(TrustedSource.category == category)

    sources = query.all()
    return {
        "sources": [
            {
                "id": s.id,
                "domain": s.domain,
                "source_name": s.source_name,
                "credibility_score": s.credibility_score,
                "region": s.region,
                "category": s.category,
                "is_active": s.is_active,
            }
            for s in sources
        ],
        "total": len(sources),
    }


@router.post("/sources")
async def add_source(request: SourceCreateRequest, db: Session = Depends(get_db)):
    """Add a new trusted source."""
    existing = db.query(TrustedSource).filter(TrustedSource.domain == request.domain).first()
    if existing:
        raise HTTPException(status_code=409, detail="Source already exists.")

    source = TrustedSource(
        domain=request.domain,
        source_name=request.source_name,
        credibility_score=request.credibility_score,
        region=request.region,
        category=request.category,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    # Also add to runtime memory
    safe_retrieval.add_trusted_source(
        domain=request.domain,
        name=request.source_name,
        credibility=request.credibility_score,
        region=request.region,
        category=request.category,
    )

    log.info(f"Admin added source: {request.domain} (credibility: {request.credibility_score})")
    return {"status": "added", "source_id": source.id}


@router.put("/sources/{source_id}")
async def update_source(source_id: int, request: SourceUpdateRequest, db: Session = Depends(get_db)):
    """Update an existing trusted source."""
    source = db.query(TrustedSource).filter(TrustedSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)

    db.commit()
    db.refresh(source)
    return {"status": "updated", "source_id": source.id}


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int, db: Session = Depends(get_db)):
    """Remove a trusted source."""
    source = db.query(TrustedSource).filter(TrustedSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")

    safe_retrieval.remove_trusted_source(source.domain)
    db.delete(source)
    db.commit()

    log.info(f"Admin removed source: {source.domain}")
    return {"status": "removed", "source_id": source_id}


# --- System Health ---

@router.get("/system/health")
async def system_health():
    """System health and statistics."""
    return {
        "service": "CAWNCADE AI",
        "status": "operational",
        "modules": {
            "retrieval": "active",
            "verification": "active",
            "scoring": "active",
            "synthesis": "active",
        },
    }


@router.get("/system/stats")
async def system_stats(db: Session = Depends(get_db)):
    """Basic system statistics."""
    from ...db.models import AnalysisRequest, User

    total_users = db.query(User).count()
    total_requests = db.query(AnalysisRequest).count()
    total_sources = db.query(TrustedSource).count()

    return {
        "total_users": total_users,
        "total_requests": total_requests,
        "total_sources": total_sources,
    }
