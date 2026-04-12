"""
CAWNCADE AI v3.1 — LangChain ReAct Agent Service.
Updated with FLAN-T5 compatibility and resilient error handling.
"""

import os
import asyncio
from langchain_huggingface import HuggingFaceEndpoint
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from app.config.settings import get_settings
from app.core.resilience import circuit_agent
from app.core.cache import cache
from app.utils.logger import log

settings = get_settings()

class CawncadeAgent:
    def __init__(self):
        self._agent_executor = None
        self._initialized = False

    def _init_agent(self):
        """Initializes the LLM and Agent with correct parameter mapping."""
        if self._initialized: return
        
        try:
            # Using FLAN-T5 while awaiting Llama 3.1 gated approval
            repo_id = "google/flan-t5-large"
            api_token = settings.HUGGINGFACE_API_TOKEN or os.getenv("HUGGINGFACE_API_TOKEN")

            # FIX: model_kwargs is the correct key for text-generation parameters
            self.llm = HuggingFaceEndpoint(
                repo_id=repo_id,
                huggingfacehub_api_token=api_token,
                timeout=120,
                model_kwargs={
                    "max_new_tokens": 512,
                    "temperature": 0.1,
                }
            )

            # Initialize Search Tool (DuckDuckGo fallback)
            wrapper = DuckDuckGoSearchAPIWrapper(region="wt-wt", time=None, max_results=5)
            self.search_tool = DuckDuckGoSearchRun(api_wrapper=wrapper)

            # Load the standard ReAct logic prompt
            self.prompt = hub.pull("hwchase17/react")
            
            # Construct the Agent
            agent = create_react_agent(self.llm, [self.search_tool], self.prompt)
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=[self.search_tool],
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5 
            )

            self._initialized = True
            log.info(f"[Agent] reasoning engine armed: {repo_id}")

        except Exception as e:
            log.error(f"[Agent] Initialization failed: {e}")
            # Keep as False to retry next time, or True to stop retrying
            self._initialized = False 

    async def run_investigation(self, query: str, evidence_context: str = "") -> str:
        """
        The core reasoning method called by the Orchestrator.
        Takes a claim and search results, and returns a verified verdict.
        """
        self._init_agent()
        
        # Cache check to save on API credits
        cache_key = f"agent_investigation:{hash(query + evidence_context)}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        if not self._agent_executor:
            log.warning("[Agent] Executor not ready. Falling back to template.")
            return self._template_synthesis(query, evidence_context)

        # Build the final prompt for the agent
        agent_input = (
            f"You are a professional fact-checker. Verify this claim using the evidence provided. "
            f"If more info is needed, use the search tool. Cite all sources.\n\n"
            f"CLAIM: {query}\n"
            f"EVIDENCE: {evidence_context}"
        )

        async def _call():
            loop = asyncio.get_event_loop()
            # AgentExecutor.invoke is a blocking call, run in thread pool
            return await loop.run_in_executor(
                None, lambda: self._agent_executor.invoke({"input": agent_input})
            )

        try:
            # Call via circuit breaker for reliability
            result = await circuit_agent.call(_call)
            
            # FIX: Check if result is None to avoid 'NoneType' object has no attribute 'get'
            if result is None:
                log.error("[Agent] Circuit breaker returned None.")
                return self._template_synthesis(query, evidence_context)

            output = result.get("output", "")
            
            if not output or len(output) < 20:
                return self._template_synthesis(query, evidence_context)
            
            # Store in cache
            cache.set(cache_key, output, ttl=3600)
            return output

        except Exception as e:
            log.error(f"[Agent] Investigation crashed: {e}")
            return self._template_synthesis(query, evidence_context)

    def _template_synthesis(self, query: str, evidence: str = "") -> str:
        """The 'Safe Mode' response if the AI fails or is offline."""
        if not evidence:
            return f"VERDICT: UNVERIFIED. (Reason: Reasoning engine offline and no search evidence found)."
        
        return (
            f"VERDICT: PRELIMINARY ASSESSMENT\n\n"
            f"Based on raw search data: {evidence[:200]}...\n\n"
            f"(Note: Deep AI reasoning is currently offline. This is a summary of raw data.)"
        )

# Global instance
cawncade_agent = CawncadeAgent()