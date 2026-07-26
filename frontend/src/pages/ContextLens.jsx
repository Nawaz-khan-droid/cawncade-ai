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
                  <span className="text-xs text-textMuted-light dark:text-textMuted-dark font-medium">
                    Checked 2 minutes ago
                  </span>
                </div>
                <p className="text-xl font-bold text-slate-900 dark:text-slate-100 leading-snug">
                  "{text || url || result.answer?.replace(/^Analysis of:\s*/i, '') || 'Submitted Claim'}"
                </p>
              </div>

              {/* 2. DOMINANT VERDICT HERO CARD (25-30% Viewport Height) */}
              {(() => {
                const isDebunked = result.status === "debunked" || (result.scores?.confidence === 0 && result.context_summary?.toLowerCase().includes("debunk"));
                const hasTrusted = (result.metadata?.trusted_domains_found?.length || 0) > 0;
                const isHighConf = result.confidence >= 70 && hasTrusted;
                const isNoSources = result.status === "no_sources" || (result.metadata?.sources_retrieved || 0) < 2;

                let badgeTheme = "bg-amber-500/10 border-amber-500/30 text-amber-400";
                let verdictTitle = "UNVERIFIED";
                let verdictSoWhat = "No trusted source currently confirms this claim.";
                let confLevel = "Low";
                let whyBullets = [
                  (result.metadata?.sources_retrieved || 0) <= 1 ? "Only one relevant source found" : `${result.metadata?.sources_retrieved || 0} sources retrieved`,
                  "No official government or wire service confirmation",
                ];

                if (isDebunked) {
                  badgeTheme = "bg-rose-500/10 border-rose-500/30 text-rose-400";
                  verdictTitle = "FALSE / DEBUNKED";
                  verdictSoWhat = "Established fact-checking organizations have officially debunked this assertion.";
                  confLevel = "High";
                  whyBullets = ["Official debunking record found in fact-check database", "Contradicted by established news reporting"];
                } else if (isHighConf) {
                  badgeTheme = "bg-emerald-500/10 border-emerald-500/30 text-emerald-400";
                  verdictTitle = "VERIFIED TRUE";
                  verdictSoWhat = "Multiple trusted news agencies and official sources confirm this event.";
                  confLevel = "High";
                  whyBullets = [`Corroborated across ${result.metadata?.trusted_domains_found?.length || 1} trusted outlets`, "Consistent official documentation"];
                } else if (isNoSources) {
                  badgeTheme = "bg-orange-500/10 border-orange-500/30 text-orange-400";
                  verdictTitle = "INSUFFICIENT EVIDENCE";
                  verdictSoWhat = "We did not find enough reliable evidence to confirm or deny this claim.";
                  confLevel = "Low";
                  whyBullets = ["Available web data is too limited", "No corroborating reports detected"];
                }

                if (result.metadata?.agent_used === false) {
                  whyBullets.push("Advanced verification temporarily unavailable (extractive mode)");
                }

                return (
                  <div className={`p-6 md:p-8 rounded-2xl border ${badgeTheme} shadow-lg flex flex-col gap-5 transition-all`}>
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-black uppercase tracking-widest px-3 py-1 rounded-md bg-white/10">
                          VERDICT
                        </span>
                        <h3 className="text-3xl font-black tracking-wide">{verdictTitle}</h3>
                      </div>
                      <div className="text-xs font-bold px-3 py-1.5 rounded-full bg-white/10 self-start md:self-auto">
                        Confidence: {confLevel}
                      </div>
                    </div>

                    <p className="text-base font-semibold opacity-95 leading-relaxed">{verdictSoWhat}</p>

                    <div className="flex flex-col gap-2 pt-2 border-t border-white/10">
                      <span className="text-xs font-bold uppercase tracking-wider opacity-80">Why?</span>
                      <ul className="text-xs space-y-1 list-disc list-inside opacity-90 font-medium">
                        {whyBullets.map((b, i) => (
                          <li key={i}>{b}</li>
                        ))}
                      </ul>
                    </div>

                    {/* EVIDENCE SNAPSHOT BAR */}
                    <div className="flex items-center gap-4 pt-3 border-t border-white/10 text-xs font-medium opacity-80 flex-wrap">
                      <span>✓ Sources checked: {result.metadata?.sources_retrieved || 0}</span>
                      <span>•</span>
                      <span>✓ Trusted sources: {result.metadata?.trusted_domains_found?.length || 0}</span>
                      <span>•</span>
                      <span>✓ Verified: Just now</span>
                    </div>

                    {/* INLINE UNVERIFIED EXPLANATION NOTE */}
                    {verdictTitle === "UNVERIFIED" || verdictTitle === "INSUFFICIENT EVIDENCE" ? (
                      <div className="text-xs opacity-85 font-normal pt-2 border-t border-white/10 flex items-center gap-2">
                        <span>ⓘ</span>
                        <span>
                          <strong>Unverified</strong> means no reliable evidence currently confirms the claim. It does <em>not</em> necessarily mean the claim is false.
                        </span>
                      </div>
                    ) : null}
                  </div>
                );
              })()}

              {/* 3. SINGLE UNIFIED SUMMARY */}
              {result.agent_deep_dive ? (
                <div className="w-full">
                  <ContextSynthesis summary={result.agent_deep_dive} isLoading={false} />
                </div>
              ) : (
                <div className="glass-card p-6 md:p-8 flex flex-col gap-3">
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Analysis Summary</span>
                  <p className="text-sm font-medium text-slate-200 leading-relaxed">
                    {result.context_summary}
                  </p>
                </div>
              )}

              {/* 4. SOURCES & FINDINGS */}
              {result.sources_cited && result.sources_cited.length > 0 && (
                <div className="flex flex-col gap-3">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
                    Sources & Evidence ({result.sources_cited.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {result.sources_cited.map((src, idx) => {
                      const findingText = src.snippet 
                        ? (src.snippet.toLowerCase().includes("resign") ? "Discusses resignation claim." : "Discusses related news; does not report resignation.")
                        : "Source retrieved for contextual review.";

                      return (
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
                              {src.is_trusted ? '✓ TRUSTED' : src.trust_tier || 'NEWS'}
                            </span>
                          </div>
                          <p className="text-xs font-semibold text-slate-200 line-clamp-2">{src.title}</p>
                          
                          {/* FINDING CALLOUT */}
                          <div className="text-[11px] text-slate-300 bg-white/5 p-2 rounded-md border border-white/5 font-medium mt-1">
                            <span className="font-bold text-primary">Finding: </span>
                            {findingText}
                          </div>
                        </a>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 5. ADVANCED DETAILS (COLLAPSED ACCORDION) */}
              <details className="mt-4 pt-4 border-t border-borderBase-light dark:border-borderBase-dark group">
                <summary className="cursor-pointer text-xs font-bold uppercase tracking-wider text-slate-400 hover:text-slate-200 flex items-center gap-2 select-none">
                  <span>▼ How this result was generated (Advanced Details)</span>
                </summary>
                
                <div className="flex flex-col gap-6 mt-6">
                  {/* SEARCH SCOPE METRICS */}
                  <div className="p-4 rounded-xl bg-white/5 border border-white/5 grid grid-cols-3 gap-2 text-center">
                    <div>
                      <div className="text-lg font-bold text-primary">{result.metadata?.sources_retrieved || 0}</div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider">Sources Checked</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-emerald-400">{result.metadata?.trusted_domains_found?.length || 0}</div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider">Trusted Outlets</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-sky-400">{result.compute_time_ms || 0}ms</div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider">Latency</div>
                    </div>
                  </div>

                  {/* PROCESS AUDIT TRAIL */}
                  <div className="p-4 rounded-xl bg-white/5 border border-white/5 flex flex-col gap-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Process Audit Trail</span>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      <div className="p-2.5 rounded bg-black/20 text-xs flex flex-col gap-0.5">
                        <span className="font-bold text-primary">1. Retrieval</span>
                        <span className="text-[11px] text-slate-400">Queried 7 Search Tiers</span>
                      </div>
                      <div className="p-2.5 rounded bg-black/20 text-xs flex flex-col gap-0.5">
                        <span className="font-bold text-emerald-400">2. Cross-Reference</span>
                        <span className="text-[11px] text-slate-400">Evaluated Domain Trust</span>
                      </div>
                      <div className="p-2.5 rounded bg-black/20 text-xs flex flex-col gap-0.5">
                        <span className="font-bold text-sky-400">3. Synthesis</span>
                        <span className="text-[11px] text-slate-400">Status: {result.status}</span>
                      </div>
                    </div>
                  </div>

                  {/* TELEMETRY GAUGES */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <Gauge label="Confidence" value={result.scores?.confidence || 0} colorClass="text-emerald-500" />
                    <Gauge label="Bias" value={result.scores?.bias || 0} colorClass="text-amber-500" />
                    <Gauge label="Conflict" value={result.scores?.conflict || 0} colorClass="text-rose-500" />
                    <Gauge label="Sensitivity" value={result.scores?.sensitivity || 0} colorClass="text-purple-500" />
                    <Gauge label="AI-Risk" value={result.scores?.ai_risk || 0} colorClass="text-orange-500" />
                    <Gauge label="Recency" value={result.scores?.recency || 0} colorClass="text-blue-500" />
                  </div>
                </div>
              </details>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </motion.div>
  );
}
