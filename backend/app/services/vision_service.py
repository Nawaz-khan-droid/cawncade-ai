"""
Visual Lens Service v3.0 — Image Verification.
Uses HuggingFace Inference API for ViT/Siglip2 deepfake detection.
No local model loading — runs on HF servers to prevent OOM on free tier.
"""

import httpx
from app.config.settings import get_settings
from app.core.cache import cache
from app.core.resilience import circuit_vision
from app.utils.logger import log

settings = get_settings()


async def analyze_image(image_data: str, is_base64: bool = True) -> dict:
    if not settings.HUGGINGFACE_API_TOKEN:
        return {"label": "unavailable", "confidence": 0.0, "all_predictions": [], "model_used": settings.VISION_MODEL, "error": "HUGGINGFACE_API_TOKEN not configured"}

    cache_key = f"vision:{image_data[:100]}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    api_url = f"{settings.HUGGINGFACE_INFERENCE_URL}{settings.VISION_MODEL}"
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}", "Content-Type": "application/json"}
    payload = {"inputs": image_data}

    async def _call():
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(api_url, headers=headers, json=payload)
            if resp.status_code == 503:
                return {"error": "model_loading", "status_code": 503}
            if resp.status_code == 429:
                return {"error": "rate_limited", "status_code": 429}
            resp.raise_for_status()
            return resp.json()

    result = await circuit_vision.call(_call)
    if result is None or (isinstance(result, dict) and "error" in result):
        return {"label": "error", "confidence": 0.0, "all_predictions": [], "model_used": settings.VISION_MODEL,
                "error": result.get("error", "Analysis failed") if result else "Service unavailable"}

    predictions = result if isinstance(result, list) else result.get("predictions", [result])

    if not predictions:
        return {"label": "unknown", "confidence": 0.0, "all_predictions": [], "model_used": settings.VISION_MODEL}

    top = predictions[0] if isinstance(predictions[0], dict) else predictions[0]
    label = top.get("label", "unknown") if isinstance(top, dict) else str(top[0])
    confidence = top.get("score", 0.0) if isinstance(top, dict) else float(top[1])

    label_lower = label.lower()
    if any(kw in label_lower for kw in ["real", "authentic", "genuine"]):
        normalized = "REAL"
    elif any(kw in label_lower for kw in ["deepfake", "fake", "ai-generated", "synthetic"]):
        normalized = "AI-GENERATED/DEEPFAKE"
    elif any(kw in label_lower for kw in ["morphed", "manipulated", "edited"]):
        normalized = "MORPHED/MANIPULATED"
    else:
        normalized = label.upper()

    output = {"label": normalized, "confidence": round(confidence, 4), "all_predictions": predictions, "model_used": settings.VISION_MODEL}
    cache.set(cache_key, output, ttl=86400)
    log.info(f"[VisualLens] Result: {normalized} ({confidence:.2%}) using {settings.VISION_MODEL}")
    return output


async def extract_image_metadata(image_data: str) -> dict:
    try:
        if image_data.startswith("data:image/"):
            parts = image_data.split(";base64,")
            mime = parts[0].replace("data:", "") if len(parts) > 1 else "unknown"
            b64_data = parts[1] if len(parts) > 1 else image_data
        else:
            mime = "image/jpeg"
            b64_data = image_data
        byte_size = (len(b64_data) * 3) // 4
        return {"format": mime, "approximate_size_kb": round(byte_size / 1024, 1), "is_base64": True}
    except Exception as e:
        return {"format": "unknown", "error": str(e)}
