import asyncio
import sys

sys.path.insert(0, 'backend')
from app.services.tier4.verification_service import tier4_verification_service
from app.services.agent_service import smart_claim_router
from app.core.resilience import get_all_circuit_breaker_telemetry

async def run_explainability_test():
    print("=================== EXPLAINABILITY & SMART ROUTING REGRESSION TEST ===================")

    # 1. Test Explainable Verification & Dated Timeline
    mock_sources = [
        {
            "url": "https://www.nasa.gov/news/europa-clipper-launch",
            "title": "NASA Launches Europa Clipper Spacecraft on October 14, 2024",
            "snippet": "On October 14, 2024, NASA's Europa Clipper launched aboard a SpaceX Falcon Heavy rocket from Kennedy Space Center to study Jupiter's ocean moon.",
            "source_name": "NASA.gov",
            "domain": "nasa.gov"
        },
        {
            "url": "https://www.bbc.com/news/science-space-europa",
            "title": "BBC: Europa Clipper En Route to Jupiter Moon",
            "snippet": "In October 2024, NASA launched the Europa Clipper mission to investigate signs of habitability on Europa.",
            "source_name": "BBC News",
            "domain": "bbc.com"
        }
    ]

    analysis = tier4_verification_service.analyze_explainable_verification("NASA launched Europa Clipper in October 2024", mock_sources)

    print("\n1. Explainability Output Structure:")
    print(f"   Verdict           : {analysis.get('verdict')}")
    print(f"   Confidence Score  : {analysis.get('confidence_score')}%")
    print(f"   Entity Alignment  : {analysis.get('explainability', {}).get('entity_alignment')}")
    print(f"   Source Quality    : {analysis.get('explainability', {}).get('source_quality')}")
    print(f"   Conflict Breakdown: {analysis.get('explainability', {}).get('conflict_breakdown')}")

    print("\n2. Dated Timeline Milestones (with Confidence Scores):")
    for t in analysis.get("timeline", []):
        print(f"   - [{t['date']}] {t['event']} (Source: {t['source']} | Confidence: {t['confidence']:.2f})")

    # 3. Test Smart Claim Cost Router
    print("\n3. Smart Claim Cost Router Evaluation:")
    route_res = smart_claim_router.evaluate_route(
        claim="NASA launched Europa Clipper in October 2024",
        entity_confidence=0.90,
        tier1_sources=2,
        contradiction_count=0,
        total_sources=2
    )
    print(f"   Selected Route   : {route_res.get('selected_route')}")
    print(f"   Cost Saved Flag  : {route_res.get('cost_saved')}")
    print(f"   Routing Rationale: {route_res.get('reason')}")

    # 4. Circuit Breaker Telemetry Check
    print("\n4. Circuit Breaker Telemetry Status:")
    telemetry = get_all_circuit_breaker_telemetry()
    for provider, stats in list(telemetry.items())[:4]:
        print(f"   - {provider}: State={stats['state']}, Failures={stats['failures']}, Total Calls={stats['total_calls']}")

if __name__ == "__main__":
    asyncio.run(run_explainability_test())
