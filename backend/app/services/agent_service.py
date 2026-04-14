"""
CAWNCADE AI v3.5 — LangChain ReAct Agent Service.

Phase 3.5 Upgrade: Triple-Tool Reasoning Engine
  Tool 1 — duckduckgo_search : Fast, free, noise-filtered news (source="news")
  Tool 2 — process_url       : Full-article fetch via Jina Reader (no proxy, no 403)
  Tool 3 — tavily_news_search: AI-ranked backup search (conditional on API key)

Bug Fixes Applied:
  BUG-03: asyncio.get_running_loop() replaces deprecated get_event_loop()
  BUG-04: max_iterations now reads from settings.AGENT_MAX_ITERATIONS (was hardcoded 4)
"""

import os
import asyncio
import httpx

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import tool
from langchain import hub
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

from app.config.settings import get_settings
from app.core.resilience import circuit_agent
from app.utils.logger import log

settings = get_settings()


# ═══════════════════════════════════════════════════════════════
# TOOL 2: Jina Reader — Full-Article Fetch (No Proxy, No 403)
# ═══════════════════════════════════════════════════════════════
@tool
def process_url(url: str) -> str:
    """
    Fetches the FULL text content of a news article from a given URL.
    Use this tool when a DuckDuckGo or Tavily snippet is too short to verify
    a claim. The Jina Reader proxy (r.jina.ai) handles paywalls and 403 bot-
    blocks automatically — no proxy configuration required.

    Input : A full URL string (e.g., https://reuters.com/article/some-story)
    Output: The article text, up to 4,000 characters (context-window safe).
    """
    try:
        jina_url = f"https://r.jina.ai/{url}"
        log.info(f"[process_url] Fetching via Jina Reader: {jina_url[:100]}")

        response = httpx.get(
            jina_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; CawncadeAI/3.5; "
                    "+https://huggingface.co/spaces) fact-checker"
                )
            },
            timeout=15.0,
            follow_redirects=True,
        )
        response.raise_for_status()

        content = response.text[:4000]
        log.info(
            f"[process_url] ✅ Fetched {len(content)} chars from: {url[:80]}"
        )
        return content if content.strip() else "No readable content found at this URL."

    except httpx.TimeoutException:
        log.warning(f"[process_url] ⚠️ Timeout fetching: {url[:80]}")
        return "Could not retrieve article: request timed out after 15 seconds."
    except httpx.HTTPStatusError as e:
        log.warning(
            f"[process_url] ⚠️ HTTP {e.response.status_code} for: {url[:80]}"
        )
        return f"Could not retrieve article: HTTP {e.response.status_code} error."
    except Exception as e:
        log.warning(f"[process_url] ⚠️ Failed for {url[:80]}: {e}")
        return f"Could not retrieve article content: {str(e)[:200]}"


