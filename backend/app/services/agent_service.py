"""
CAWNCADE AI v3.0 — LangChain ReAct Agent Service.
Uses Llama 3.1 8B Instruct via HuggingFaceEndpoint for agentic reasoning.
The agent uses DuckDuckGoSearchAPIWrapper as a search tool to fill knowledge gaps.
Falls back gracefully if LangChain or HF token is unavailable.

NON-NEGOTIABLE REQUIREMENTS (Phase 4):
  - DuckDuckGoSearchAPIWrapper MUST use time=None (historical access, no 24hr limit)
  - Agent prompt MUST command source_url citation for EVERY fact in the final report
  - max_iterations=5 to prevent infinite loops on HF free tier (2 vCPU, 16GB RAM)
  - HuggingFaceEndpoint (inference runs on HF servers, NOT locally)
"""

import os
import asyncio
from app.config.settings import get_settings
from app.core.resilience import circuit_agent
from app.core.cache import cache
from app.utils.logger import log

settings = get_settings()

# ── REASONING SYSTEM PROMPT (explicitly commands source citations) ──
REASONING_SYSTEM_PROMPT = """You are CAWNCADE-AI, an expert professional fact-checker and news verification analyst.

CRITICAL RULES:
1. You MUST cite the source_url for EVERY fact, claim, or data point in your final report.
2. Use the format: [Source: URL] after each factual statement.
3. If you cannot verify a claim from your search results, explicitly state "UNVERIFIED" rather than guessing.
4. Provide a final verdict: VERIFIED, PARTIALLY TRUE, MISLEADING, or FALSE.
5. Explain your reasoning step by step - show your evidence before concluding.
6. Compare what the user claims against what your sources actually say.
7. If sources contradict each other, report the conflict explicitly.

STRUCTURE YOUR REPORT AS:
- CLAIM ANALYSIS: What is being claimed
- EVIDENCE FOUND: What the sources say (with source URLs)
- VERDICT: Your final assessment
- CONFIDENCE: How confident you are (High/Medium/Low) and why"""


class CawncadeAgent:
    """
    LangChain ReAct Agent for deep-dive news verification.
    Uses Thought -> Action (DDG Search) -> Observation -> Final Answer loop.
    """

    def __init__(self):
        self._agent_executor = None
        self._initialized = False

    def _init_agent(self):
        """Lazy-initialize the agent to avoid import errors if langchain is not installed."""
        if self._initialized:
            return

        try:
            from langchain_huggingface import HuggingFaceEndpoint
            from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

            api_token = settings.HUGGINGFACE_API_TOKEN or os.getenv("HUGGINGFACE_API_TOKEN")
            if not api_token:
                log.warning("[Agent] No HUGGINGFACE_API_TOKEN. Agent synthesis disabled.")
                self._initialized = True
                return

            # LLM: Llama 3.1 8B Instruct via HF Inference API
            # Model runs on HF's servers — ZERO local RAM/CPU usage
            self.llm = HuggingFaceEndpoint(
                repo_id=settings.AGENT_MODEL,
                max_new_tokens=settings.AGENT_MAX_TOKENS,
                temperature=settings.AGENT_TEMPERATURE,
                huggingfacehub_api_token=api_token,
            )

            # Tool: DuckDuckGo Search via LangChain
            # NON-NEGOTIABLE: time=None ensures historical fact-checking (NOT limited to 24 hours)
            wrapper = DuckDuckGoSearchAPIWrapper(
                region="wt-wt",
                time=None,  # NO hardcoded time limit — searches full web history
                max_results=5,
            )
            self.search_tool = DuckDuckGoSearchRun(api_wrapper=wrapper)

            # ReAct Prompt from LangChain Hub
            from langchain import hub
            self.prompt = hub.pull("hwchase17/react")

            # Build the ReAct Agent
            from langchain.agents import AgentExecutor, create_react_agent
            agent = create_react_agent(self.llm, [self.search_tool], self.prompt)
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=[self.search_tool],
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=settings.AGENT_MAX_ITERATIONS,  # 5 iterations max
            )

            self._initialized = True
            log.info(f"[Agent] Initialized: {settings.AGENT_MODEL} + DuckDuckGoSearchAPIWrapper (time=None)")

        except ImportError as e:
            log.warning(f"[Agent] LangChain not installed ({e}). Agent synthesis disabled.")
            self._initialized = True
        except Exception as e:
            log.error(f"[Agent] Initialization failed: {e}")
            self._initialized = True

    async def run_investigation(self, query: str, evidence_context: str = "") -> str:
        """
        Run the ReAct agent to produce a deep-dive verification report.
        Falls back to template-based synthesis if agent is unavailable.

        The agent receives pre-gathered evidence from Tiers 1-3 and uses
        DuckDuckGo ONLY for gaps, then synthesizes a final report with
        source_url citations for every fact.
        """
        self._init_agent()

        if not self._agent_executor:
            return self._template_synthesis(query, evidence_context)

        cache_key = f"agent:{query[:200]}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Build the agent input with the reasoning system prompt
        agent_input = (
            f"{REASONING_SYSTEM_PROMPT}\n\n"
            f"USER CLAIM TO VERIFY: {query}\n"
        )

        if evidence_context:
            agent_input += (
                f"\nEVIDENCE ALREADY FOUND from our trusted search tiers:\n"
                f"{evidence_context}\n\n"
                f"Use your DuckDuckGo search tool ONLY if you need additional evidence "
                f"to fill gaps. Your final report MUST cite source URLs for every fact."
            )
        else:
            agent_input += (
                f"\nNo pre-existing evidence available. "
                f"Use your DuckDuckGo search tool to find evidence. "
                f"Your final report MUST cite source URLs for every fact."
            )

        async def _call():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: self._agent_executor.invoke({"input": agent_input})
            )

        result = await circuit_agent.call(_call)
        if result is None:
            log.warning("[Agent] Agent call failed (circuit open). Using template synthesis.")
            return self._template_synthesis(query, evidence_context)

        output = result.get("output", "") if isinstance(result, dict) else str(result)

        if not output or len(output) < 50:
            log.warning("[Agent] Agent returned empty/short response. Using template.")
            return self._template_synthesis(query, evidence_context)

        cache.set(cache_key, output, ttl=settings.SEARCH_CACHE_TTL)
        log.info(f"[Agent] Investigation complete: {len(output)} chars for '{query[:60]}'")
        return output

    def _template_synthesis(self, query: str, evidence: str = "") -> str:
        """Fallback template-based synthesis when agent is unavailable."""
        if evidence:
            return (
                f"CLAIM ANALYSIS: {query}\n\n"
                f"EVIDENCE FOUND:\n{evidence}\n\n"
                f"VERDICT: Analysis based on retrieved sources without AI-powered reasoning.\n\n"
                f"Note: AI-powered deep analysis (Llama 3.1 agent) is unavailable. "
                f"Add HUGGINGFACE_API_TOKEN to enable full agent reasoning with source citations."
            )
        return (
            f"CLAIM ANALYSIS: {query}\n\n"
            f"EVIDENCE FOUND: Insufficient data for verification.\n\n"
            f"VERDICT: CANNOT ASSESS\n\n"
            f"Configure HUGGINGFACE_API_TOKEN to enable the Llama 3.1 agent for deep analysis."
        )

    def is_available(self) -> bool:
        """Check if the agent is initialized and ready."""
        self._init_agent()
        return self._agent_executor is not None


# Singleton instance
cawncade_agent = CawncadeAgent()
