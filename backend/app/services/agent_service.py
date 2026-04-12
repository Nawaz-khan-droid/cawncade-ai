"""
CAWNCADE AI v3.2 — LangChain ReAct Agent Service.
Upgraded to Llama 3.1 8B Instruct with Pydantic-compliant parameter mapping.
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
        """Initializes the Llama 3.1 8B reasoning engine."""
        if self._initialized: return
        
        try:
            # UPGRADED: Switched back to Llama 3.1 8B Instruct
            repo_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"
            api_token = settings.HUGGINGFACE_API_TOKEN or os.getenv("HUGGINGFACE_API_TOKEN")

            # Pydantic-compliant initialization (parameters as direct arguments)
            self.llm = HuggingFaceEndpoint(
                repo_id=repo_id,
                huggingfacehub_api_token=api_token,
                timeout=120,
                max_new_tokens=1024, # Increased for Llama's detailed reasoning
                temperature=0.1,
                repetition_penalty=1.1
            )

            # DuckDuckGo Tool for real-time verification
            wrapper = DuckDuckGoSearchAPIWrapper(region="wt-wt", time=None, max_results=5)
            self.search_tool = DuckDuckGoSearchRun(api_wrapper=wrapper)

            # Load the standard ReAct logic prompt
            self.prompt = hub.pull("hwchase17/react")
            
            # Construct the Agent with Llama
            agent = create_react_agent(self.llm, [self.search_tool], self.prompt)
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=[self.search_tool],
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5 
            )

            self._initialized = True
            log.info(f"[Agent] Llama 3.1 reasoning engine armed: {repo_id}")

        except Exception as e:
            log.error(f"[Agent] Llama 3.1 Init Failed: {e}")
            self._initialized = False # Retry on next request

    async def run_investigation(self, query: str, evidence_context: str = "") -> str:
        """Main entry point for claim verification."""
        self._init_agent()
        
        if not self._agent_executor:
            log.warning("[Agent] Agent offline. Using template fallback.")
            return self._template_synthesis(query, evidence_context)

        # Enhanced prompt for Llama 3.1 to ensure URL citations
        agent_input = (
            f"You are a professional fact-checker. Verify the following claim using the provided evidence. "
            f"If the evidence is insufficient, use the search tool to find more details. "
            f"CRITICAL: You MUST cite the source URL for every fact you state.\n\n"
            f"CLAIM: {query}\n"
            f"EVIDENCE: {evidence_context}\n\n"
            f"Final Answer Format: Give a VERDICT followed by your detailed reasoning and sources."
        )

        async def _call():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self._agent_executor.invoke({"input": agent_input})
            )

        try:
            result = await circuit_agent.call(_call)
            
            if result is None:
                return self._template_synthesis(query, evidence_context)

            output = result.get("output", "")
            
            # Llama usually provides longer output; threshold remains for safety
            if not output or len(output) < 20:
                return self._template_synthesis(query, evidence_context)
                
            return output

        except Exception as e:
            log.error(f"[Agent] Investigation crashed: {e}")
            return self._template_synthesis(query, evidence_context)

    def _template_synthesis(self, query: str, evidence: str = "") -> str:
        """Safe mode fallback synthesis."""
        if not evidence:
            return "VERDICT: UNVERIFIED. Reasoning engine is initializing or offline."
        
        return (
            f"VERDICT: PRELIMINARY ASSESSMENT (Agent Offline)\n\n"
            f"Summary of raw evidence: {evidence[:300]}...\n\n"
            f"Note: This summary was generated without full AI reasoning."
        )

# Global instance for use in orchestrators
cawncade_agent = CawncadeAgent()