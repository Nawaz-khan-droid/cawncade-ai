import sys

sys.path.insert(0, 'backend')
from app.services.tier4.verification_service import tier4_verification_service
from app.services.tier4.verdict_engine import verdict_engine

print("=================== TESTING TIER 4 DETERMINISTIC VERDICT ENGINE ===================")

# Test Case 1: True / Supported Claim
claim1 = "Water boils at 100 degrees Celsius at standard atmospheric pressure"
evidence1 = "At standard atmospheric pressure at sea level, pure water boils at exactly 100 degrees Celsius (212 degrees Fahrenheit). This is a fundamental physical constant."
report1 = tier4_verification_service.generate_report(claim1, evidence1, sources_count=3, trusted_count=1)

print("\n--- TEST CASE 1: True Physical Constant ---")
print("Claim:", claim1)
for line in report1.split("\n"):
    if "Grounded Deterministic Verdict" in line or "Analysis" in line or "Ranked Evidence" in line:
        print(" ->", line)

# Test Case 2: Contradicted / False Claim
claim2 = "Water boils at 500 degrees Celsius at sea level"
evidence2 = "Claims that water boils at 500 degrees Celsius are false. Standard water boiling point at sea level is 100 degrees Celsius, not 500 degrees."
report2 = tier4_verification_service.generate_report(claim2, evidence2, sources_count=3, trusted_count=1)

print("\n--- TEST CASE 2: Contradicted Claim ---")
print("Claim:", claim2)
for line in report2.split("\n"):
    if "Grounded Deterministic Verdict" in line or "Analysis" in line or "Ranked Evidence" in line:
        print(" ->", line)

# Test Case 3: Insufficient / 0 Evidence Claim
claim3 = "Random unverified rumor with zero search results"
evidence3 = ""
report3 = tier4_verification_service.generate_report(claim3, evidence3, sources_count=0, trusted_count=0)

print("\n--- TEST CASE 3: Insufficient Evidence ---")
print("Claim:", claim3)
print(" ->", report3.split("\n")[0])
