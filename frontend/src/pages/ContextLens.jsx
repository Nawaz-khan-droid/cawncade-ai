import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Link as LinkIcon, Lock, Loader2, AlertCircle } from 'lucide-react';
import api from '../services/api';
import { usePipeline } from '../context/PipelineContext';
import ContextSynthesis from '../components/ContextSynthesis';

const Gauge = ({ label, value, colorClass }) => {
  const radius = 40;
  const circumference = Math.PI * radius;
  const dashoffset = circumference - (value * circumference);
  
  return (
    <div className="flex flex-col items-center gap-2 p-4 bg-surface-light/50 dark:bg-surface-dark/50 rounded-xl border border-borderBase-light dark:border-borderBase-dark">
      <div className="relative w-24 h-12 flex justify-center">
        <svg className="w-full h-full overflow-visible" viewBox="0 0 100 50">
          <path
            d="M 10 50 a 40 40 0 0 1 80 0"
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            className="text-slate-200 dark:text-slate-800"
            strokeLinecap="round"
          />
          <path
            d="M 10 50 a 40 40 0 0 1 80 0"
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            strokeLinecap="round"
            className={`${colorClass} transition-all duration-1000 ease-out`}
            strokeDasharray={circumference}
            strokeDashoffset={dashoffset}
          />
        </svg>
        <div className="absolute bottom-0 text-lg font-bold font-display text-slate-800 dark:text-slate-100">
          {Math.round(value * 100)}%
        </div>
      </div>
      <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">{label}</span>
    </div>
  );
};

