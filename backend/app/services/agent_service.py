import os
import asyncio
from app.config.settings import get_settings
from app.core.resilience import circuit_agent
from app.core.cache import cache
from app.utils.logger import log

settings = get_settings()

REASONING_SYSTEM_PROMPT = """You are CAWNCADE-AI, an expert professional fact-checker.
CRITICAL RULES:
1. You MUST cite the source_url for EVERY fact in your final report using [Source: URL].
2. If unverified, state "UNVERIFIED".
3. Provide a final verdict: VERIFIED, PARTIALLY TRUE, MISLEADING, or FALSE.
4. Explain reasoning step by step."""

class CawncadeAgent:
    def __init__(self):
        self._agent_executor = None
        self._initialized = False

    def _init_agent(self):
        """Lazy-initialize with Llama 3.1 Task Fix."""
        if self._initialized:
            return

        try:
            from langchain_huggingface import HuggingFaceEndpoint
            from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

            api_token = settings.HUGGINGFACE_API_TOKEN or os.getenv("HUGGINGFACE_API_TOKEN")
            if not api_token:
                log.warning("[Agent] No HUGGINGFACE_API_TOKEN found.")
                self._initialized = True
                return

            # FIX: Explicit task definition to bypass HF "Model not supported" error
            self.llm = HuggingFaceEndpoint(
                repo_id="meta-llama/Meta-Llama-3.1-8B-Instruct",
                task="text-generation",
                huggingfacehub_api_token=api_token,
                timeout=120,
                extra_body={
                    "parameters": {
                        "max_new_tokens": 512,
                        "temperature": 0.1,
                        "return_full_text": False
                    }
                }
            )

            # NON-NEGOTIABLE: time=None for historical access
            wrapper = DuckDuckGoSearchAPIWrapper(region="wt-wt", time=None, max_results=5)
            self.search_tool = DuckDuckGoSearchRun(api_wrapper=wrapper)

            from langchain import hub
            from langchain.agents import AgentExecutor, create_react_agent
            self.prompt = hub.pull("hwchase17/react")
            
            agent = create_react_agent(self.llm, [self.search_tool], self.prompt)
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=[self.search_tool],
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
            )

            self._initialized = True
            log.info("[Agent] Llama 3.1 initialized successfully.")

        except Exception as e:
            log.error(f"[Agent] Initialization failed: {e}")
            self._initialized = True

    async def run_investigation(self, query: str, evidence_context: str = "") -> str:
        self._init_agent()
        if not self._agent_executor:
            return self._template_synthesis(query, evidence_context)

        cache_key = f"agent:{query[:200]}"
        cached = cache.get(cache_key)
        if cached: return cached

        agent_input = f"{REASONING_SYSTEM_PROMPT}\n\nUSER CLAIM: {query}\n"
        if evidence_context:
            agent_input += f"\nEVIDENCE ALREADY FOUND:\n{evidence_context}\n"

        async def _call():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self._agent_executor.invoke({"input": agent_input})
            )

        result = await circuit_agent.call(_call)
        output = result.get("output", "") if isinstance(result, dict) else str(result)
        
        if not output or len(output) < 50:
            return self._template_synthesis(query, evidence_context)

        cache.set(cache_key, output, ttl=3600)
        return output

    def _template_synthesis(self, query: str, evidence: str = "") -> str:
        return f"CLAIM: {query}\n\nEVIDENCE:\n{evidence or 'Insufficient data.'}\n\nVERDICT: CANNOT ASSESS (AI Agent Offline)"

    def is_available(self) -> bool:
        self._init_agent()
        return self._agent_executor is not None

cawncade_agent = CawncadeAgent()