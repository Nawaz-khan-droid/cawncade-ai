"""
LLM Service v3.0 — HuggingFace Inference API Integration.
Supports both direct HF Inference API (flan-t5-large default) and
HuggingFaceEndpoint via langchain-huggingface (Llama 3.1 for agent).
The agent_service.py uses the HuggingFaceEndpoint directly.
This service is used for template-based synthesis fallback.
"""

import os
import httpx
from app.config.settings import get_settings
from app.utils.logger import log

settings = get_settings()


class LLMService:
    """Interface to HuggingFace Inference API for text generation."""

    def __init__(self):
        self.api_token = settings.HUGGINGFACE_API_TOKEN or os.getenv("HUGGINGFACE_API_TOKEN")
        self.base_url = settings.HUGGINGFACE_INFERENCE_URL
        self.model_id = settings.LLM_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE

        if self.api_token:
            self.headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            log.info(f"[LLM] Configured: {self.model_id}")
        else:
            self.headers = {}
            log.warning("[LLM] No HUGGINGFACE_API_TOKEN. AI synthesis will use fallback.")

    async def generate(self, prompt: str, system_prompt: str = None,
                       max_tokens: int = None, temperature: float = None) -> str:
        if not self.api_token:
            return self._fallback_response(prompt)

        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        full_prompt = self._build_prompt(prompt, system_prompt)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}{self.model_id}",
                    headers=self.headers,
                    json={
                        "inputs": full_prompt,
                        "parameters": {
                            "max_new_tokens": max_tokens,
                            "temperature": temperature,
                            "return_full_text": False,
                        },
                    },
                )

                if response.status_code == 429:
                    log.warning("[LLM] Rate limited (429). Using fallback.")
                    return self._fallback_response(prompt)

                if response.status_code == 503:
                    log.warning("[LLM] Model loading (503). Using fallback.")
                    return self._fallback_response(prompt)

                response.raise_for_status()
                result = response.json()

                if isinstance(result, list) and result:
                    text = result[0].get("generated_text", "").strip()
                    return text if text else self._fallback_response(prompt)
                elif isinstance(result, dict):
                    text = result.get("generated_text", "").strip()
                    return text if text else self._fallback_response(prompt)

                return self._fallback_response(prompt)

        except httpx.TimeoutException:
            log.error("[LLM] Timeout (120s). Using fallback.")
            return self._fallback_response(prompt)
        except Exception as e:
            log.error(f"[LLM] Error: {e}. Using fallback.")
            return self._fallback_response(prompt)

    def _build_prompt(self, user_prompt: str, system_prompt: str = None) -> str:
        model = self.model_id.lower()
        if "t5" in model or "flan" in model:
            parts = []
            if system_prompt:
                parts.append(f"Context: {system_prompt}")
            parts.append(f"Task: {user_prompt}")
            return "\n\n".join(parts)
        parts = []
        if system_prompt:
            parts.append(f"<system>\n{system_prompt}\n</system>\n")
        parts.append(f"<instruction>\n{user_prompt}\n</instruction>")
        parts.append("<response>")
        return "\n".join(parts)

    def _fallback_response(self, prompt: str) -> str:
        return (
            "Analysis based on retrieved sources without AI synthesis. "
            "Configure HUGGINGFACE_API_TOKEN in Hugging Face Space secrets "
            "to enable AI-powered detailed analysis."
        )

    def is_available(self) -> bool:
        return bool(self.api_token)


llm_service = LLMService()
