# SKILLS PROTOCOL: TOOL EXECUTION MANUAL
# CONFIGURATION: CLEAR STYLE

## 1. CONCISE TOOL SELECTION
- Use `duckduckgo_search` as your primary weapon for breaking news, social trends, and general assertions.
- Use `process_url` exclusively when a search snippet looks relevant but is too short to verify the claim. This reads the FULL article text (bypassing paywalls).
- Use `tavily_news_search`, `serper_search`, or `you_search` (if available) as explicit fallback options to gather broader context.

## 2. LOGICAL QUERY FORMULATION
- Strip out conversational fluff (e.g., do NOT search "is it true that the sky is green").
- Isolate nouns, entities, dates, and actions into dense keyword arrays (e.g., "sky color Rayleigh scattering anomalies").
- Always append "latest news" to your DuckDuckGo queries to prioritize fresh, reputable reporting over noisy SEO pages.

## 3. EXPLICIT FALLBACK ROUTING
- If a tool encounters a network drop, timeout, or rate limit block, or returns 0 results, you must immediately pivot to an alternative tool.
- If DuckDuckGo returns nothing useful, seamlessly execute a Tavily or Serper fallback query. Do not throw an exception to the user.

## 4. ACTIONABLE DATA SCRAPING
- When analyzing a direct URL payload via `process_url`, scan specifically for hard evidence, dates, official statements, and statistical figures.
- Ignore marketing jargon, cookie notices, and navigation text returned by parsing scripts.

## 5. RELEVANT ANCHORING
- Match your search tool actions directly to the input context types. Prioritize reputable outlets (e.g., Reuters, AP News, BBC).
- Ignore results from jewelry brands, shopping sites, or viral video descriptions unless specifically analyzing a product/video claim.
