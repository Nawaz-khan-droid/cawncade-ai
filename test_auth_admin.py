import sys
import json

sys.path.insert(0, 'backend')
from app.main import app
from fastapi.testclient import TestClient

with TestClient(app) as client:
    print("=================== TEST 4: POST /api/v1/auth/register ===================")
    res4 = client.post("/api/v1/auth/register", json={"email": "newuser@example.com", "password": "securepassword123"})
    print("Status:", res4.status_code)
    print("Response JSON:", res4.json())

    print("\n=================== TEST 5: GET /api/v1/admin/sources ===================")
    res5 = client.get("/api/v1/admin/sources")
    print("Status:", res5.status_code)
    print("Response JSON:", res5.json())
