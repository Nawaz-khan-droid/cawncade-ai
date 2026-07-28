import sys
import json
import logging

sys.path.insert(0, 'backend')
from app.main import app
from fastapi.testclient import TestClient

# Configure logging to capture exact log stream
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

print("=================== EXECUTING FULL FALLBACK CHAIN TRACE ===================")
with TestClient(app) as client:
    payload = {
        "input_text": "NASA launches Europa Clipper spacecraft to study Jupiter moon Europa",
        "input_type": "text"
    }
    print("Endpoint Called: POST /api/v1/analysis/analyze")
    print(f"Payload: {json.dumps(payload)}")
    print("\n--- BEGIN BACKEND LOGS & TRANSITION TRACE ---")
    
    response = client.post("/api/v1/analysis/analyze", json=payload)
    
    print("--- END BACKEND LOGS ---")
    print(f"\nFinal HTTP Status: {response.status_code} OK")
    print("Final HTTP Response JSON:")
    data = response.json()
    print(json.dumps({
        "verdict": data.get("verdict"),
        "answer": data.get("answer"),
        "context_summary": data.get("context_summary"),
        "agent_deep_dive": data.get("agent_deep_dive", "")[:300] + "...",
        "scores": data.get("scores"),
        "system_metadata": data.get("system_metadata"),
        "metadata": data.get("metadata")
    }, indent=2))
