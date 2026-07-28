import sys
import json
from pprint import pprint

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, 'backend')
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("=================== TEST 1: GET /api/health ===================")
res1 = client.get("/api/health")
print("Status:", res1.status_code)
print("Response Raw JSON:")
print(json.dumps(res1.json(), indent=2))

print("\n=================== TEST 2: POST /api/v1/analysis/analyze (Text Claim) ===================")
payload2 = {"input_text": "Water boils at 100 degrees Celsius at sea level", "input_type": "text"}
res2 = client.post("/api/v1/analysis/analyze", json=payload2)
print("Status:", res2.status_code)
print("Response Raw JSON:")
print(json.dumps(res2.json(), indent=2))

print("\n=================== TEST 3: POST /api/v1/analysis/analyze (YouTube URL) ===================")
payload3 = {"input_text": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "input_type": "youtube"}
res3 = client.post("/api/v1/analysis/analyze", json=payload3)
print("Status:", res3.status_code)
print("Response Body:")
print(res3.text)

print("\n=================== TEST 4: POST /api/v1/auth/register ===================")
res4 = client.post("/api/v1/auth/register", json={"email": "testuser@example.com", "password": "securepassword123"})
print("Status:", res4.status_code)
print("Response Body:", res4.text)

print("\n=================== TEST 5: GET /api/v1/admin/sources ===================")
res5 = client.get("/api/v1/admin/sources")
print("Status:", res5.status_code)
print("Response Body:", res5.text)
