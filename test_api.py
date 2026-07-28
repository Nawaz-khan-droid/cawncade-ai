import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def print_res(name, res):
    print(f"--- {name} ---")
    print(f"Status: {res.status_code}")
    try:
        data = res.json()
        status = data.get("status") or data.get("verdictTitle") or data.get("output") or "UNKNOWN"
        print(f"Result: {str(status)[:150]}...")
    except:
        print("Failed to decode JSON")
    print("")

def run_tests():
    print("Testing ContextLens (Text)...")
    res = requests.post(f"{BASE_URL}/analysis/analyze", json={"input_text": "NASA is going to Mars in 2030", "input_type": "text"})
    print_res("ContextLens Text", res)

    print("Testing ContextLens (URL)...")
    res = requests.post(f"{BASE_URL}/analysis/analyze", json={"input_text": "https://www.theverge.com/2026/1/1/nasa-mars-mission", "input_type": "url"})
    print_res("ContextLens URL", res)
    
    print("Testing YouTube (Invalid)...")
    res = requests.post(f"{BASE_URL}/analysis/analyze", json={"input_text": "https://youtube.com/watch?v=invalid123", "input_type": "youtube"})
    print_res("YouTube Invalid", res)
    
    print("Testing YouTube (Valid)...")
    res = requests.post(f"{BASE_URL}/analysis/analyze", json={"input_text": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "input_type": "youtube"})
    print_res("YouTube Valid", res)

    print("Testing Agent Chat (Normal)...")
    res = requests.post(f"{BASE_URL}/chat", json={"message": "What is the capital of France?", "session_id": "test_1"})
    print_res("Agent Chat (LLM)", res)

if __name__ == "__main__":
    run_tests()