# ═══════════════════════════════════════════════════════════════
# CAWNCADE AGENT — ReAct Engine
# ═══════════════════════════════════════════════════════════════
class CawncadeAgent:
    """
    ReAct agent powered by Llama 3.1 8B via Hugging Face Router.
    Maintains a triple-tool research stack assembled at init time.
    """

    def __init__(self):
        self._agent_executor: AgentExecutor | None = None
        self._initialized: bool = False
        self.tools: list = []

    # ── Tool Assembly ──────────────────────────────────────────
    def _build_tools(self) -> list:
        """
        Assembles the tool list dynamically based on available API keys.
        Always includes: DDG News + Jina Reader.
        Conditionally includes: Tavily (only if TAVILY_API_KEY is set).
        """
        # ── Tool 1: DuckDuckGo News Search ─────────────────────
        # source="news" is the PRIMARY noise-blocking mechanism.
        # Prevents jewelry, shopping, dog-video hallucinations.
        wrapper = DuckDuckGoSearchAPIWrapper(
            region="wt-wt",
            time="m",          # Last 30 days — relevant 2026 news only
            max_results=5,
            source="news",     # ← KEY: forces news results only
        )
        ddg_tool = DuckDuckGoSearchRun(
            api_wrapper=wrapper,
            description=(
                "Search DuckDuckGo for recent news articles (news only, last 30 days). "
                "Use this FIRST for any fact-checking query. "
                "Returns titles, snippets, and URLs from reputable news sources."
            ),
        )
        built_tools = [ddg_tool, process_url]

        # ── Tool 3: Tavily AI Search (Conditional Backup) ──────
        # Preserves your 'backup' intent — only active when key is present.
        # Gives Llama 3.1 the autonomous choice: "DDG failed, use Tavily."
        tavily_key = settings.TAVILY_API_KEY or os.getenv("TAVILY_API_KEY", "")
        if tavily_key:
            try:
                from langchain_community.tools.tavily_search import TavilySearchResults

                # LangChain's Tavily wrapper reads the key from os.environ
                os.environ["TAVILY_API_KEY"] = tavily_key

                tavily_tool = TavilySearchResults(
                    max_results=3,
                    name="tavily_news_search",
                    description=(
                        "AI-powered news search via Tavily. Use this as a BACKUP "
                        "if duckduckgo_search returns irrelevant, noisy, or insufficient results. "
                        "Returns high-quality, AI-ranked news articles with full context."
                    ),
                )
                built_tools.append(tavily_tool)
                log.info("[Agent] ✅ Tavily news search tool armed (backup, quota-preserving).")
            except ImportError:
                log.warning(
                    "[Agent] ⚠️ TavilySearchResults not importable from langchain_community. "
                    "Ensure langchain-community>=0.0.10 is installed."
                )
            except Exception as e:
                log.warning(f"[Agent] ⚠️ Tavily tool failed to initialize: {e}")
        else:
            log.info("[Agent] ℹ️ TAVILY_API_KEY not set — Tavily tool skipped.")

        return built_tools

    # ── Lazy Initialization ────────────────────────────────────
    def _init_agent(self):
        """
        Initializes Llama 3.1 via HF Router on first call (lazy init).
        Idempotent — safe to call multiple times.
        """
        if self._initialized:
            return

        try:
            api_token = (
                settings.HUGGINGFACE_API_TOKEN
                or os.getenv("HUGGINGFACE_API_TOKEN", "")
            )

            # ── LLM: Llama 3.1 8B via HF Router ───────────────
            # base_url uses the HF Router because it exposes the OpenAI
            # chat-completions contract (/v1/chat/completions).
            # This bypasses the old HF Serverless Inference API that
            # caused Phase 2 task-compatibility failures (Flan-T5).
            self.llm = ChatOpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=api_token,
                model="meta-llama/Llama-3.1-8B-Instruct",
                temperature=0,        # Zero hallucination — strict fact-checking
                max_tokens=1024,
            )

            # ── Tool Stack ─────────────────────────────────────
            self.tools = self._build_tools()

            # ── Prompt (ReAct) ─────────────────────────────────
            self.prompt = hub.pull("hwchase17/react")

            # ── Agent + Executor ───────────────────────────────
            agent = create_react_agent(self.llm, self.tools, self.prompt)
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=settings.AGENT_MAX_ITERATIONS,  # BUG-04 fixed
            )

            self._initialized = True
            tool_names = [t.name for t in self.tools]
            log.info(
                f"[Agent] ✅ Llama 3.1 8B + Triple-Tool Engine armed. "
                f"Tools: {tool_names} | max_iter={settings.AGENT_MAX_ITERATIONS}"
            )

        except Exception as e:
            log.error(f"[Agent] ❌ Engine Initialization Failed: {e}")
            self._initialized = False

    # ── Investigation Runner ───────────────────────────────────
    async def run_investigation(self, query: str, evidence_context: str = "") -> str:
        """
        Runs a deep-dive investigation into a claim using the triple-tool stack.

        Reasoning loop (ReAct):
          Thought → Action (tool call) → Observation (tool result) → repeat
          Up to settings.AGENT_MAX_ITERATIONS cycles before forced conclusion.
        """
        self._init_agent()

        if not self._agent_executor:
            return self._template_synthesis(query, evidence_context)

        # Build a dynamic tool manifest so the agent always knows what it has
        tool_manifest = "\n".join(
            [f"  • {t.name}: {(t.description or '').strip()[:100]}" for t in self.tools]
        )

        agent_input = (
            f"You are a professional fact-checker. Verify this NEWS CLAIM: {query}\n\n"
            f"PRE-FETCHED EVIDENCE (from initial pipeline search):\n"
            f"{evidence_context}\n\n"
            f"YOUR AVAILABLE TOOLS:\n{tool_manifest}\n\n"
            f"STEP-BY-STEP INSTRUCTIONS:\n"
            f"1. Use duckduckgo_search to find verified news reports from 2026.\n"
            f"2. IGNORE results from jewelry brands, shopping sites, or viral videos.\n"
            f"3. If a search result URL looks relevant but its SNIPPET IS TOO SHORT, "
            f"   use the process_url tool to read the FULL article text.\n"
            f"   Format: process_url('https://example.com/article-url')\n"
            f"4. If DuckDuckGo returns poor, noisy, or irrelevant results, "
            f"   switch to tavily_news_search as your backup.\n"
            f"5. Prioritize reputable outlets: Reuters, AP News, BBC, PTI, The Hindu, Livemint.\n"
            f"6. Issue a clear VERDICT: True, False, or Mixed.\n"
            f"7. MANDATORY: Cite the full source URL for every fact in your final answer."
        )

        async def _call():
            # BUG-03 fixed: get_running_loop() is Python 3.10+ safe
            # Runs synchronous LangChain invoke in a thread pool (async-compatible)
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                lambda: self._agent_executor.invoke({"input": agent_input}),
            )

        try:
            result = await circuit_agent.call(_call)

            if result is None:
                return self._template_synthesis(query, evidence_context)

            output = result.get("output", "")

            if not output or len(output) < 30:
                return (
                    "No conclusive evidence found in news archives to verify this claim."
                )

            return output

        except Exception as e:
            log.error(f"[Agent] ❌ Investigation execution failed: {e}")
            return self._template_synthesis(query, evidence_context)

    # ── Fallback ───────────────────────────────────────────────
    def _template_synthesis(self, query: str, evidence: str = "") -> str:
        """Graceful fallback synthesis when the reasoning engine is unavailable."""
        summary = evidence[:300] if evidence else "No direct evidence found."
        return (
            f"VERDICT: PRELIMINARY ASSESSMENT\n\n"
            f"Reasoning: The deep-check engine is currently unavailable. "
            f"Initial data snippet: {summary}..."
        )


# ── Singleton export for the orchestrator ─────────────────────
cawncade_agent = CawncadeAgent()