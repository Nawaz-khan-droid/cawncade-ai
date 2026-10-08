"""
Core Corrective RAG (CRAG) Pipeline implementation.
Features:
- Pure Python Async State Machine
- Retries via Tenacity
- Structured Pydantic LLM Responses via Raw HTTP
"""

import os
import json
import logging
import httpx
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("cawncade.crag_pipeline")

class DocumentEvaluation(BaseModel):
    is_relevant: bool = Field(description="True if the document contains factual information directly confirming or refuting the claim.")
    extracted_facts: str = Field(description="Extracted objective facts only. Ignore opinion and formatting.")
    confidence: float = Field(description="Relevance confidence score (0.0 to 1.0).")

class FinalVerdict(BaseModel):
    verdict: str = Field(description="Must be exactly: VERIFIED_TRUE, FALSE_DEBUNKED, or UNVERIFIED.")
    confidence_score: float = Field(description="Overall confidence in the final verdict (0.0 to 1.0).")
    structured_explanation: str = Field(description="Objective, step-by-step reasoning proving the verdict using only the retrieved facts.")

class CRAGPipeline:
    def __init__(self, primary_model: str = "openai/gpt-oss-120b"):
        self.model = primary_model
        from dotenv import load_dotenv
        load_dotenv(".env")
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_base = "https://api.groq.com/openai/v1/chat/completions"

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.api_base, headers=headers, json=payload, timeout=30.0)
            if response.status_code != 200: logger.error(f"GROQ ERROR: {response.status_code} - {response.text}"); response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def evaluate_document(self, claim: str, document_text: str) -> DocumentEvaluation:
        system_prompt = (
            "You are a strict Evaluator Node in a Corrective RAG system. "
            "Your job is to determine if the provided document contains factual evidence that proves or disproves the claim. "
            "You MUST output exactly valid JSON matching this schema: {\"is_relevant\": bool, \"extracted_facts\": string, \"confidence\": float(0.0-1.0)}"
        )
        content = await self._call_llm(system_prompt, f"Claim: {claim}\n\nDocument: {document_text[:4000]}")
        content = content.strip()
        if content.startswith("```json"): content = content[7:]
        elif content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        content = content.strip()
        return DocumentEvaluation.model_validate_json(content)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_final_verdict(self, claim: str, sanitized_evidence: List[str]) -> FinalVerdict:
        system_prompt = (
            "You are the Final Verdict Synthesis Node. Evaluate the claim strictly against the sanitized evidence. "
            "If the evidence is contradictory or insufficient, report UNVERIFIED. "
            "You MUST output exactly valid JSON matching this schema: {\"verdict\": \"VERIFIED_TRUE\"|\"FALSE_DEBUNKED\"|\"UNVERIFIED\", \"confidence_score\": float, \"structured_explanation\": string}"
        )
        evidence_payload = "\n---\n".join(sanitized_evidence)
        content = await self._call_llm(system_prompt, f"Claim: {claim}\n\nEvidence:\n{evidence_payload}")
        content = content.strip()
        if content.startswith("```json"): content = content[7:]
        elif content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        content = content.strip()
        return FinalVerdict.model_validate_json(content)

    async def execute_crag(self, claim: str, initial_documents: List[Dict[str, str]]) -> Dict[str, Any]:
        logger.info(f"[CRAG Pipeline] Processing claim: {claim}")
        sanitized_facts = []
        requires_deep_search = False
        
        for doc in initial_documents[:3]:  # Limit to top 3 to avoid extreme latency
            try:
                eval_result = await self.evaluate_document(claim, doc.get("snippet", ""))
                if eval_result.is_relevant and eval_result.confidence > 0.6:
                    sanitized_facts.append(f"Source: {doc.get('url')} | Fact: {eval_result.extracted_facts}")
                else:
                    requires_deep_search = True
            except Exception as e:
                logger.warning(f"[CRAG] Evaluation failure on document: {e}")
                requires_deep_search = True

        if requires_deep_search or not sanitized_facts:
            logger.info("[CRAG] Initial retrieval insufficient/incorrect. Triggering Corrective Deep Web Search...")
            from app.services.news_service import tiered_search
            deep_results = await tiered_search(claim)
            
            for doc in deep_results.get("sources", [])[:3]:
                try:
                    eval_result = await self.evaluate_document(claim, doc.get("snippet", ""))
                    if eval_result.is_relevant and eval_result.confidence > 0.5:
                        sanitized_facts.append(f"Source: {doc.get('url')} | Fact: {eval_result.extracted_facts}")
                except Exception as e:
                    continue

        if not sanitized_facts:
            return {
                "verdict_code": "UNVERIFIED",
                "confidence_score": 0.0,
                "layer2_verification": "System safe-state triggered: No clean, reliable evidence could be harvested."
            }
            
        try:
            verdict_result = await self.generate_final_verdict(claim, sanitized_facts)
            return {
                "verdict_code": verdict_result.verdict,
                "confidence_score": verdict_result.confidence_score,
                "layer2_verification": verdict_result.structured_explanation
            }
        except Exception as e:
            logger.critical(f"[CRAG] Verdict generation failed: {e}")
            return {
                "verdict_code": "UNVERIFIED",
                "confidence_score": 0.0,
                "layer2_verification": "Internal system failure while compiling final analytical decision matrices."
            }

crag_pipeline = CRAGPipeline()
