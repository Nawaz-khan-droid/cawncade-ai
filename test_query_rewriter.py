import sys

sys.path.insert(0, 'backend')
from app.services.tier4.claim_parser import claim_parser

raw_transcript_input = """
Unknown Title [♪♪♪]
♪ We're no strangers to love ♪
♪ You know the rules and so do I ♪
♪ A full commitment's what I'm thinking of ♪
♪ You wouldn't get this from any other guy ♪
♪ Never gonna give you up ♪
♪ Never gonna let you down ♪
"""

rewritten = claim_parser.rewrite_query_for_search(raw_transcript_input)

print("=================== QUERY REWRITER STAGE VERIFICATION ===================")
print("Raw Input (Musical Symbols & Transcripts):")
print(raw_transcript_input.strip())
print("\nRewritten Clean Search Query:")
print(f"'{rewritten}'")
