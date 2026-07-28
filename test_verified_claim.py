import sys
import json

sys.path.insert(0, 'backend')
from app.main import app
from fastapi.testclient import TestClient

with TestClient(app) as client:
    print("=================== TEST: NASA Europa Clipper Mission ===================")
    payload = {"input_text": "NASA launches Europa Clipper spacecraft to study Jupiter moon Europa", "input_type": "text"}
    res = client.post("/api/v1/analysis/analyze", json=payload)
    print("Status Code:", res.status_code)
    data = res.json()
    print("Verdict Label:", data.get("scores", {}).get("confidence_label"))
    print("Confidence Score:", data.get("confidence"))
    print("Retrieved Sources Count:", len(data.get("sources_cited", [])))
    print("Top Sources Cited:")
    for s in data.get("sources_cited", [])[:3]:
        print(f"  - [{s.get('trust_tier')}] {s.get('title')} ({s.get('source_name')}) -> {s.get('url')}")
