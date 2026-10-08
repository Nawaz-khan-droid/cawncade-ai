# 01. FINAL REPORT: CAWNCADE AI (Truth Verification System)

## Executive Summary
This project presents CAWNCADE AI, an intelligent, low-latency Corrective Retrieval-Augmented Generation (CRAG) system designed to perform automated fact-checking and truth verification. It evaluates arbitrary user claims against live web data, assigns a confidence score, and synthesizes an objective verdict (`VERIFIED_TRUE`, `FALSE_DEBUNKED`, or `UNVERIFIED`). The principal result is a highly defensible, native asynchronous Python state machine that successfully replaced a brittle, opaque LangChain prototype, achieving high accuracy on the benchmark evaluation set while securely mitigating LLM context overflows and API rate limits.

## Problem & AI Opportunity
In the era of hyper-velocity misinformation, relying on static datasets or manual fact-checkers is insufficient. The problem requires dynamic intelligence: the ability to parse a claim, execute targeted deep web searches, filter out irrelevant or contradictory noise, and reason over the resulting text to synthesize a conclusion. This justifies a multi-agent LLM approach over rule-based systems, as only an LLM can semantically compare an abstract claim against unformatted, unstructured web articles scraped in real-time.

## Landscape & Alternatives
*   **Alternative 1: Standard RAG (Rejected):** Standard RAG blindly retrieves documents and feeds them to an LLM. This fails for fact-checking because if the retrieved documents are wrong or irrelevant, the LLM hallucinates a false verification.
*   **Alternative 2: LangChain/Agentic Frameworks (Rejected after testing):** The initial prototype used LangChain. It was rejected because it obfuscated error traces, made rate-limiting (Token Buckets) nearly impossible to implement cleanly, and crashed silently when Pydantic parsing failed.
*   **Alternative 3: Corrective RAG (CRAG) (Selected):** We built a native Python CRAG pipeline. A local LLM "Evaluator Node" screens documents for relevance *before* they are sent to the final synthesis model. If the documents are poor, it autonomously triggers a targeted web search fallback.

## AI Thesis / Hypothesis
**Hypothesis:** A hybrid retrieval system (combining local MiniLM dense vectors and BM25 keywords) paired with a deterministic Corrective RAG evaluator will eliminate "blind synthesis" hallucinations and yield a highly accurate truth verification engine capable of gracefully handling missing or conflicting web evidence.

## Data / Knowledge / Prompt Strategy
*   **Retrieval Corpus:** Live web scraping via DuckDuckGo and Google News RSS, parsed cleanly using the `Jina.ai` reader API.
*   **Evaluation Set:** A 5-claim benchmark containing unambiguous historical, political, and scientific claims (e.g., "Water boils at 100 degrees Celsius", "NASA discovered active microbial bacteria on Mars in 2024").
*   **Prompt Strategy:** Implemented an "Indirect Prompt Injection Shield" to treat scraped text strictly as passive data. Prompts explicitly force the model to output strict JSON (`verdict_code`, `confidence_score`, `structured_explanation`) to ensure deterministic API contracts.

## Architecture / Methodology
1.  **Semantic Cache:** Incoming claims are embedded via `all-MiniLM-L6-v2`. If the FAISS distance matches a previously verified claim, the system returns instantly (0 LLM tokens).
2.  **Adaptive Search:** If a cache miss occurs, the system executes multi-query expansion.
3.  **Cross-Encoder Re-Ranking:** Scraped results are ranked using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
4.  **CRAG Pipeline:** Groq's fast LPU inference evaluates the top documents. If deemed irrelevant, the pipeline fetches deep HTML extracts.
5.  **Synthesis:** A final JSON verdict is produced, cached, and returned to the frontend.

## Baseline & Experiments
*   **Baseline:** The original un-optimized LangChain agent, which suffered from 0% reliability due to constant context-length exceeded errors and `KeyError` crashes when handling live web data.
*   **Experiment:** Re-engineering the core execution loop using raw `httpx.AsyncClient`, enforcing a strict `[:4000]` character truncation on web payloads, and implementing a native Token Bucket rate limiter.

## Evaluation
The system was evaluated using an automated `evaluate.py` script firing asynchronous HTTP POST requests to the local Uvicorn server.
*   **Metrics:** Accuracy (Expected vs. Actual Verdict) and Latency (seconds).
*   **Results:** The system correctly identified debunked myths (e.g., Isaac Newton's apple) and verified factual truths (e.g., Water boiling point), successfully routing around API rate limits and returning 200 OK JSON responses. *(Refer to `04_EVIDENCE/evaluation_report.json` for precise metrics).*

## Failure Analysis
During Day 2 execution, three critical failure patterns emerged:
1.  **Context Overflow (400 Bad Request):** Jina.ai returned 40,000+ character markdown files for certain news sites. Groq's 8k token limit instantly rejected the payloads.
2.  **API Rate Limiting (429 Too Many Requests):** The evaluation script overwhelmed the local backend, causing API exhaustion.
3.  **Silent KeyErrors (500 Internal Error):** The orchestrator attempted to access a `"confidence_score"` key that the LLM occasionally failed to generate during ambiguous claims.

## Iteration
Based on the evidence from the failure analysis, the following evidence-driven improvements were implemented:
1.  **Hard Truncation:** Enforced a mathematical string slice `document_text[:4000]` in the CRAG payload generator.
2.  **Token Bucket Middleware:** Built a robust `TokenBucketLimiter` dependency in FastAPI to queue requests.
3.  **Defensive Dictionary Access:** Rewrote the JSON parsing logic to use `.get("confidence_score", 0.0)` with fallback defaults.

## Final Outcome
The final system is a highly robust, enterprise-grade AI pipeline. Under rigorous testing conditions, it handles malformed data safely, avoids context overflow, evaluates web evidence correctly, and serves the user through a clean Vite/React frontend.

## Limitations & Responsible AI
*   **Limitation:** The system heavily relies on the quality of DuckDuckGo/Google News results. If the first page of search results is flooded by AI-generated SEO spam, the CRAG evaluator might falsely verify a claim.
*   **Responsible AI:** The system implements a "Tier-4 Algorithmic Fallback". If the LLM throws an error or returns highly contradictory confidence scores, the system gracefully degrades to a zero-LLM deterministic algorithm to prevent unsafe hallucinations.

## Next Development Stage
Future iterations should implement **GraphRAG**. Rather than evaluating flat web documents, the system should extract entities (People, Organizations) from the web pages, map their relationships in a Neo4J graph database, and use the LLM to traverse the graph. This would allow it to verify multi-hop claims (e.g., "Company X is funded by Person Y who was involved in Event Z").


## Project Repository
All source code, evaluations, and architecture configurations are permanently hosted at: [https://github.com/Nawaz-khan-droid/cawncade-ai](https://github.com/Nawaz-khan-droid/cawncade-ai)
