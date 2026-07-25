// A production-grade reactive data store using native features
class GlobalStore {
    constructor() {
        this._state = {
            page: 'landing', // 'landing' | 'dashboard'
            analysis: {
                isAnalyzing: false,
                result: null,
                input: {
                    text: '',
                    url: '',
                    image: null
                }
            }
        };
    }

    get state() {
        return this._state;
    }

    setPage(page) {
        this._state.page = page;
        this._broadcast('page-changed', { page });
    }

    updateInput(key, value) {
        this._state.analysis.input[key] = value;
        this._broadcast('input-changed', this._state.analysis.input);
    }

    clearInput() {
        this._state.analysis.input = { text: '', url: '', image: null };
        this._state.analysis.result = null;
        this._broadcast('input-changed', this._state.analysis.input);
        this._broadcast('analysis-changed', this._state.analysis);
    }

    async runAnalysis() {
        this._state.analysis.isAnalyzing = true;
        this._broadcast('analysis-changed', this._state.analysis);
        
        // Simulate network latency for ML inference
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        const hasImage = this._state.analysis.input.image !== null;
        
        this._state.analysis.result = {
            confidence: 0.72, 
            bias: 0.58, 
            conflict: 0.85, 
            sensitivity: 0.41, 
            aiRisk: 0.63, 
            recency: 0.29,
            summary: `**Analysis Summary — Context Reliability Report**\n\nThe submitted claim exhibits **high conflict signals** (85%) across retrieved sources, suggesting that major reputable outlets are presenting materially different narratives around the same event.\n\n**Key findings:**\n- **Reuters** and **BBC** both reference the underlying data, but apply contradictory interpretations regarding causality. This divergence is a strong indicator of *selective framing* rather than factual error.\n- The **AI-Risk score** (63%) is elevated, meaning portions of the circulating content show linguistic patterns consistent with LLM-generated text — though this is not conclusive.\n- **Source recency** is low (29%), indicating that most retrieved corroborating evidence is more than 72 hours old.\n\n**Entities identified:** European Central Bank [1], Bloomberg Markets [2], RT International [3]\n\n**Reliability assessment:** Exercise caution. Cross-reference with [1] and [2] before drawing conclusions. [3] carries significant credibility penalties.`,
            sources: [
                { id: 1, domain: 'reuters.com', credibility: 0.91, publishDate: '2026-07-24', isRecent: true, factCheckStatus: 'VERIFIED', fullText: 'Global economic indicators show mixed signals as central banks adjust forward guidance amid persistent inflation uncertainty. Analysts diverge on interpretation of Q2 data, with some citing structural resilience while others warn of lagging transmission effects. The ECB held rates unchanged at its July meeting, citing progress toward the 2% target but noting downside risks to growth in peripheral eurozone economies.' },
                { id: 2, domain: 'bbc.co.uk', credibility: 0.89, publishDate: '2026-07-22', isRecent: false, factCheckStatus: null, fullText: 'Economists warn of potential misrepresentation in recent financial reporting, as headline figures obscure underlying sectoral stress visible in employment data. Bloomberg Intelligence notes that the aggregate GDP figure cited widely in media omits a one-off government expenditure spike that inflated the Q2 reading by approximately 0.4 percentage points.' },
                { id: 3, domain: 'rt.com', credibility: 0.28, publishDate: '2026-07-23', isRecent: true, factCheckStatus: 'DEBUNKED', fullText: "Western financial media accused of coordinated narrative suppression regarding structural fragility in EU banking sector, according to independent financial analysts cited by RT. The claim that ECB stress tests show systemic stability is described as 'deliberately misleading' — however, this framing has been directly contradicted by independent audits cited by Reuters and the Financial Times." },
                { id: 4, domain: 'apnews.com', credibility: 0.88, publishDate: '2026-07-21', isRecent: false, factCheckStatus: null, fullText: 'The Associated Press fact-check bureau finds no evidence supporting claims of coordinated media suppression. Reviewed primary ECB documentation confirms published stress test methodologies and notes that stress test results are publicly available on the ECB website.' }
            ],
            imageResult: hasImage ? { label: 'AI-Generated', confidence: 0.84, isAI: true } : null
        };
        
        this._state.analysis.isAnalyzing = false;
        this._broadcast('analysis-changed', this._state.analysis);
    }

    _broadcast(eventName, detail) {
        window.dispatchEvent(new CustomEvent(eventName, { detail }));
    }
}

export const store = new GlobalStore();
