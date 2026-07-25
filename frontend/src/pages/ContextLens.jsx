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
              <div className="flex flex-col gap-2">
                <h3 className="text-2xl font-display font-bold text-slate-900 dark:text-white">Analysis Result</h3>
                <p className="text-sm text-textMuted-light dark:text-textMuted-dark leading-relaxed">
                  {result.answer || "Analysis complete."}
                </p>
                <p className="text-sm text-primary font-medium mt-2 bg-primary/10 p-3 rounded-lg border border-primary/20">
                  {result.context_summary}
                </p>
              </div>

              {result.agent_deep_dive && (
                <div className="w-full">
                  <ContextSynthesis summary={result.agent_deep_dive} isLoading={false} />
                </div>
              )}

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <Gauge label="Confidence" value={result.scores?.confidence || 0} colorClass="text-emerald-500" />
                <Gauge label="Bias" value={result.scores?.bias || 0} colorClass="text-amber-500" />
                <Gauge label="Conflict" value={result.scores?.conflict || 0} colorClass="text-rose-500" />
                <Gauge label="Sensitivity" value={result.scores?.sensitivity || 0} colorClass="text-purple-500" />
                <Gauge label="AI-Risk" value={result.scores?.ai_risk || 0} colorClass="text-orange-500" />
                <Gauge label="Recency" value={result.scores?.recency || 0} colorClass="text-blue-500" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </motion.div>
  );
}
