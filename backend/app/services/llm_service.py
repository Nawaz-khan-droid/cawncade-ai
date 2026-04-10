import httpx
import json
import os
from ..config.settings import get_settings
from ..utils.logger import log

settings = get_settings()

class LLMService:
    """Interface to HuggingFace Inference API using Gemma-7b."""

    def __init__(self):
        # Use the token from settings/environment
        self.api_token = settings.HUGGINGFACE_API_TOKEN or os.getenv("HUGGINGFACE_API_TOKEN")
        
        # Official Hugging Face Inference URL for Gemma-7b
        self.base_url = "https://api-inference.huggingface.co/models/google/gemma-7b"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """
        Generate text using HuggingFace Inference API.
        This uses httpx (async) to prevent blocking your FastAPI backend.
        """
        if not self.api_token:
            log.warning("No HUGGINGFACE_API_TOKEN set. Returning fallback response.")
            return self._fallback_response(prompt)

        full_prompt = self._build_prompt(prompt, system_prompt)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # We post directly to the base_url because it already includes the model ID
                response = await client.post(
                    self.base_url,
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
                    log.warning("HF API rate limited (429). Check your plan or token.")
                    return self._fallback_response(prompt)

                response.raise_for_status()
                result = response.json()
                
                if isinstance(result, list) and result:
                    return result[0].get("generated_text", "").strip()
                return ""

        except httpx.TimeoutException:
            log.error("HF API timeout. Using fallback.")
            return self._fallback_response(prompt)
        except Exception as e:
            log.error(f"HF API error: {e}. Using fallback.")
            return self._fallback_response(prompt)

    def _build_prompt(self, user_prompt: str, system_prompt: str = None) -> str:
        parts = []
        if system_prompt:
            parts.append(f"<system>\n{system_prompt}\n</system>\n")
        parts.append(f"<instruction>\n{user_prompt}\n</instruction>")
        parts.append("<response>")
        return "\n".join(parts)

    def _fallback_response(self, prompt: str) -> str:
        return (
            "Analysis based on retrieved sources without AI synthesis. "
            "The system was unable to generate a detailed explanation via Gemma-7b at this time."
        )

# Singleton instance for use across the app
llm_service = LLMService()