import asyncio
import json
import time
import os
from datetime import datetime

# Assuming the backend is running locally, we hit the API.
# If not, we can import orchestrator directly.
import httpx

EVALUATION_DATASET = [
    {
        "claim": "Isaac Newton discovered gravity after an apple fell on his head.",
        "expected_verdict": "FALSE_DEBUNKED"
    },
    {
        "claim": "Joe Biden won the 2020 US Presidential Election.",
        "expected_verdict": "VERIFIED_TRUE"
    },
    {
        "claim": "The Great Wall of China is visible from the Moon with the naked eye.",
        "expected_verdict": "FALSE_DEBUNKED"
    },
    {
        "claim": "NASA discovered active microbial bacteria on Mars in 2024.",
        "expected_verdict": "FALSE_DEBUNKED"
    },
    {
        "claim": "Water boils at 100 degrees Celsius at standard atmospheric pressure.",
        "expected_verdict": "VERIFIED_TRUE"
    }
]

API_URL = "http://localhost:8000/api/v1/analysis/analyze"

async def run_evaluation():
    print(f"Starting End-to-End System Evaluation at {datetime.now().isoformat()}")
    results = []
    correct_count = 0
    total = len(EVALUATION_DATASET)
    
    # Needs to be run while the server is active!
    async with httpx.AsyncClient(timeout=60.0) as client:
        for idx, test_case in enumerate(EVALUATION_DATASET):
            print(f"[{idx+1}/{total}] Evaluating: {test_case['claim']}")
            start_time = time.time()
            try:
                response = await client.post(
                    API_URL, 
                    json={"input_text": test_case["claim"], "input_type": "text"}
                )
                
                if response.status_code == 429:
                    print("Rate limit hit! Sleeping for 15 seconds...")
                    await asyncio.sleep(15)
                    response = await client.post(
                        API_URL, 
                        json={"input_text": test_case["claim"], "input_type": "text"}
                    )

                if response.status_code == 200:
                    data = response.json()
                    verdict = data.get("synthesis", {}).get("verdict_code", data.get("verdict_code", "UNKNOWN"))
                    latency = time.time() - start_time
                    
                    is_correct = (verdict == test_case["expected_verdict"])
                    if is_correct: correct_count += 1
                    
                    results.append({
                        "claim": test_case["claim"],
                        "expected": test_case["expected_verdict"],
                        "actual": verdict,
                        "latency_seconds": round(latency, 2),
                        "success": is_correct,
                        "explanation": data.get("synthesis", {}).get("layer3_deep_dive", data.get("layer2_verification", ""))[:200] + "..."
                    })
                    print(f"  -> Result: {verdict} (Expected: {test_case['expected_verdict']}) - Success: {is_correct}")
                else:
                    print(f"  -> API Error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"  -> Exception: {e}")
            
            # Sleep to avoid rate limiting
            await asyncio.sleep(12)
            
    accuracy = (correct_count / total) * 100
    print(f"\nEvaluation Complete! Accuracy: {accuracy}%")
    
    report_path = os.path.join("..", "04_EVIDENCE", "evaluation_report.json")
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "accuracy": accuracy,
            "total_tested": total,
            "results": results
        }, f, indent=4)
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
