import sys
import json

sys.path.insert(0, 'backend')
from app.services.tier4.claim_parser import claim_parser

test_cases = [
    ("1. YouTube Subtitles / Song Lyrics", "Unknown Title [♪♪♪] ♪ We're no strangers to love ♪ You know the rules and so do I ♪"),
    ("2. Quantitative Health Claim (Numbers & Entities)", "WHO says vaccine X reduced deaths by 40% in 2024 in India"),
    ("3. Space Science Claim (NASA & Named Entities)", "NASA launches Europa Clipper spacecraft to study Jupiter moon Europa in October 2024")
]

print("=================== TESTING QUERY EXPANSION & ENTITY-PRESERVING ENGINE v2.0 ===================")
for label, raw_input in test_cases:
    print(f"\n--- {label} ---")
    print("Raw Input:", raw_input)
    expanded = claim_parser.generate_expanded_queries(raw_input)
    print("Generated Expanded Queries (3-4 Parallel Variations):")
    for i, q in enumerate(expanded, 1):
        print(f"  Query {i}: {q}")
