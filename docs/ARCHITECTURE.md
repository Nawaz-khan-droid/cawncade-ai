# CAWNCADE AI — Living Project Architecture Documentation

**Context Aware Watch News Confirmation Authenticity Detection Engine (v3.5)**  
*Single Source of Truth for Application Architecture, Verification Pipelines, Security Model, LLM Routing, and Testing Strategy.*

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Global System Architecture](#2-global-system-architecture)
3. [Decoupled Input Pipeline Architectures](#3-decoupled-input-pipeline-architectures)
   - [3.1 Global Input Classifier Router](#31-global-input-classifier-router)
   - [3.2 ContextLens Pipeline (Text & URLs)](#32-contextlens-pipeline-text--urls)
   - [3.3 VisualLens Pipeline (Images & Forensics)](#33-visuallens-pipeline-images--forensics)
   - [3.4 YouTube Pipeline (Dual-Stream Transcripts)](#34-youtube-pipeline-dual-stream-transcripts)
4. [Extraction Result State Machine](#4-extraction-result-state-machine)
5. [Backend Architecture](#5-backend-architecture)
6. [Frontend Architecture](#6-frontend-architecture)
7. [LLM Provider Architecture](#7-llm-provider-architecture)
8. [Extraction Architecture](#8-extraction-architecture)
9. [Security Architecture](#9-security-architecture)
10. [Rate Limiting & Resilience Architecture](#10-rate-limiting--resilience-architecture)
11. [Verification Matrix](#11-verification-matrix)
12. [User Use Cases](#12-user-use-cases)
13. [Deployment Architecture](#13-deployment-architecture)
14. [Performance & Latency Budget](#14-performance--latency-budget)
15. [Architecture Update Policy](#15-architecture-update-policy)

---

## 1. Project Overview

CAWNCADE AI is a multi-tiered, fault-tolerant news verification platform and claim-analysis engine. It cross-references user claims, news URLs, YouTube videos, and images against multi-vector web sources, historical fact-check databases, domain trust registries, and an autonomous ReAct AI reasoning agent.

### Supported Inputs
- **Text Claims**: Raw text statements, news excerpts, or viral social media posts (Up to 5,000 characters).
- **Article URLs**: News article links validated against SSRF protection rules and parsed via a hybrid extraction pipeline.
- **YouTube URLs**: YouTube video links processed via dual-stream API and transcript extraction (`youtube_service.py`).
- **Images**: Visual files analyzed via HuggingFace Inference API vision models (ViT/SigLIP2) and local OCR pre-processing (`image_service.py`).

### Verified Tech Stack (Codebase Reality Audit)
- **Frontend**: React 18, Vite, Tailwind CSS, Framer Motion, Lucide Icons.
- **Backend**: FastAPI (Python 3.11), Uvicorn, Pydantic v2.
- **Extraction Engine**: Jina Reader API (Primary) + `httpx` / `BeautifulSoup4` (Secondary Fallback).
- **LLM Reasoning Cascade**:
  1. Tier 1: OpenRouter (`nvidia/nemotron-3-super-120b-a12b:free`)
  2. Tier 2: HuggingFace Router Groq (`meta-llama/Llama-3.3-70B-Instruct:groq`)
  3. Tier 3: HuggingFace Router DeepInfra (`google/gemma-3-27b-it:deepinfra`)
  4. Tier 4: Offline No-LLM Mode (Local Extractive LexRank NLP + Entity Extraction via `sumy` & `extract_local_entities`)
- **Semantic Vector Cache**: FAISS (`faiss-cpu`) + `sentence-transformers/all-MiniLM-L6-v2` (`app/services/cache_service.py`).
- **Resilience**: Custom state-machine CircuitBreaker (`app/core/resilience.py`), Tenacity exponential backoff retries.

---

## 2. Global System Architecture

```mermaid
flowchart TD
    User([User / Web Browser]) <-->|HTTPS / REST API| Frontend[React 18 + Vite SPA]
    Frontend <-->|JSON / Axios API| Backend[FastAPI Backend - Port 8000/7860]
    
    subgraph FastAPI Backend
        Routes[API Routes: /api/v1/analyze, /analyze/image, /chat]
        Orchestrator[Pipeline Orchestrator]
        
        subgraph Safety & Extraction
            SSRF[SSRF Post-DNS Guard]
            SafeBrowse[Google Safe Browsing]
            Jina[Jina Reader Primary: r.jina.ai]
            BS4[httpx + BeautifulSoup Fallback]
        end
        
        subgraph Research & Search Stack
            Tier0[Tier 0: Dictionary Matcher]
            TierCache[FAISS Vector Cache: IndexFlatIP 384d]
            FactCheck[Pre-Flight: Google Fact Check API]
            SearchTiers[7-Tier Search: Serper -> Tavily -> You.com -> NewsData -> RSS -> Google CSE -> DDG]
        end
        
        subgraph AI Agent Reasoning
            Agent[LangChain ReAct Agent]
            LLMRouter[4-Tier Router: Nemotron 120B -> Groq 70B -> DeepInfra 27B -> Local LexRank NLP]
        end
        
        Scorer[CAWNCADE Multi-Factor Scorer]
    end
    
    Routes --> Orchestrator
    Orchestrator --> SSRF
    SSRF --> Jina
    SSRF --> BS4
    Orchestrator --> Tier0
    Orchestrator --> TierCache
    Orchestrator --> FactCheck
    Orchestrator --> SearchTiers
    Orchestrator --> Agent
    Agent --> LLMRouter
    Orchestrator --> Scorer
```

---

## 3. Decoupled Input Pipeline Architectures

### 3.1 Global Input Classifier Router

```
                 User Input
                     |
                     ↓
            Input Classifier (orchestrator.py)
                     |
        +------------+------------+------------------+
        |                         |                  |
    Text Claim                Article URL        Image Upload / YouTube
        |                         |                  |
        ↓                         ↓                  ↓
  ContextLens              SSRF Security Guard   VisualLens
 (Direct Analysis)                |             (OCR / Vision Model)
                                  ↓
                        Hybrid Extractor
                        (Jina -> BS4 Fallback)
```

---

### 3.2 ContextLens Pipeline (Text & URLs)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as ContextLens.jsx
    participant API as FastAPI (/api/v1/analyze)
    participant Orch as Orchestrator
    participant SSRF as SSRF Guard
    participant Ext as ContentExtractor
    participant Search as Tiered Search Stack
    participant LLM as 4-Tier LLM Router
    participant UI as ResultHero + SourceCard

    User->>FE: Submits Text Claim or News URL
    FE->>API: POST /api/v1/analyze {input_text: input, input_type: "auto"}
    API->>API: Validate Pydantic Schema (maxLength=5000)
    API->>Orch: orchestrator.process(input)
    alt URL Input
        Orch->>SSRF: is_ssrf_safe_url(url)
        SSRF->>SSRF: socket.getaddrinfo IPv4/v6 DNS Check
        alt Unsafe IP
            SSRF-->>Orch: Blocked (Private/Loopback IP)
            Orch-->>FE: Return status: BLOCKED
        else Safe IP
            SSRF-->>Orch: Safe
            Orch->>Ext: extract_from_url(url)
            Ext-->>Orch: Clean Text (Jina or BS4 fallback)
        end
    end
    Orch->>Search: tiered_search(query)
    Search-->>Orch: Web Citations
    Orch->>LLM: run_investigation(query, evidence)
    LLM-->>Orch: Synthesis (Nemotron 120B / Groq 70B / DeepInfra 27B / Local LexRank)
    Orch->>FE: Payload + system_metadata
    FE->>User: Render ResultHero + SourceCard
```

---

### 3.3 VisualLens Pipeline (Images & Forensics)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as VisualLens.jsx
    participant API as FastAPI (/api/v1/analyze/image)
    participant Orch as Orchestrator
    participant Vis as Vision Service (vision_service.py)
    participant Img as Image Service (image_service.py)
    participant LLM as 4-Tier LLM Router

    User->>FE: Uploads Image File (Base64)
    FE->>API: POST /api/v1/analyze/image {image_base64: b64, user_query: q}
    API->>Orch: orchestrator.process_image(b64)
    Orch->>Img: extract_image_evidence(img_bytes)
    Img->>Img: OCR Text Extraction (pytesseract) + EXIF Metadata
    Img-->>Orch: {ocr_text, metadata_context}
    Orch->>Vis: analyze_image(b64)
    Vis->>Vis: Call HF Inference API (ViT/SigLIP2 Model)
    Vis-->>Orch: {label: "AI-GENERATED/DEEPFAKE", confidence: 0.94}
    Orch->>LLM: run_investigation(ocr_text, image_metadata)
    LLM-->>Orch: Visual Forensic Explanation
    Orch->>FE: 5-Card Forensics Payload
    FE->>User: Render Deepfake Badge, EXIF Details & OCR Evidence
```

---

### 3.4 YouTube Pipeline (Dual-Stream Transcripts)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as VisualLens.jsx / ContextLens.jsx
    participant API as FastAPI (/api/v1/analyze)
    participant Orch as Orchestrator
    participant YT as YouTube Service (youtube_service.py)
    participant LLM as 4-Tier LLM Router

    User->>FE: Submits YouTube URL
    FE->>API: POST /api/v1/analyze {input_text: yt_url, input_type: "youtube"}
    API->>Orch: orchestrator.process(yt_url)
    Orch->>YT: analyze_youtube(yt_url)
    YT->>YT: Stream 1: YouTube Data API (Metadata)
    YT->>YT: Stream 2: youtube_transcript_api / Scraper (Captions)
    YT-->>Orch: {title, channel, transcript, api_stream, scraper_stream}
    Orch->>LLM: run_investigation(transcript[:2000], evidence)
    LLM-->>Orch: Synthesis of Video Claims
    Orch->>FE: Return Structured JSON Result
    FE->>User: Render ResultHero + Video Transcript Highlights
```

---

## 4. Extraction Result State Machine

Instead of crashing or returning opaque `500` errors, CAWNCADE classifies extraction outcomes into structured state codes:

| State Code | Trigger Condition | System Behavior | User-Facing UI Message |
| :--- | :--- | :--- | :--- |
| **`SUCCESS`** | Article text extracted cleanly (>=1000 chars). | Proceeds directly to LLM & 3-Way Evidence Compression. | Rendered in dominant `ResultHero` card. |
| **`PAYWALL`** | HTTP 401/403/451 or subscription wall detected. | Engages slug keyword extraction + web search citations. | `⚠️ Article restricted by paywall. Verification performed via multi-source web citations.` |
| **`TIMEOUT`** | Server connection > 15 seconds. | Aborts fetch; falls back to search evidence. | `⚠️ Target website did not respond within 15 seconds. Using web search citations.` |
| **`BLOCKED`** | SSRF Guard intercepts private/loopback IP. | Blocks request before network connection. | `❌ Security Warning: Target URL is restricted from server-side fetching.` |
| **`INVALID_URL`**| Malformed string or non-HTTP(S) scheme. | Prompts user or treats input as plain text claim. | `❌ Invalid URL format. Please paste a valid news article URL.` |
| **`NO_CONTENT`** | Body tag empty or script-only page. | Engages Jina Reader or prompts for raw text paste. | `⚠️ Unable to extract article text. Please paste the article text directly.` |

---

## 5. Backend Architecture

### Directory Structure
```
backend/app/
├── api/
│   └── routes/
│       ├── admin.py         # System health & telemetry endpoints
│       ├── analysis.py      # Core analysis routes (/analyze, /analyze/image, /feedback)
│       └── auth.py          # Authentication routes
├── config/
│   └── settings.py          # Type-safe environment settings (Pydantic BaseSettings)
├── core/
│   ├── cache.py             # Global memory cache
│   ├── orchestrator.py      # Master pipeline coordinator with system_metadata tracking
│   ├── rate_limiter.py      # Sliding window rate limiter
│   ├── resilience.py        # Custom state-machine CircuitBreaker (CLOSED->OPEN->HALF_OPEN)
│   ├── security.py          # JWT authentication helpers
│   └── trusted_domains.py   # Walled garden domain registry (50+ trusted sites)
├── modules/
│   ├── extraction/          # Web scraping & URL extraction (ContentExtractor)
│   ├── ranking/             # Source trust ranker
│   ├── retrieval/           # Search retrievers
│   ├── scoring/             # Multi-factor score engine
│   └── text/                # Embedding & TF-IDF modules
├── services/
│   ├── agent_service.py     # ReAct LLM agent & 4-tier provider router (with telemetry)
│   ├── cache_service.py     # FAISS CPU vector cache (SentenceTransformers)
│   ├── dictionary_matcher.py# Tier 0 local viral claim cache
│   ├── fact_check_service.py# Google Fact Check API integration
│   ├── news_service.py      # 7-Tier web search engine (Serper, Tavily, DDG, RSS, GDELT)
│   ├── safe_browsing_service.py # Google Safe Browsing & SSRF DNS guard
│   ├── vision_service.py    # HF Inference ViT/SigLIP2 deepfake analysis
│   └── youtube_service.py   # YouTube API & transcript scraper
└── utils/
    ├── helpers.py           # Recency & date helpers
    └── logger.py            # Structured logging
```

---

## 6. Frontend Architecture

### Component Hierarchy
```
frontend/src/
├── components/
│   ├── ui/
│   │   ├── ResultHero.jsx   # Dominant verdict card with verdict-specific themes & left stripe
│   │   ├── SourceCard.jsx   # 4-state Lucide finding badge source card (break-words enabled)
│   │   ├── SectionCard.jsx  # Glass container primitive
│   │   ├── LoadingState.jsx # Animated step-by-step skeleton loaders
│   │   ├── EmptyState.jsx   # 0-result empty state callouts
│   │   ├── ErrorState.jsx   # Inline error callout with focus-ring retry button
│   │   └── Logo.jsx         # Application branding SVG
│   ├── ContextSynthesis.jsx # Analysis summary renderer (DOMParser HTML sanitized)
│   ├── Header.jsx           # Global navigation header
│   └── FooterDisclaimer.jsx # Regulatory disclaimer footer
├── pages/
│   ├── ContextLens.jsx      # Claim & URL analysis screen (with live color-coded char counter)
│   ├── VisualLens.jsx       # 5-Card Image forensics & YouTube analysis screen
│   ├── AgentChat.jsx        # Conversational agent interface
│   └── Home.jsx             # Hero landing page & Bento grid
├── context/
│   ├── PipelineContext.jsx  # Global pipeline state manager
│   └── ThemeContext.jsx     # Dark / Light theme toggle
└── services/
    └── api.js               # Axios REST client with Vite proxy
```

---

## 7. LLM Provider Architecture

CAWNCADE AI implements a 4-tier fault-tolerant LLM router cascade:

```mermaid
flowchart LR
    Request[Agent Prompt] --> Tier1{Tier 1: OpenRouter}
    Tier1 -->|Success| Nemotron[NVIDIA Nemotron 3 Super 120B Free]
    Tier1 -->|Fail / Timeout| Tier2{Tier 2: HF Router Groq}
    Tier2 -->|Success| GroqLlama[Llama 3.3 70B via Groq LPU]
    Tier2 -->|Fail / Timeout| Tier3{Tier 3: HF Router DeepInfra}
    Tier3 -->|Success| Gemma27B[Gemma 3 27B via DeepInfra]
    Tier3 -->|Fail / Timeout| Tier4[Tier 4: Offline No-LLM Mode - LexRank NLP]
```

### Provider Cascade Policy
- **Primary (Tier 1)**: OpenRouter `nvidia/nemotron-3-super-120b-a12b:free` for high-parameter multi-step ReAct reasoning.
- **Fallback 1 (Tier 2)**: Hugging Face Router Meta Llama 3.3 70B Instruct via Groq LPU engine.
- **Fallback 2 (Tier 3)**: Hugging Face Router Google Gemma 3 27B via DeepInfra engine.
- **Fallback 3 (Tier 4)**: Local CPU Extractive NLP (`sumy` LexRank + `extract_local_entities`) when all online LLM endpoints are unreachable.

### Telemetry Metadata Payload (`system_metadata`)
Every response payload includes diagnostic telemetry tracking execution details:

```json
{
  "system_metadata": {
    "model_used": "nvidia/nemotron-3-super-120b-a12b:free",
    "llm_tier": "tier_1_openrouter",
    "fallback_used": false,
    "latency_ms": 4200
  }
}
```

---

## 8. Extraction Architecture

### Hybrid Extraction Decision Tree

```mermaid
flowchart TD
    URL[Input Article URL] --> SSRF{is_ssrf_safe_url?}
    SSRF -->|Unsafe| Block[Security Block: status = BLOCKED]
    SSRF -->|Safe| Jina[Try Jina Reader API: r.jina.ai/url]
    
    Jina --> JinaCheck{Status 200 & Chars >= 1000?}
    JinaCheck -->|YES| CleanJina[Method: jina_reader]
    JinaCheck -->|NO / Timeout| BS4[Secondary Fallback: httpx + BeautifulSoup]
    
    BS4 --> SizeCheck{Response Size <= 5MB?}
    SizeCheck -->|NO| SizeCap[Abort: 5MB Byte Cap Exceeded]
    SizeCheck -->|YES| ParseBS4[Strip script/style/nav/footer -> Clean Text]
    
    CleanJina --> Compression[Apply 3-Way Compression: First 3k + Middle 4k + Last 3k]
    ParseBS4 --> Compression
    Compression --> Payload[Structured Payload: status, keywords, text]
```

---

## 9. Security Architecture

### Security Matrix

| Security Layer | Implementation Status | Implementation Location | Mitigation Target |
| :--- | :--- | :--- | :--- |
| **SSRF Post-DNS Guard** | ✅ Implemented | `safe_browsing_service.py::is_ssrf_safe_url` | Resolves IPv4/v6 via `socket.getaddrinfo()`; blocks `localhost`, `169.254.169.254`, & private subnets. |
| **Pydantic Validation** | ✅ Implemented | `analysis.py::AnalyzeRequest` | Blocks buffer overflow and oversized payloads at HTTP entry (`max_length=5000`). |
| **Response Size Cap** | ✅ Implemented | `extractor.py::extract_from_url` | Aborts HTTP streaming if response body exceeds 5MB (`MAX_RESPONSE_BYTES`). |
| **Prompt Injection Guard**| ✅ Implemented | `agent_service.py::run_investigation` | Prevents malicious web text from overriding LLM instructions. |
| **DOMParser Sanitization**| ✅ Implemented | `ContextSynthesis.jsx` | Sanitizes LLM HTML output before browser DOM insertion. |
| **Rate Limiting** | ✅ Implemented | `rate_limiter.py::SlidingWindowRateLimiter` | Restricts clients to 30 requests per minute. |
| **CORS Policy** | ✅ Implemented | `main.py::CORSMiddleware` | Restricts API access to authorized frontend origins. |
| **CSRF Protection** | 🔮 Future Requirement| `auth.py` | Needed when cookie-based session auth is introduced. |

---

## 10. Rate Limiting & Resilience Architecture

### Timeout & Circuit Breaker Matrix

CAWNCADE uses a custom `CircuitBreaker` class (`app/core/resilience.py`) with `CLOSED -> OPEN -> HALF_OPEN` states to isolate unhealthy endpoints.

| Operation | Service / Library | Timeout | Circuit Breaker | Failure Fallback |
| :--- | :--- | :--- | :--- | :--- |
| **DNS Resolution** | `socket.getaddrinfo` | 5.0s | N/A | Returns `BLOCKED` status immediately. |
| **Jina Reader Fetch** | `httpx.AsyncClient` | 15.0s | N/A | Fallback to `httpx` + `BeautifulSoup`. |
| **HTTP Fallback Fetch**| `httpx.AsyncClient` | 15.0s | N/A | Fallback to URL slug keyword search. |
| **Google Safe Browsing**| `httpx.AsyncClient` | 10.0s | `circuit_safe_browsing` | Returns `safe: True` with warning log. |
| **Tiered Web Search** | `news_service.py` | 15.0s | `circuit_google_search`, `circuit_tavily` | Cascades through 7 search tiers. |
| **ReAct LLM Investigation**| `CawncadeAgent` | 30.0s | `circuit_agent` | Fallback to LexRank Extractive NLP (`sumy`). |

---

## 11. Verification Matrix

| Component / Feature | Code Location | Verified Test Suite | Expected Production Output |
| :--- | :--- | :--- | :--- |
| **SSRF Post-DNS Guard** | [safe_browsing_service.py](file:///C:/Users/ks919/Downloads/CAWNCADE%20AI/backend/app/services/safe_browsing_service.py#L20-L50) | Input `http://localhost:8000/admin` | Returns `(False, "Security Block: Access to local network prohibited.")` |
| **Jina Primary Extractor** | [extractor.py](file:///C:/Users/ks919/Downloads/CAWNCADE%20AI/backend/app/modules/extraction/extractor.py#L34-L65) | URL submit via ContextLens | `method: "jina_reader"`, text >= 1000 chars, status: `SUCCESS` |
| **5MB Response Byte Cap** | [extractor.py](file:///C:/Users/ks919/Downloads/CAWNCADE%20AI/backend/app/modules/extraction/extractor.py#L70-L85) | Stream byte count check | Aborts download if > 5MB; returns size cap warning. |
| **FAISS Vector Cache** | [cache_service.py](file:///C:/Users/ks919/Downloads/CAWNCADE%20AI/backend/app/services/cache_service.py#L60-L90) | Submit identical claim | `< 50ms` Instant Cache Hit with `confidence_label: "CACHED"` |
| **Tier 4 Offline No-LLM** | [orchestrator.py](file:///C:/Users/ks919/Downloads/CAWNCADE%20AI/backend/app/core/orchestrator.py#L35-L53) | [test_tier4_fallback.py](file:///C:/Users/ks919/Downloads/CAWNCADE%20AI/backend/tests/test_tier4_fallback.py) | `model_used: "local_lexrank_nlp"`, extracted key sentences + detected entities |
| **Deepfake Detection** | [vision_service.py](file:///C:/Users/ks919/Downloads/CAWNCADE%20AI/backend/app/services/vision_service.py#L16-L65) | Image upload via VisualLens | `normalized: "AI-GENERATED/DEEPFAKE"` with score confidence % |
| **YouTube Transcript** | [youtube_service.py](file:///C:/Users/ks919/Downloads/CAWNCADE%20AI/backend/app/services/youtube_service.py#L15-L60) | YouTube URL submit | Dual-stream API + Scraper transcript text extraction |

---

## 12. User Use Cases

### Use Case 1: Checking a Text Claim
- **Actor**: Public User / Journalist
- **Input**: Text statement entered in ContextLens (`maxLength=5000`).
- **Flow**: Frontend -> FastAPI `/api/v1/analyze` -> FAISS Vector Cache -> Google Fact Check -> Tiered Search -> Scoring -> ReAct Agent -> UI.
- **Output**: Dominant `ResultHero` verdict, Analysis Summary, and Source Cards.

### Use Case 2: Submitting an Article URL
- **Actor**: User verifying a suspicious news link.
- **Input**: URL string (`https://example.com/news`).
- **Flow**: SSRF Guard -> Jina Reader Primary -> 3-Way Compression -> Tiered Search -> ReAct Agent -> UI.
- **Output**: Verified findings and source domain trust ratings.

### Use Case 3: Uploading an Image for Forensics
- **Actor**: User verifying a visual file.
- **Input**: Image upload or YouTube link in VisualLens.
- **Flow**: Base64 decode -> OCR text extraction (pytesseract) + SigLIP2 deepfake analysis -> Orchestrator -> 5-Card Forensics UI.
- **Output**: Deepfake probability score, EXIF metadata, and visual reference matches.

---

## 13. Deployment Architecture

### Environments
- **Development**:
  - `ENVIRONMENT=development`
  - Frontend: `http://localhost:5173` (Vite dev server)
  - Backend: `http://localhost:8000` (Uvicorn reload)
- **Production (Hugging Face Spaces)**:
  - `ENVIRONMENT=production`
  - Docker container running on port 7860.
  - Persistent SQLite storage mounted to `/data/cawncade.db`.

---

## 14. Performance & Latency Budget

- **Instant Path (Cache Hit)**: `< 50ms` via FAISS CPU vector lookup (`app/services/cache_service.py`).
- **Fast Path (Cached Search + Direct LLM)**: `5 - 10 seconds`.
- **Standard Pipeline Path (Full Search + Jina Extraction + LLM)**: `10 - 20 seconds`.
- **Maximum Bound (Cascading LLM Router + Web Retries)**: `30 - 60 seconds`.
- **Memory Cap**: Stream caps enforce a strict **5MB limit** per HTTP request.

---

## 15. Architecture Update Policy

> ### ⚠️ ARCHITECTURE UPDATE POLICY
> **This document (`docs/ARCHITECTURE.md`) is a living specification.**  
> Whenever any of the following items are added, modified, or refactored in the repository:
> 1. API routes or Pydantic schemas (`app/api/routes/`)
> 2. LLM providers or prompt templates (`app/services/agent_service.py`)
> 3. Extraction algorithms or scraper tools (`app/modules/extraction/`)
> 4. Security layers or SSRF rules (`app/services/safe_browsing_service.py`)
> 5. Frontend component primitives or page layouts (`frontend/src/`)
> 
> **The developer or AI agent performing the update MUST update `docs/ARCHITECTURE.md` to reflect the changes prior to marking the task complete.**
