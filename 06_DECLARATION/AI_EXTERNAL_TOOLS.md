# AI_EXTERNAL_TOOLS.md

## Tool & Assistance Declaration

In accordance with the EDURANKAI evaluation rubric (Section 10), this document transparently declares all external AI models, APIs, libraries, data sources, and assistance utilized in the development and evaluation of this system.

### 1. Foundation Models & Inference APIs
- **Groq API (`openai/gpt-oss-120b`)**: Utilized as the primary Generative LLM for the Corrective RAG (CRAG) Evaluator Node and Synthesis Node. Selected for its exceptionally low latency (LPU inference), enabling rapid real-time multi-document evaluation during the web search fallback process. 
- **Sentence-Transformers (`all-MiniLM-L6-v2`)**: Utilized locally via HuggingFace for dense vector retrieval. Converts incoming claims and cached evidence into 384-dimensional embeddings for local FAISS similarity search.
- **Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`)**: Utilized locally to re-rank keyword (BM25) and dense (FAISS) retrieval results to ensure the most semantically relevant evidence blocks are fed to the CRAG LLM.

### 2. External APIs & Web Scraping
- **DuckDuckGo Search (HTML/Lite)**: Used as the primary tier-1 search fallback when local semantic cache misses occur.
- **Jina AI Reader API (`r.jina.ai`)**: Used to convert raw HTML web pages into clean Markdown for LLM ingestion, vastly reducing token consumption and stripping noise.
- **Google News RSS**: Used as an early-stopping high-trust news source for contemporary claims.

### 3. Core Libraries & Architecture
- **FastAPI & Uvicorn**: The asynchronous Python backend framework processing the multi-threaded search workflows.
- **Pydantic**: Used extensively to enforce strict typed JSON schemas for all LLM inputs and outputs, serving as a prompt-injection shield.
- **Tenacity**: Implemented for exponential backoff and retry logic when external APIs (e.g., Groq rate limits, Jina 500 errors) fail.
- **SQLAlchemy (SQLite)**: Used to persist the Semantic Cache, saving embeddings to avoid redundant LLM/Network calls for previously verified claims.

### 4. Code & Research Assistance
- **AI Coding Assistant (Antigravity/LLM)**: Used as a pair-programming partner to help debug complex asynchronous loop failures, refactor the LangChain prototype into a Native Python State Machine, and write regex parsers to cleanly extract JSON from markdown code blocks during Groq API integration.
- *Disclaimer*: All architectural decisions, prompt engineering, CRAG workflow design, and evaluation metric definitions were strictly manually directed, tested, and verified to ensure full comprehension and ownership of the system's execution path.
