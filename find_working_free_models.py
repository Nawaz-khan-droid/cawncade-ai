import httpx
import json

print("Fetching active OpenRouter free models...")
try:
    res = httpx.get("https://openrouter.ai/api/v1/models", timeout=10.0)
    if res.status_code == 200:
        data = res.json()
        free_models = [m["id"] for m in data.get("data", []) if ":free" in m["id"] or m.get("pricing", {}).get("prompt") == "0"]
        print(f"Found {len(free_models)} free models on OpenRouter:")
        for m in free_models:
            print(f"  - {m}")
    else:
        print("Failed to fetch models:", res.status_code)
except Exception as e:
    print("Error:", e)

import os
from dotenv import load_dotenv

load_dotenv()
hf_token = os.getenv("HF_TOKEN", "")
headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}

# Test standard Hugging Face Serverless endpoint format: https://api-inference.huggingface.co/models/<model-id>
test_hf_models = [
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "meta-llama/Llama-3.2-3B-Instruct",
    "HuggingFaceH4/zephyr-7b-beta"
]

with httpx.Client(timeout=10.0) as client:
    for m in test_hf_models:
        url = f"https://api-inference.huggingface.co/models/{m}"
        payload = {"inputs": "Respond with OK", "parameters": {"max_new_tokens": 10}}
        res = client.post(url, headers=headers, json=payload)
        print(f"\nHF Model '{m}': Status {res.status_code}")
        print("Response:", res.text[:200])
