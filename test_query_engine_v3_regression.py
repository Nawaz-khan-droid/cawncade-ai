import sys
import json

sys.path.insert(0, 'backend')
from app.services.tier4.claim_parser import claim_parser

test_suite = [
    (
        "TEST 1: Quantitative Health Claim (Location + Percent + Product + Year)",
        "WHO says vaccine X reduced deaths by 40% in India in 2024"
    ),
    (
        "TEST 2: Space Science Claim (NASA + Europa Clipper + Jupiter + Date)",
        "NASA launches Europa Clipper spacecraft to study Jupiter moon Europa in October 2024"
    ),
    (
        "TEST 3: YouTube Lyric Transcript (Exact Phrase Preservation)",
        "Unknown Title [♪♪♪]\n♪ We're no strangers to love ♪\n♪ You know the rules and so do I ♪"
    ),
    (
        "TEST 4: Famous Speech / Viral Quote",
        "\"I have a dream that one day this nation will rise up\""
    )
]

print("=================== REGRESSION TEST SUITE: QUERY ENGINE v3.0 ===================")

for title, raw_claim in test_suite:
    print(f"\n----------------------------------------------------------------------")
    print(title)
    print("----------------------------------------------------------------------")
    print("Raw Input:", repr(raw_claim))
    
    parsed = claim_parser.parse_claim(raw_claim)
    print("\nStructured Claim Object Extracted:")
    print("  - Organizations :", parsed["organizations"])
    print("  - Locations     :", parsed["locations"])
    print("  - Percentages   :", parsed["percentages"])
    print("  - Products/Codes:", parsed["products"])
    print("  - Years & Dates :", parsed["years"] + parsed["dates"])
    print("  - Quoted Phrases:", parsed["quoted_phrases"])

    queries = claim_parser.generate_expanded_queries(raw_claim)
    print("\nRanked & Scored Expanded Queries:")
    for i, q in enumerate(queries, 1):
        score = claim_parser.score_query_quality(q, parsed)
        print(f"  [Query {i} | Quality Score: {score:4.1f}] -> {q}")
