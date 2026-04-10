"""
Analysis API Routes.
Main endpoint for content analysis / verification.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from ...core.orchestrator import orchestrator
from ...core.rate_limiter import rate_limiter
from ...core.security import sanitize_input
from ...utils.logger import log

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    input_text: str = Field(..., min_length=3, max_length=5000, description="Text, claim, or URL to analyze")
    input_type: str = Field(default="text", description="Type of input: text | url")
    max_sources: int = Field(default=8, ge=1, le=15, description="Max sources to retrieve")


class AnalysisResponse(BaseModel):
    answer: str
    context_summary: str
    agreements: list
    conflicts: list
    sources_cited: list
    confidence: float
    scores: dict
    compute_time_ms: int
    status: str
    metadata: Optional[dict] = None


class FeedbackRequest(BaseModel):
    request_id: int
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    user_comment: Optional[str] = None
    was_helpful: Optional[bool] = None


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_content(request: AnalysisRequest):
    """
    Main analysis endpoint.
    Accepts text or URL input, returns full verification analysis.
    """
    # Rate limit check
    rate_limiter.check_or_raise("analyze")

    # Sanitize input
    sanitized_text = sanitize_input(request.input_text)

    if not sanitized_text:
        raise HTTPException(status_code=400, detail="Input text is empty after sanitization.")

    log.info(f"Analysis request: type={request.input_type}, length={len(sanitized_text)}")

    try:
        result = await orchestrator.process(
            input_text=sanitized_text,
            input_type=request.input_type,
            max_sources=request.max_sources,
        )
        return AnalysisResponse(**result)

    except Exception as e:
        log.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "CAWNCADE AI Analysis Engine"}


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback for an analysis result.
    Used for ML lifecycle: collect labeled data for future model improvement.
    """
    # TODO: Save to database
    log.info(f"Feedback received: request_id={request.request_id}, rating={request.user_rating}")
    return {"status": "recorded", "message": "Thank you for your feedback."}