export default function ContextLens() {
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const { isLoading, result, error, startPipeline, finishPipeline, failPipeline } = usePipeline();

  const handleAnalyze = async () => {
    if (!text && !url) return;
    startPipeline();
    try {
      const payload = url ? { input_text: url, input_type: 'url' } : { input_text: text, input_type: 'text' };
      const res = await api.analyze(payload);
      finishPipeline(res);
    } catch (err) {
      failPipeline(err.message);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-8 w-full max-w-4xl mx-auto"
    >
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-display font-bold text-slate-900 dark:text-slate-50">ContextLens</h2>
        <p className="text-slate-500 dark:text-slate-400">Analyze raw text claims and article URLs against multi-vector knowledge graphs.</p>
      </div>

      <div className="glass-card p-6 md:p-8 flex flex-col gap-8">
        
        {/* Text Input */}
        <div className="flex flex-col gap-3">
          <label className="text-sm font-semibold flex items-center gap-2 text-textMain-light dark:text-textMain-dark">
            <Search className="w-4 h-4 text-primary" />
            Claim or Text Segment
          </label>
          <textarea 
            value={text}
            onChange={(e) => { setText(e.target.value); setUrl(''); }}
            disabled={isLoading}
            placeholder="Paste a suspicious claim, news excerpt, or social media post for context analysis..." 
            className="w-full bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl p-4 text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all resize-none min-h-[120px] disabled:opacity-50"
          />
        </div>

        {/* OR Divider */}
        <div className="flex items-center gap-4">
          <div className="flex-1 h-px bg-borderBase-light dark:bg-borderBase-dark"></div>
          <span className="text-xs font-medium text-textMuted-light dark:text-textMuted-dark uppercase tracking-widest">OR</span>
          <div className="flex-1 h-px bg-borderBase-light dark:bg-borderBase-dark"></div>
        </div>

        {/* URL Input */}
        <div className="flex flex-col gap-3">
          <label className="text-sm font-semibold flex items-center justify-between text-textMain-light dark:text-textMain-dark">
            <span className="flex items-center gap-2">
              <LinkIcon className="w-4 h-4 text-primary" />
              Article URL
            </span>
            <span className="flex items-center gap-1 text-[10px] uppercase tracking-wider bg-success/10 text-success px-2 py-0.5 rounded-full border border-success/20">
              <Lock className="w-3 h-3" /> HTTPS Only
            </span>
          </label>
          <div className="relative">
            <input 
              type="url" 
              value={url}
              onChange={(e) => { setUrl(e.target.value); setText(''); }}
              disabled={isLoading}
              placeholder="https://example.com/news-article" 
              className="w-full bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl pl-10 pr-4 py-3.5 text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all disabled:opacity-50" 
            />
            <LinkIcon className="w-5 h-5 text-textMuted-light dark:text-textMuted-dark absolute left-3.5 top-3.5" />
          </div>
        </div>

        {error && (
          <div className="bg-alert/10 border border-alert/20 text-alert p-4 rounded-xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5" />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        <button 
          onClick={handleAnalyze}
          disabled={(!text && !url) || isLoading}
          className="btn-primary py-4 mt-2 text-lg font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isLoading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> Extracting Context...</>
          ) : (
            <><Search className="w-5 h-5" /> Analyze Context</>
          )}
        </button>

        {/* RESULT SECTION */}
        <AnimatePresence>
          {result && !isLoading && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="border-t border-borderBase-light dark:border-borderBase-dark pt-8 mt-4 flex flex-col gap-6"
            >
              {/* 1. CLAIM CARD */}
              <div className="p-5 rounded-2xl bg-surface-light/80 dark:bg-surface-dark/80 border border-borderBase-light dark:border-borderBase-dark shadow-sm flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-extrabold uppercase tracking-widest text-primary">Target Claim</span>
                  <span className="text-xs text-textMuted-light dark:text-textMuted-dark">
                    Last checked: {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  "{text || url || result.answer?.replace(/^Analysis of:\s*/i, '') || 'Submitted Claim'}"
                </p>
              </div>

              {/* 2. VERDICT HERO BANNER (Evidence-Driven) */}
              {(() => {
                const isDebunked = result.status === "debunked" || (result.scores?.confidence === 0 && result.context_summary?.toLowerCase().includes("debunk"));
                const hasTrusted = (result.metadata?.trusted_domains_found?.length || 0) > 0;
                const isHighConf = result.confidence >= 70 && hasTrusted;
                const isNoSources = result.status === "no_sources" || (result.metadata?.sources_retrieved || 0) < 2;

                let badgeColor = "bg-amber-500/10 border-amber-500/30 text-amber-400";
                let verdictTitle = "UNVERIFIED";
                let verdictSub = "No reliable evidence from established fact-checkers or wire services currently confirms this claim.";

                if (isDebunked) {
                  badgeColor = "bg-rose-500/10 border-rose-500/30 text-rose-400";
                  verdictTitle = "FALSE / DEBUNKED";
                  verdictSub = "Established fact-checking organizations have officially debunked this assertion.";
                } else if (isHighConf) {
                  badgeColor = "bg-emerald-500/10 border-emerald-500/30 text-emerald-400";
                  verdictTitle = "VERIFIED TRUE";
                  verdictSub = "Corroborated by multiple trusted news agencies and official sources.";
                } else if (isNoSources) {
                  badgeColor = "bg-orange-500/10 border-orange-500/30 text-orange-400";
                  verdictTitle = "INSUFFICIENT EVIDENCE";
                  verdictSub = "Available web data is too limited to reach a definitive conclusion.";
                }

                return (
                  <div className={`p-6 rounded-2xl border ${badgeColor} shadow-md flex flex-col gap-3 transition-all`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-black uppercase tracking-widest px-3 py-1 rounded-md bg-white/10">
                          VERDICT
                        </span>
                        <h3 className="text-2xl font-black tracking-wide">{verdictTitle}</h3>
                      </div>
                      <div className="text-xs font-semibold px-3 py-1 rounded-full bg-white/10">
                        {result.confidence >= 70 ? 'HIGH' : result.confidence >= 40 ? 'MEDIUM' : 'LOW'} CONFIDENCE ({Math.round(result.confidence || 0)}%)
                      </div>
                    </div>
                    <p className="text-sm font-medium opacity-90 leading-relaxed">{verdictSub}</p>
                  </div>
                );
              })()}

              {/* 3. CONFIDENCE & SEARCH SCOPE CARD */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 rounded-xl bg-surface-light/60 dark:bg-surface-dark/60 border border-borderBase-light dark:border-borderBase-dark flex flex-col gap-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Confidence Explanation</span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold text-slate-100">
                      {result.confidence >= 70 ? 'HIGH' : result.confidence >= 40 ? 'MEDIUM' : 'LOW'}
                    </span>
                    <span className="text-xs text-slate-400">({Math.round(result.confidence || 0)}%)</span>
                  </div>
                  <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside opacity-90">
                    {(result.metadata?.sources_retrieved || 0) > 0 ? (
                      <li>{result.metadata?.sources_retrieved || 0} total web source(s) retrieved</li>
                    ) : (
                      <li>Limited web source coverage found</li>
                    )}
                    {(result.metadata?.trusted_domains_found?.length || 0) > 0 ? (
                      <li>Confirmed coverage across: {result.metadata.trusted_domains_found.join(', ')}</li>
                    ) : (
                      <li>No official government or wire service announcements found</li>
                    )}
                    {result.metadata?.agent_used === false && (
                      <li>Advanced LLM deep-synthesis currently offline (running extractive NLP pass)</li>
                    )}
                  </ul>
                </div>

                <div className="p-5 rounded-xl bg-surface-light/60 dark:bg-surface-dark/60 border border-borderBase-light dark:border-borderBase-dark flex flex-col gap-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Search Scope & Metrics</span>
                  <div className="grid grid-cols-3 gap-2 text-center my-auto">
                    <div className="p-2 rounded-lg bg-white/5 border border-white/5">
                      <div className="text-lg font-bold text-primary">{result.metadata?.sources_retrieved || 0}</div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider">Sources</div>
                    </div>
                    <div className="p-2 rounded-lg bg-white/5 border border-white/5">
                      <div className="text-lg font-bold text-emerald-400">{result.metadata?.trusted_domains_found?.length || 0}</div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider">Trusted</div>
                    </div>
                    <div className="p-2 rounded-lg bg-white/5 border border-white/5">
                      <div className="text-lg font-bold text-sky-400">{result.compute_time_ms || 0}ms</div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider">Latency</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 4. EVIDENCE SUMMARY & CONTEXT SYNTHESIS */}
              <div className="flex flex-col gap-3">
                <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Evidence Summary</span>
                <p className="text-sm font-medium text-slate-200 bg-primary/10 p-4 rounded-xl border border-primary/20 leading-relaxed">
                  {result.context_summary}
                </p>
              </div>

              {result.agent_deep_dive && (
                <div className="w-full">
                  <ContextSynthesis summary={result.agent_deep_dive} isLoading={false} />
                </div>
              )}

              {/* 5. SEQUENTIAL VERIFICATION PROCESS AUDIT */}
              <div className="p-5 rounded-xl bg-surface-light/40 dark:bg-surface-dark/40 border border-borderBase-light dark:border-borderBase-dark flex flex-col gap-4">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Verification Audit Trail</span>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="p-3 rounded-lg bg-white/5 border border-white/5 flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-primary uppercase">Step 1 • Retrieval</span>
                    <span className="text-xs font-medium text-slate-200">Queried 7 Search Tiers</span>
                    <span className="text-[11px] text-slate-400">{result.metadata?.sources_retrieved || 0} articles fetched</span>
                  </div>
                  <div className="p-3 rounded-lg bg-white/5 border border-white/5 flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-emerald-400 uppercase">Step 2 • Cross-Reference</span>
                    <span className="text-xs font-medium text-slate-200">Evaluated Domain Trust</span>
                    <span className="text-[11px] text-slate-400">{result.metadata?.trusted_domains_found?.length || 0} trusted outlets matched</span>
                  </div>
                  <div className="p-3 rounded-lg bg-white/5 border border-white/5 flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-sky-400 uppercase">Step 3 • Synthesis</span>
                    <span className="text-xs font-medium text-slate-200">Computed Multi-Factor Score</span>
                    <span className="text-[11px] text-slate-400">Status: {result.status}</span>
                  </div>
                </div>
              </div>

              {/* 6. REAL SOURCES & TRUST CARDS */}
              {result.sources_cited && result.sources_cited.length > 0 && (
                <div className="flex flex-col gap-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Retrieved Evidence Sources ({result.sources_cited.length})
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {result.sources_cited.map((src, idx) => (
                      <a
                        key={idx}
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-4 rounded-xl bg-surface-light/60 dark:bg-surface-dark/60 border border-borderBase-light dark:border-borderBase-dark hover:border-primary/40 transition-all flex flex-col gap-2 group"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-primary group-hover:underline truncate max-w-[200px]">
                            {src.source_name || src.domain || 'Source'}
                          </span>
                          <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded ${
                            src.is_trusted ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-700 text-slate-300'
                          }`}>
                            {src.is_trusted ? '✓ TRUSTED' : src.trust_tier || 'UNVERIFIED'}
                          </span>
                        </div>
                        <p className="text-xs font-medium text-slate-200 line-clamp-2">{src.title}</p>
                        <span className="text-[10px] text-slate-400 truncate opacity-75">{src.url}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* 7. UNVERIFIED DISCLAIMER & SYSTEM LIMITATIONS NOTICE */}
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200/90 text-xs leading-relaxed flex flex-col gap-2">
                <div className="font-bold flex items-center gap-2 text-amber-300">
                  <span>💡 What does "Unverified" mean?</span>
                </div>
                <p>
                  <strong>Unverified</strong> means the system did not find sufficient reliable evidence or official announcements to confirm the claim at the time of checking. It does <strong>not</strong> necessarily mean the claim is false.
                </p>
                {result.metadata?.agent_used === false && (
                  <p className="text-[11px] opacity-80 border-t border-amber-500/20 pt-2 mt-1">
                    ℹ️ Advanced semantic verification is temporarily offline. This report is based on real-time web search and extractive source analysis.
                  </p>
                )}
              </div>

              {/* 8. COLLAPSIBLE TECHNICAL TELEMETRY & DEBUG GAUGES */}
              <details className="mt-4 pt-4 border-t border-borderBase-light dark:border-borderBase-dark group">
                <summary className="cursor-pointer text-xs font-bold uppercase tracking-wider text-slate-400 hover:text-slate-200 flex items-center gap-2 select-none">
                  <span>▼ Technical Telemetry & Debug Gauges</span>
                  <span className="text-[10px] font-normal text-slate-500">(Developer Inspection)</span>
                </summary>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6">
                  <Gauge label="Confidence" value={result.scores?.confidence || 0} colorClass="text-emerald-500" />
                  <Gauge label="Bias" value={result.scores?.bias || 0} colorClass="text-amber-500" />
                  <Gauge label="Conflict" value={result.scores?.conflict || 0} colorClass="text-rose-500" />
                  <Gauge label="Sensitivity" value={result.scores?.sensitivity || 0} colorClass="text-purple-500" />
                  <Gauge label="AI-Risk" value={result.scores?.ai_risk || 0} colorClass="text-orange-500" />
                  <Gauge label="Recency" value={result.scores?.recency || 0} colorClass="text-blue-500" />
                </div>
              </details>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </motion.div>
  );
}
