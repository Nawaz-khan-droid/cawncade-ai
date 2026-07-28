import urllib.request
import json
import sys

def test_url(name, url, method="GET", payload=None, headers=None):
    headers = headers or {}
    print(f"\n=================== {name} ===================")
    print(f"Request: {method} {url}")
    if payload:
        print(f"Payload: {json.dumps(payload)}")
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        data = None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            body = response.read().decode('utf-8', errors='replace')
            print(f"HTTP Status: {status} OK")
            try:
                parsed = json.loads(body)
                print("Response JSON:")
                print(json.dumps(parsed, indent=2)[:500] + "...")
                return status, parsed
            except Exception:
                print(f"Response Raw (First 200 chars): {body[:200]}...")
                return status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"HTTP Error: {e.code} - {body}")
        return e.code, body
    except Exception as e:
        print(f"Connection Exception: {e}")
        return 500, str(e)

if __name__ == "__main__":
    # 1. Test Vite Dev Server HTML
    s1, r1 = test_url("1. Vite Frontend SPA Entry", "http://localhost:5173/")
    assert s1 == 200, "Vite Frontend failed to respond"

    # 2. Test Backend Health Endpoint
    s2, r2 = test_url("2. FastAPI Health Check", "http://localhost:8000/api/health")
    assert s2 == 200, "FastAPI Health check failed"

    # 3. Test End-to-End Analysis API
    s3, r3 = test_url(
        "3. Text Analysis Endpoint",
        "http://localhost:8000/api/v1/analysis/analyze",
        method="POST",
        payload={"input_text": "NASA launches Europa Clipper spacecraft to study Jupiter moon Europa", "input_type": "text"}
    )
    assert s3 == 200, "Analysis API failed"

    # 4. Test User Auth Registration Flow
    email = "e2e_user@example.com"
    s4, r4 = test_url(
        "4. Auth Register Endpoint",
        "http://localhost:8000/api/v1/auth/register",
        method="POST",
        payload={"email": email, "password": "password123"}
    )
    assert s4 == 200 or "registered" in str(r4).lower() or "already" in str(r4).lower(), "Auth registration failed"

    # 5. Test Admin Panel Listing Endpoint
    s5, r5 = test_url("5. Admin Sources Endpoint", "http://localhost:8000/api/v1/admin/sources")
    assert s5 == 200, "Admin sources API failed"

    print("\n" + "="*60)
    print("  ALL END-TO-END FRONTEND & BACKEND AUDIT CHECKS PASSED")
    print("="*60)
