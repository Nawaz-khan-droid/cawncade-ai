import os
import sys
import httpx

sys.path.insert(0, 'backend')
from app.config.settings import get_settings

settings = get_settings()

print("=" * 60)
print("  TESTING LLM PROVIDERS (OPENROUTER & HUGGINGFACE)")
print("=" * 60)

openrouter_key = settings.OPENROUTER_API_KEY
hf_token = settings.HUGGINGFACE_API_TOKEN or settings.HUGGINGFACEHUB_API_TOKEN

print(f"\n[1] OpenRouter API Key Present: {bool(openrouter_key)}")
if openrouter_key:
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "CAWNCADE-AI"
    }
    # Test model 1: meta-llama/llama-3.1-8b-instruct:free
    # Test model 2: google/gemini-2.0-flash-lite-001:free
    # Test model 3: deepseek/deepseek-r1:free
    test_models = [
        "meta-llama/llama-3.1-8b-instruct:free",
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "deepseek/deepseek-r1:free",
        "nvidia/nemotron-3-super-120b-a12b:free"
    ]
    
    with httpx.Client(timeout=15.0) as client:
        for model in test_models:
            print(f"\nTesting OpenRouter Model: '{model}'...")
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Respond with: OK"}],
                "max_tokens": 10
            }
            res = client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            print(f"Status Code: {res.status_code}")
            if res.status_code == 200:
                print("Response Body:", res.json()["choices"][0]["message"]["content"])
            else:
                print("Response Body:", res.text)

print(f"\n[2] Hugging Face Token Present: {bool(hf_token)}")
if hf_token:
    headers = {"Authorization": f"Bearer {hf_token}"}
    # Hugging Face Router URL: https://router.huggingface.co/hf-inference/v1/chat/completions
    # Hugging Face Serverless URL: https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct
    hf_endpoints = [
        ("HF Router Llama 3.1 8B", "https://router.huggingface.co/hf-inference/v1/chat/completions", {"model": "meta-llama/Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "Respond with: OK"}], "max_tokens": 10}),
        ("HF Serverless Qwen 2.5 7B", "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct/v1/chat/completions", {"model": "Qwen/Qwen2.5-72B-Instruct", "messages": [{"role": "user", "content": "Respond with: OK"}], "max_tokens": 10})
    ]
    
    with httpx.Client(timeout=15.0) as client:
        for label, url, payload in hf_endpoints:
            print(f"\nTesting Hugging Face: '{label}'...")
            res = client.post(url, headers=headers, json=payload)
            print(f"Status Code: {res.status_code}")
            if res.status_code == 200:
                try:
                    print("Response Body:", res.json())
                except Exception:
                    print("Raw Body:", res.text)
            else:
                print("Response Body:", res.text)
