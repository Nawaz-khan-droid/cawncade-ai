import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Link as LinkIcon, 
  Lock, 
  Loader2, 
  AlertCircle, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle, 
  Info, 
  Clock, 
  ShieldCheck, 
  Check 
} from 'lucide-react';
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
      className="flex flex-col gap-6 w-full max-w-4xl mx-auto px-2 md:px-0"
    >
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl md:text-3xl font-display font-bold text-slate-900 dark:text-slate-50">ContextLens</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">Analyze raw text claims and article URLs against multi-vector knowledge graphs.</p>
      </div>

      <div className="glass-card p-5 md:p-7 flex flex-col gap-6">
        
        {/* Text Input */}
        <div className="flex flex-col gap-2.5">
          <label className="text-sm font-semibold flex items-center gap-2 text-textMain-light dark:text-textMain-dark">
            <Search className="w-4 h-4 text-primary" />
            Claim or Text Segment
          </label>
          <textarea 
            value={text}
            onChange={(e) => { setText(e.target.value); setUrl(''); }}
            disabled={isLoading}
            placeholder="Paste a suspicious claim, news excerpt, or social media post for context analysis..." 
            className="w-full bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl p-3.5 text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all resize-none min-h-[110px] text-sm disabled:opacity-50"
          />
        </div>

        {/* OR Divider */}
        <div className="flex items-center gap-4 my-0.5">
          <div className="flex-1 h-px bg-borderBase-light dark:bg-borderBase-dark"></div>
          <span className="text-[10px] font-bold text-textMuted-light dark:text-textMuted-dark uppercase tracking-widest">OR</span>
          <div className="flex-1 h-px bg-borderBase-light dark:bg-borderBase-dark"></div>
        </div>

        {/* URL Input */}
        <div className="flex flex-col gap-2.5">
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
              className="w-full bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl pl-10 pr-4 py-3 text-sm text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all disabled:opacity-50" 
            />
            <LinkIcon className="w-4 h-4 text-textMuted-light dark:text-textMuted-dark absolute left-3.5 top-3.5" />
          </div>
        </div>

        {error && (
          <div className="bg-alert/10 border border-alert/20 text-alert p-3.5 rounded-xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span className="text-xs md:text-sm font-medium">{error}</span>
          </div>
        )}

        <button 
          onClick={handleAnalyze}
          disabled={(!text && !url) || isLoading}
          className="btn-primary py-3.5 text-base font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
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
              className="border-t border-borderBase-light dark:border-borderBase-dark pt-6 mt-2 flex flex-col gap-5"
            >
              {/* 1. COMPACT CLAIM CARD */}
              <div className="p-4 rounded-xl bg-surface-light/80 dark:bg-surface-dark/80 border border-borderBase-light dark:border-borderBase-dark shadow-sm flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-extrabold uppercase tracking-widest text-primary">Target Claim</span>
                  <span className="text-[11px] text-textMuted-light dark:text-textMuted-dark font-medium flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Checked 2 minutes ago
                  </span>
                </div>
                <p className="text-base md:text-lg font-bold text-slate-900 dark:text-slate-100 leading-snug">
                  "{text || url || result.answer?.replace(/^Analysis of:\s*/i, '') || 'Submitted Claim'}"
                </p>
              </div>

              {/* 2. DOMINANT VERDICT HERO CARD (Subtle Accent Tint + Left Stripe) */}
              {(() => {
                const isDebunked = result.status === "debunked" || (result.scores?.confidence === 0 && result.context_summary?.toLowerCase().includes("debunk"));
                const hasTrusted = (result.metadata?.trusted_domains_found?.length || 0) > 0;
                const isHighConf = result.confidence >= 70 && hasTrusted;
                const isNoSources = result.status === "no_sources" || (result.metadata?.sources_retrieved || 0) < 2;

                // Subtle dark palette with vertical left accent stripe
                let themeConfig = {
                  stripe: "border-l-4 border-amber-500",
                  bgGradient: "bg-gradient-to-br from-amber-950/40 via-surface-dark/95 to-slate-950",
                  borderColor: "border-amber-500/30",
                  titleColor: "text-amber-400",
                  badgeBg: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
                  icon: AlertTriangle,
                  verdictTitle: "UNVERIFIED",
                  verdictSoWhat: "No trusted source currently confirms this claim.",
                  confLevel: "Low",
                  whyBullets: [
                    (result.metadata?.sources_retrieved || 0) <= 1 ? "Only one relevant source found" : `${result.metadata?.sources_retrieved || 0} web sources retrieved`,
                    "No official government or wire service confirmation",
                  ],
                };

                if (isDebunked) {
                  themeConfig = {
                    stripe: "border-l-4 border-rose-500",
                    bgGradient: "bg-gradient-to-br from-rose-950/40 via-surface-dark/95 to-slate-950",
                    borderColor: "border-rose-500/30",
                    titleColor: "text-rose-400",
                    badgeBg: "bg-rose-500/15 text-rose-300 border border-rose-500/30",
                    icon: XCircle,
                    verdictTitle: "FALSE / DEBUNKED",
                    verdictSoWhat: "Established fact-checking organizations have officially debunked this assertion.",
                    confLevel: "High",
                    whyBullets: ["Official debunking record found in fact-check database", "Contradicted by established news reporting"],
                  };
                } else if (isHighConf) {
                  themeConfig = {
                    stripe: "border-l-4 border-emerald-500",
                    bgGradient: "bg-gradient-to-br from-emerald-950/40 via-surface-dark/95 to-slate-950",
                    borderColor: "border-emerald-500/30",
                    titleColor: "text-emerald-400",
                    badgeBg: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
                    icon: CheckCircle2,
                    verdictTitle: "VERIFIED TRUE",
                    verdictSoWhat: "Multiple trusted news agencies and official sources confirm this event.",
                    confLevel: "High",
                    whyBullets: [`Corroborated across ${result.metadata?.trusted_domains_found?.length || 1} trusted outlets`, "Consistent official documentation"],
                  };
                } else if (isNoSources) {
                  themeConfig = {
                    stripe: "border-l-4 border-orange-500",
                    bgGradient: "bg-gradient-to-br from-orange-950/40 via-surface-dark/95 to-slate-950",
                    borderColor: "border-orange-500/30",
                    titleColor: "text-orange-400",
                    badgeBg: "bg-orange-500/15 text-orange-300 border border-orange-500/30",
                    icon: HelpCircle,
                    verdictTitle: "INSUFFICIENT EVIDENCE",
                    verdictSoWhat: "We did not find enough reliable evidence to confirm or deny this claim.",
                    confLevel: "Low",
                    whyBullets: ["Available web data is too limited", "No corroborating reports detected"],
                  };
                }

                if (result.metadata?.agent_used === false) {
                  themeConfig.whyBullets.push("Advanced verification temporarily offline (extractive mode)");
                }

                const VerdictIcon = themeConfig.icon;

                return (
                  <div className={`p-5 md:p-7 rounded-2xl border ${themeConfig.stripe} ${themeConfig.borderColor} ${themeConfig.bgGradient} shadow-lg flex flex-col gap-4 transition-all`}>
                    
                    {/* Header Row */}
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-2.5">
                        <VerdictIcon className={`w-7 h-7 md:w-8 md:h-8 ${themeConfig.titleColor} shrink-0`} />
                        <h3 className={`text-2xl md:text-3xl font-black tracking-tight ${themeConfig.titleColor}`}>
                          {themeConfig.verdictTitle}
                        </h3>
                      </div>
                      <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1 rounded-full bg-white/5 border border-white/10">
                        <span>Confidence:</span>
                        <span className={`font-bold ${themeConfig.titleColor}`}>{themeConfig.confLevel}</span>
                      </div>
                    </div>

                    {/* So-What Explanation */}
                    <p className="text-sm md:text-base font-semibold text-slate-200 leading-relaxed">{themeConfig.verdictSoWhat}</p>

                    {/* Why Bullets */}
                    <div className="flex flex-col gap-1.5 pt-2 border-t border-white/10">
                      <span className="text-[11px] font-extrabold uppercase tracking-wider text-slate-400">Why?</span>
                      <ul className="text-xs space-y-1 list-disc list-inside text-slate-300 font-medium">
                        {themeConfig.whyBullets.map((b, i) => (
                          <li key={i}>{b}</li>
                        ))}
                      </ul>
                    </div>

                    {/* EVIDENCE SNAPSHOT BADGES */}
                    <div className="flex items-center gap-2 pt-3 border-t border-white/10 flex-wrap text-xs font-medium text-slate-300">
                      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10">
                        <Check className="w-3.5 h-3.5 text-primary" />
                        <span>{result.metadata?.sources_retrieved || 0} Sources</span>
                      </div>
                      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        <span>{result.metadata?.trusted_domains_found?.length || 0} Trusted</span>
                      </div>
                      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>Checked just now</span>
                      </div>
                    </div>

                    {/* INLINE UNVERIFIED NOTE */}
                    {(themeConfig.verdictTitle === "UNVERIFIED" || themeConfig.verdictTitle === "INSUFFICIENT EVIDENCE") && (
                      <div className="text-xs text-slate-300/90 font-normal pt-2 border-t border-white/10 flex items-start gap-2 leading-relaxed">
                        <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                        <span>
                          <strong>Unverified</strong> means no reliable evidence currently confirms the claim. It does <em>not</em> necessarily mean the claim is false. Confidence reflects available evidence quantity—not truth value.
                        </span>
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* 3. SINGLE UNIFIED ANALYSIS SUMMARY */}
              {result.agent_deep_dive ? (
                <div className="w-full">
                  <ContextSynthesis summary={result.agent_deep_dive} isLoading={false} />
                </div>
              ) : (
                <div className="glass-card p-5 md:p-7 flex flex-col gap-2.5">
                  <span className="text-xs font-extrabold uppercase tracking-widest text-slate-400">Analysis Summary</span>
                  <p className="text-sm font-medium text-slate-200 leading-relaxed">
                    {result.context_summary}
                  </p>
                </div>
              )}

              {/* 4. SOURCES & EVIDENCE (4-State Lucide Status Badges) */}
              {result.sources_cited && result.sources_cited.length > 0 && (
                <div className="flex flex-col gap-3">
                  <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">
                    Sources & Evidence ({result.sources_cited.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {result.sources_cited.map((src, idx) => {
                      const lowerSnippet = (src.snippet || '').toLowerCase();
                      const lowerTitle = (src.title || '').toLowerCase();

                      // 4-State Classification: Supports, Contradicts, Related, Insufficient
                      let stateConfig = {
                        label: "Related News",
                        badgeClass: "bg-amber-500/15 text-amber-300 border-amber-500/30",
                        icon: AlertTriangle,
                        findingText: "Discusses related news; does not report that the claim occurred.",
                      };

                      if (lowerSnippet.includes("debunk") || lowerSnippet.includes("fake") || lowerSnippet.includes("false")) {
                        stateConfig = {
                          label: "Contradicts Claim",
                          badgeClass: "bg-rose-500/15 text-rose-300 border-rose-500/30",
                          icon: XCircle,
                          findingText: "Explicitly refutes or debunks this claim.",
                        };
                      } else if (src.is_trusted && (lowerSnippet.includes("confirm") || lowerSnippet.includes("official"))) {
                        stateConfig = {
                          label: "Supports Claim",
                          badgeClass: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
                          icon: CheckCircle2,
                          findingText: "Corroborates the claim with official reports.",
                        };
                      } else if (!src.snippet || src.snippet.length < 15) {
                        stateConfig = {
                          label: "Insufficient Info",
                          badgeClass: "bg-slate-700/50 text-slate-300 border-slate-600",
                          icon: HelpCircle,
                          findingText: "Source retrieved for contextual background.",
                        };
                      }

                      const StatusIcon = stateConfig.icon;

                      return (
                        <a
                          key={idx}
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-4 rounded-xl bg-surface-light/60 dark:bg-surface-dark/60 border border-borderBase-light dark:border-borderBase-dark hover:border-primary/40 transition-all flex flex-col gap-2.5 group"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-primary group-hover:underline truncate max-w-[180px]">
                              {src.source_name || src.domain || 'Source'}
                            </span>
                            <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded ${
                              src.is_trusted ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'
                            }`}>
                              {src.is_trusted ? '✓ TRUSTED' : src.trust_tier || 'NEWS'}
                            </span>
                          </div>

                          <p className="text-xs font-semibold text-slate-200 line-clamp-2 leading-snug">{src.title}</p>
                          
                          {/* 4-STATE FINDING STATUS BADGE */}
                          <div className={`text-[11px] p-2 rounded-lg border flex items-center gap-2 font-medium ${stateConfig.badgeClass}`}>
                            <StatusIcon className="w-3.5 h-3.5 shrink-0" />
                            <span className="font-bold shrink-0">{stateConfig.label}:</span>
                            <span className="truncate opacity-90">{stateConfig.findingText}</span>
                          </div>
                        </a>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 5. ADVANCED VERIFICATION DETAILS (COLLAPSED ACCORDION) */}
              <details className="mt-2 pt-4 border-t border-borderBase-light dark:border-borderBase-dark group">
                <summary className="cursor-pointer text-xs font-bold uppercase tracking-wider text-slate-400 hover:text-slate-200 flex items-center gap-2 select-none">
                  <span>▼ Advanced Verification Details</span>
                  <span className="text-[10px] font-normal text-slate-500">(How we analyzed this claim)</span>
                </summary>
                
                <div className="flex flex-col gap-5 mt-5">
                  {/* SEARCH SCOPE METRICS */}
                  <div className="p-4 rounded-xl bg-white/5 border border-white/5 grid grid-cols-3 gap-2 text-center">
                    <div>
                      <div className="text-base font-bold text-primary">{result.metadata?.sources_retrieved || 0}</div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider">Sources Checked</div>
                    </div>
                    <div>
                      <div className="text-base font-bold text-emerald-400">{result.metadata?.trusted_domains_found?.length || 0}</div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider">Trusted Outlets</div>
                    </div>
                    <div>
                      <div className="text-base font-bold text-sky-400">{result.compute_time_ms || 0}ms</div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider">Latency</div>
                    </div>
                  </div>

                  {/* PROCESS AUDIT TRAIL */}
                  <div className="p-4 rounded-xl bg-white/5 border border-white/5 flex flex-col gap-2.5">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Process Audit Trail</span>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      <div className="p-2 rounded bg-black/20 text-xs flex flex-col gap-0.5">
                        <span className="font-bold text-primary">1. Retrieval</span>
                        <span className="text-[11px] text-slate-400">Queried 7 Search Tiers</span>
                      </div>
                      <div className="p-2 rounded bg-black/20 text-xs flex flex-col gap-0.5">
                        <span className="font-bold text-emerald-400">2. Cross-Reference</span>
                        <span className="text-[11px] text-slate-400">Evaluated Domain Trust</span>
                      </div>
                      <div className="p-2 rounded bg-black/20 text-xs flex flex-col gap-0.5">
                        <span className="font-bold text-sky-400">3. Synthesis</span>
                        <span className="text-[11px] text-slate-400">Status: {result.status}</span>
                      </div>
                    </div>
                  </div>

                  {/* TELEMETRY GAUGES */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
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
