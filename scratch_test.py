import sys
import json
import urllib.request
import urllib.error

sys.path.insert(0, 'backend')
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("=== TEST 1: GET /api/health ===")
res1 = client.get("/api/health")
print(f"Status Code: {res1.status_code}")
print(f"Response Body: {res1.json()}")

print("\n=== TEST 2: POST /api/v1/analysis/analyze (Text) ===")
payload2 = {"input_text": "Water boils at 100 degrees Celsius", "input_type": "text"}
res2 = client.post("/api/v1/analysis/analyze", json=payload2)
print(f"Status Code: {res2.status_code}")
print(f"Response Keys: {list(res2.json().keys()) if res2.status_code == 200 else res2.text}")
if res2.status_code == 200:
    data = res2.json()
    print(f"Verdict: {data.get('verdict')}")
    print(f"Scores: {data.get('scores')}")
    print(f"Answer snippet: {data.get('answer')[:150]}")

print("\n=== TEST 3: POST /api/v1/analysis/analyze (YouTube URL) ===")
payload3 = {"input_text": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "input_type": "youtube"}
res3 = client.post("/api/v1/analysis/analyze", json=payload3)
print(f"Status Code: {res3.status_code}")
print(f"Response: {res3.text[:300]}")

print("\n=== TEST 4: POST /api/v1/auth/register (Testing /api/v1/auth/register vs /api/v1/auth/auth/register) ===")
res4_bad = client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "pass"})
print(f"/api/v1/auth/register Status Code: {res4_bad.status_code} (Expected 404 due to double prefix bug)")

res4_double = client.post("/api/v1/auth/auth/register", json={"email": "test@example.com", "password": "pass"})
print(f"/api/v1/auth/auth/register Status Code: {res4_double.status_code} (Actual registered endpoint due to prefix bug)")

