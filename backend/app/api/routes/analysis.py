"""
CAWNCADE AI v3.0 — API Routes for Analysis.
Supports: Text, URL, YouTube, and Image analysis.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.core.orchestrator import orchestrator
from app.core.resilience import (
    circuit_google_search, circuit_tavily, circuit_fact_check,
    circuit_safe_browsing, circuit_youtube, circuit_vision,
    circuit_newsapi, circuit_newsdata, circuit_gdelt, circuit_google_news, circuit_agent,
)
from app.core.cache import cache

router = APIRouter(tags=["analysis"])


class AnalyzeRequest(BaseModel):
    input_text: str = Field(..., min_length=1, max_length=5000, description="Text claim, news URL, or YouTube URL to analyze")
    input_type: str = Field(default="auto", description="auto | text | url | youtube")
    max_sources: int = Field(default=10, ge=1, le=20)


class ImageAnalyzeRequest(BaseModel):
    image_base64: str = Field(..., min_length=1, description="Base64-encoded image data")


class FeedbackRequest(BaseModel):
    request_id: Optional[str] = None
    user_rating: int = Field(default=0, ge=0, le=5)
    user_comment: str = Field(default="")
    was_helpful: Optional[bool] = None


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        # We pass the arguments explicitly. 
        # If your orchestrator's 'process' method calls 'tiered_search', 
        # make sure 'tiered_search' in orchestrator.py is updated to accept **kwargs.
        result = await orchestrator.process(
            input_text=request.input_text, 
            input_type=request.input_type, 
            max_sources=request.max_sources
        )
        return result
    except TypeError as e:
        # This catches the "unexpected keyword argument" error specifically
        if "max_sources" in str(e):
            # Fallback: Try calling without max_sources if the internal function isn't updated yet
            result = await orchestrator.process(
                input_text=request.input_text, 
                input_type=request.input_type
            )
            return result
        raise HTTPException(status_code=500, detail=f"Logic Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/image")
async def analyze_image_endpoint(request: ImageAnalyzeRequest):
    try:
        result = await orchestrator.process_image(image_base64=request.image_base64)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    return {"status": "received", "message": "Thank you for your feedback!"}


@router.get("/health")
async def health_check():
    circuits = {
        "google_search": circuit_google_search.status(), "tavily": circuit_tavily.status(),
        "fact_check": circuit_fact_check.status(), "safe_browsing": circuit_safe_browsing.status(),
        "youtube": circuit_youtube.status(), "vision": circuit_vision.status(),
        "newsapi": circuit_newsapi.status(), "newsdata": circuit_newsdata.status(),
        "gdelt": circuit_gdelt.status(), "google_news": circuit_google_news.status(),
        "llm_agent": circuit_agent.status(),
    }
    return {"status": "healthy", "service": "CAWNCADE AI", "version": "3.0.0", "services": circuits, "cache": cache.stats()}
