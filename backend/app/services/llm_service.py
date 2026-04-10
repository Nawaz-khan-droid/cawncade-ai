import httpx
import json
from ..config.settings import get_settings
from ..utils.logger import log

settings = get_settings()


class LLMService:
    """Interface to HuggingFace Inference API (or any OpenAI-compatible endpoint)."""

    def __init__(self):
        self.api_token = settings.HUGGINGFACE_API_TOKEN
        self.base_url = settings.HUGGINGFACE_INFERENCE_URL
        # Default model: use a free text-generation model
        self.model_id = "mistralai/Mistral-7B-Instruct-v0.2"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 1024, temperature: float = 0.3) -> str:
        """
        Generate text using HuggingFace Inference API.
        Falls back gracefully if API is unavailable.
        """
        if not self.api_token:
            log.warning("No HUGGINGFACE_API_TOKEN set. Returning fallback response.")
            return self._fallback_response(prompt)

        full_prompt = self._build_prompt(prompt, system_prompt)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
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
                    log.warning("HF API rate limited. Using fallback.")
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
        """Return a safe fallback when LLM is unavailable."""
        return (
            "Analysis based on retrieved sources without AI synthesis. "
            "The system was unable to generate a detailed explanation at this time. "
            "Please review the sources and scores manually."
        )


# Singleton instance
llm_service = LLMService()
