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
        if self._initialized: return
        
        try:
            # FLAN-T5 does not require gated approval
            repo_id = "google/flan-t5-large"
            api_token = settings.HUGGINGFACE_API_TOKEN or os.getenv("HUGGINGFACE_API_TOKEN")

            self.llm = HuggingFaceEndpoint(
                repo_id=repo_id,
                huggingfacehub_api_token=api_token,
                timeout=120,
                # FLAN-T5 works better with slightly different generation params
                extra_body={
                    "parameters": {
                        "max_new_tokens": 512,
                        "temperature": 0.1,
                    }
                }
            )

            # Standard DuckDuckGo Setup
            wrapper = DuckDuckGoSearchAPIWrapper(region="wt-wt", time=None, max_results=5)
            self.search_tool = DuckDuckGoSearchRun(api_wrapper=wrapper)

            # Pull the ReAct prompt
            self.prompt = hub.pull("hwchase17/react")
            
            # Create the agent
            agent = create_react_agent(self.llm, [self.search_tool], self.prompt)
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=[self.search_tool],
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5 
            )

            self._initialized = True
            log.info(f"[Agent] FLAN-T5 Large initialized as temporary reasoning engine.")

        except Exception as e:
            log.error(f"[Agent] FLAN-T5 Init Failed: {e}")
            self._initialized = True

    async def run_investigation(self, query: str, evidence_context: str = "") -> str:
        self._init_agent()
        
        if not self._agent_executor:
            return self._template_synthesis(query, evidence_context)

        # Build the reasoning prompt
        agent_input = (
            f"Answer the following claim using the provided evidence. "
            f"Search the internet if more info is needed. "
            f"Cite your sources accurately.\n\n"
            f"CLAIM: {query}\n"
            f"EVIDENCE: {evidence_context}"
        )

        async def _call():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self._agent_executor.invoke({"input": agent_input})
            )

        try:
            result = await circuit_agent.call(_call)
            output = result.get("output", "")
            
            if not output or len(output) < 20: # Lowered threshold for T5
                return self._template_synthesis(query, evidence_context)
                
            return output
        except Exception as e:
            log.error(f"[Agent] Execution failed: {e}")
            return self._template_synthesis(query, evidence_context)

    def _template_synthesis(self, query: str, evidence: str = "") -> str:
        return f"VERDICT: CANNOT ASSESS (Agent processing error)"

cawncade_agent = CawncadeAgent()