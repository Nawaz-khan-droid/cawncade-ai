"""
CAWNCADE AI v3.5 — LangChain ReAct Agent Service.
Refined: High-precision DuckDuckGo News Search integration.
Fixed: Removed general web noise (jewelry/videos) by forcing 'news' source.
"""

import os
import asyncio
from langchain_openai import ChatOpenAI 
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from app.config.settings import get_settings
from app.core.resilience import circuit_agent
from app.utils.logger import log

settings = get_settings()

class CawncadeAgent:
    def __init__(self):
        self._agent_executor = None
        self._initialized = False

    def _init_agent(self):
        """Initializes the Llama 3.1 engine via HF Router with News-First Search."""
        if self._initialized: return
        
        try:
            # Retrieve token from settings or environment
            api_token = settings.HUGGINGFACE_API_TOKEN or os.getenv("HUGGINGFACE_API_TOKEN")

            # Temperature set to 0 for strict fact-checking (no creative wandering)
            self.llm = ChatOpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=api_token,
                model="meta-llama/Llama-3.1-8B-Instruct",
                temperature=0,
                max_tokens=1024
            )

            # FINE-TUNED NEWS SEARCH: 
            # We force source="news" to prevent shopping/jewelry/video hallucinations.
            wrapper = DuckDuckGoSearchAPIWrapper(
                region="wt-wt", 
                time="m", # Focus on the current month for 2026 news
                max_results=5,
                source="news" 
            )
            self.search_tool = DuckDuckGoSearchRun(api_wrapper=wrapper)

            # Pull the standard ReAct prompt from LangChain Hub
            self.prompt = hub.pull("hwchase17/react")
            
            # Create the ReAct agent
            agent = create_react_agent(self.llm, [self.search_tool], self.prompt)
            
            # The Executor manages the Thought/Action/Observation loop
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=[self.search_tool],
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=4 
            )

            self._initialized = True
            log.info("[Agent] Llama 3.1 + DDG News Engine armed and ready.")

        except Exception as e:
            log.error(f"[Agent] Engine Initialization Failed: {e}")
            self._initialized = False 

    async def run_investigation(self, query: str, evidence_context: str = "") -> str:
        """Runs a deep-dive investigation into a specific claim using news archives."""
        self._init_agent()
        
        if not self._agent_executor:
            return self._template_synthesis(query, evidence_context)

        # STRICT INSTRUCTION PROMPT: Forces the LLM to filter for reputable news.
        agent_input = (
            f"You are a professional fact-checker. Verify this NEWS CLAIM: {query}\n\n"
            f"PROVIDED EVIDENCE: {evidence_context}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Use the search tool to find verified news reports from 2026.\n"
            f"2. IGNORE jewelry brands, shopping sites, or unrelated viral videos.\n"
            f"3. Focus on reputable outlets (e.g., Reuters, PTI, The Hindu, Livemint).\n"
            f"4. Provide a clear VERDICT (True, False, or Mixed).\n"
            f"5. MANDATORY: Cite the full source URL for every fact used in your final answer."
        )

        async def _call():
            # Run the synchronous LangChain invoke in a thread pool for async compatibility
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self._agent_executor.invoke({"input": agent_input})
            )

        try:
            # Wrapped in a circuit breaker for stability
            result = await circuit_agent.call(_call)
            
            if result is None:
                return self._template_synthesis(query, evidence_context)

            output = result.get("output", "")
            
            # Ensure we didn't get an empty response
            if not output or len(output) < 30:
                return "No conclusive evidence found in news archives to verify this claim."
                
            return output

        except Exception as e:
            log.error(f"[Agent] Investigation execution failed: {e}")
            return self._template_synthesis(query, evidence_context)

    def _template_synthesis(self, query: str, evidence: str = "") -> str:
        """Fallback synthesis when the reasoning engine is unavailable."""
        summary = evidence[:300] if evidence else "No direct evidence found."
        return (
            f"VERDICT: PRELIMINARY ASSESSMENT\n\n"
            f"Reasoning: The deep-check engine is currently adjusting search parameters. "
            f"Initial data snippet: {summary}..."
        )

# Exported instance for the orchestrator
cawncade_agent = CawncadeAgent()