import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Link as LinkIcon, Lock, Clock } from 'lucide-react';
import api from '../services/api';
import { usePipeline } from '../context/PipelineContext';
import ContextSynthesis from '../components/ContextSynthesis';

// Shared UI Library Primitives
import ResultHero from '../components/ui/ResultHero';
import SourceCard from '../components/ui/SourceCard';
import LoadingState from '../components/ui/LoadingState';
import EmptyState from '../components/ui/EmptyState';
import ErrorState from '../components/ui/ErrorState';

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
      className="flex flex-col gap-5 w-full max-w-4xl mx-auto px-2 md:px-0"
    >
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl md:text-3xl font-display font-bold text-slate-900 dark:text-slate-50">ContextLens</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">Analyze raw text claims and article URLs against multi-vector knowledge graphs.</p>
      </div>

      <div className="glass-card p-4 md:p-6 flex flex-col gap-5">
        
        {/* Text Input */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold uppercase tracking-wider flex items-center gap-2 text-textMain-light dark:text-textMain-dark">
              <Search className="w-3.5 h-3.5 text-primary" />
              Claim or Text Segment
            </label>
            <span className={`text-[11px] font-mono transition-colors ${
              text.length >= 4750 
                ? 'text-rose-400 font-bold' 
                : text.length >= 4000 
                ? 'text-amber-400 font-bold' 
                : 'text-slate-400'
            }`}>
              {text.length.toLocaleString()} / 5,000
            </span>
          </div>
          <textarea 
            value={text}
            onChange={(e) => { setText(e.target.value); setUrl(''); }}
            disabled={isLoading}
            maxLength={5000}
            placeholder="Paste a suspicious claim, news excerpt, or social media post for context analysis (up to 5,000 characters)..." 
            className="w-full bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl p-3.5 text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all resize-none min-h-[100px] text-sm disabled:opacity-50"
          />
        </div>

        {/* OR Divider */}
        <div className="flex items-center gap-4">
          <div className="flex-1 h-px bg-borderBase-light dark:bg-borderBase-dark"></div>
          <span className="text-[10px] font-bold text-textMuted-light dark:text-textMuted-dark uppercase tracking-widest">OR</span>
          <div className="flex-1 h-px bg-borderBase-light dark:bg-borderBase-dark"></div>
        </div>

        {/* URL Input */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-bold uppercase tracking-wider flex items-center justify-between text-textMain-light dark:text-textMain-dark">
            <span className="flex items-center gap-2">
              <LinkIcon className="w-3.5 h-3.5 text-primary" />
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
              className="w-full bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl pl-10 pr-4 py-2.5 text-sm text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all disabled:opacity-50" 
            />
            <LinkIcon className="w-4 h-4 text-textMuted-light dark:text-textMuted-dark absolute left-3.5 top-3" />
          </div>
        </div>

        {error && <ErrorState error={error} onRetry={handleAnalyze} />}

        <button 
          onClick={handleAnalyze}
          disabled={(!text && !url) || isLoading}
          className="btn-primary py-3 text-base font-semibold flex items-center justify-center gap-2 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          {isLoading ? 'Extracting Context...' : 'Analyze Context'}
        </button>

        {/* LOADING STATE */}
        {isLoading && <LoadingState message="Querying 7 Web Search Tiers & Evaluating Domain Trust..." />}

        {/* RESULT SECTION */}
        <AnimatePresence>
          {result && !isLoading && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="border-t border-borderBase-light dark:border-borderBase-dark pt-5 flex flex-col gap-4"
            >
              {/* 1. COMPACT CLAIM CARD */}
              <div className="p-3.5 rounded-xl bg-surface-light/80 dark:bg-surface-dark/80 border border-borderBase-light dark:border-borderBase-dark shadow-sm flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-extrabold uppercase tracking-widest text-primary">Target Claim</span>
                  <span className="text-[11px] text-textMuted-light dark:text-textMuted-dark font-medium flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Checked 2 minutes ago
                  </span>
                </div>
                <p className="text-sm md:text-base font-bold text-slate-900 dark:text-slate-100 leading-snug">
                  "{text || url || result.answer?.replace(/^Analysis of:\s*/i, '') || 'Submitted Claim'}"
                </p>
              </div>

              {/* 2. REUSABLE HERO VERDICT CARD */}
              <ResultHero result={result} />

              {/* 3. SINGLE UNIFIED ANALYSIS SUMMARY */}
              {result.agent_deep_dive ? (
                <div className="w-full">
                  <ContextSynthesis summary={result.agent_deep_dive} isLoading={false} />
                </div>
              ) : (
                <div className="glass-card p-4 md:p-6 flex flex-col gap-2 rounded-2xl">
                  <span className="text-xs font-extrabold uppercase tracking-widest text-slate-400">Analysis Summary</span>
                  <p className="text-sm font-medium text-slate-200 leading-relaxed">
                    {result.context_summary}
                  </p>
                </div>
              )}

              {/* 4. SOURCES & EVIDENCE */}
              {result.sources_cited && result.sources_cited.length > 0 ? (
                <div className="flex flex-col gap-2.5">
                  <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">
                    Sources & Evidence ({result.sources_cited.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {result.sources_cited.map((src, idx) => (
                      <SourceCard key={idx} src={src} />
                    ))}
                  </div>
                </div>
              ) : (
                <EmptyState />
              )}

              {/* 5. ADVANCED VERIFICATION DETAILS (COLLAPSED ACCORDION) */}
              <details className="mt-1 pt-3 border-t border-borderBase-light dark:border-borderBase-dark group">
                <summary className="cursor-pointer text-xs font-bold uppercase tracking-wider text-slate-400 hover:text-slate-200 flex items-center gap-2 select-none">
                  <span>▼ Advanced Verification Details</span>
                  <span className="text-[10px] font-normal text-slate-500">(How we analyzed this claim)</span>
                </summary>
                
                <div className="flex flex-col gap-4 mt-4">
                  {/* SEARCH SCOPE METRICS */}
                  <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 grid grid-cols-3 gap-2 text-center">
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
                  <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 flex flex-col gap-2">
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
