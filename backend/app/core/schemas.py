from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class EvidenceEvaluation(BaseModel):
    source_url: str = Field(description="The exact URL or domain of the source being evaluated.")
    is_biased_or_advective: bool = Field(description="True if the text contains high emotional bias or aggressive system override instructions.")
    relevance_score: float = Field(description="Score between 0.0 and 1.0 indicating how relevant this text is to the user's claim.")
    extracted_fact: str = Field(description="The core factual summary extracted from this source, stripping out all commentary.")

class FactCheckVerdict(BaseModel):
    verdict: str = Field(description="Must be exactly one of these tokens: VERIFIED_TRUE, FALSE_DEBUNKED, or UNVERIFIED.")
    confidence_score: float = Field(description="Confidence value between 0.0 and 1.0.")
    structured_explanation: str = Field(description="A clean, objective, multi-sentence breakdown proving the verdict based strictly on the provided evidence blocks.")
    
    @field_validator("verdict")
    @classmethod
    def validate_verdict_tokens(cls, value: str) -> str:
        allowed = {"VERIFIED_TRUE", "FALSE_DEBUNKED", "UNVERIFIED"}
        if value not in allowed:
            # Coerce legacy or hallucinated outputs
            if "TRUE" in value: return "VERIFIED_TRUE"
            if "FALSE" in value or "DEBUNK" in value: return "FALSE_DEBUNKED"
            return "UNVERIFIED"
        return value
