import React, { useState } from 'react';
import { Database, ChevronDown, ChevronUp, CheckCircle, XCircle } from 'lucide-react';
import clsx from 'clsx';

const SourceCard = ({ source, index }) => {
  const [expanded, setExpanded] = useState(false);
  
  // Is recency within 24 hours?
  const isRecent = (new Date() - new Date(source.publish_date)) < 86400000;
  
  return (
    <div id={`source-${index + 1}`} className="bg-surface-800 border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors flex flex-col gap-3">
      
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 overflow-hidden">
          <img 
            src={`https://www.google.com/s2/favicons?domain=${source.domain}&sz=32`} 
            alt={source.domain} 
            className="w-5 h-5 rounded-sm bg-white"
            onError={(e) => { e.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJjdXJyZW50Q29sb3IiIHN0cm9rZS13aWR0aD0iMiI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48L3N2Zz4=' }} // Fallback
          />
          <span className="text-sm font-medium text-text-muted truncate">{source.domain}</span>
        </div>
        
        {/* Badges */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {isRecent && (
            <span className="text-[10px] font-bold bg-brand-500/10 text-primary border border-primary/20 px-1.5 py-0.5 rounded uppercase tracking-wider">
              New
            </span>
          )}
          {source.fact_check_status === 'DEBUNKED' && (
            <span className="flex items-center gap-1 text-[10px] font-bold bg-alert/10 text-alert border border-alert/20 px-1.5 py-0.5 rounded uppercase tracking-wider">
              <XCircle className="w-3 h-3" /> Debunked
            </span>
          )}
          {source.fact_check_status === 'VERIFIED' && (
            <span className="flex items-center gap-1 text-[10px] font-bold bg-success/10 text-success border border-success/20 px-1.5 py-0.5 rounded uppercase tracking-wider">
              <CheckCircle className="w-3 h-3" /> Verified
            </span>
          )}
        </div>
      </div>

      {/* Title */}
      <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-slate-900 dark:text-white font-medium hover:text-primary transition-colors line-clamp-2">
        [{index + 1}] {source.title}
      </a>

      {/* Credibility Score */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-text-muted w-16">Credibility</span>
        <div className="flex-1 h-1.5 bg-surface-950 rounded-full overflow-hidden">
          <div 
            className={clsx(
              "h-full rounded-full",
              source.credibility_score > 0.7 ? "bg-success" : source.credibility_score > 0.4 ? "bg-warning" : "bg-alert"
            )} 
            style={{ width: `${Math.max(5, source.credibility_score * 100)}%` }}
          />
        </div>
        <span className="text-xs font-semibold text-slate-900 dark:text-white">{Math.round(source.credibility_score * 100)}%</span>
      </div>

      {/* Expandable Content */}
      <div className="mt-2 pt-3 border-t border-white/5 relative">
        <p className={clsx("text-sm text-text-muted leading-relaxed", !expanded && "line-clamp-2")}>
          {source.content}
        </p>
        
        <button 
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-primary hover:text-primary-hover font-medium mt-2 transition-colors"
        >
          {expanded ? (
            <><ChevronUp className="w-3 h-3" /> Show Less</>
          ) : (
            <><ChevronDown className="w-3 h-3" /> Expand Context</>
          )}
        </button>
      </div>

    </div>
  );
};

export default function SourceFeed({ sources, isLoading }) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 h-full flex flex-col gap-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-5 h-5 bg-surface-700 rounded animate-pulse"></div>
          <div className="h-6 w-32 bg-surface-700 rounded animate-pulse"></div>
        </div>
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-32 bg-surface-800 rounded-xl border border-white/5 animate-pulse"></div>
        ))}
      </div>
    );
  }

  if (!sources || sources.length === 0) return null;

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <Database className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Source Verification</h2>
        </div>
        <span className="text-xs text-text-muted">{sources.length} Retrieved</span>
      </div>
      
      <div className="flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar" style={{ maxHeight: '600px' }}>
        {sources.map((source, idx) => (
          <SourceCard key={idx} source={source} index={idx} />
        ))}
      </div>
    </div>
  );
}
