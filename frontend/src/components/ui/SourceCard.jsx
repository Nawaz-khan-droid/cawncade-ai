import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, HelpCircle } from 'lucide-react';

export default function SourceCard({ src }) {
  if (!src) return null;

  const lowerSnippet = (src.snippet || '').toLowerCase();

  // 4-State Classification: Supports, Contradicts, Related, Insufficient
  let stateConfig = {
    label: "Related News",
    badgeClass: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    icon: AlertTriangle,
    findingText: "Discusses related news; does not report that the claim occurred.",
  };

  if (src.stance === "CONTRADICTS" || lowerSnippet.includes("debunk") || lowerSnippet.includes("fake") || lowerSnippet.includes("false") || lowerSnippet.includes("untrue")) {
    stateConfig = {
      label: "Contradicts Claim",
      badgeClass: "bg-rose-500/15 text-rose-300 border-rose-500/30",
      icon: XCircle,
      findingText: "Explicitly refutes or debunks this claim.",
    };
  } else if (src.stance === "SUPPORTS" || src.is_trusted || lowerSnippet.includes("created by") || lowerSnippet.includes("launched") || lowerSnippet.includes("located in") || lowerSnippet.includes("official") || lowerSnippet.includes("confirm")) {
    stateConfig = {
      label: "Supports Claim",
      badgeClass: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
      icon: CheckCircle2,
      findingText: "Corroborates key claim entities with reference coverage.",
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
      href={src.url}
      target="_blank"
      rel="noopener noreferrer"
      className="p-3.5 md:p-4 rounded-xl bg-surface-light/60 dark:bg-surface-dark/60 border border-borderBase-light dark:border-borderBase-dark hover:border-primary/40 transition-all flex flex-col gap-2 group focus:outline-none focus:ring-2 focus:ring-primary/50 min-w-0"
    >
      <div className="flex items-center justify-between gap-2 min-w-0">
        <span className="text-xs font-bold text-primary group-hover:underline truncate min-w-0 flex-1">
          {src.source_name || src.domain || 'Source'}
        </span>
        <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded shrink-0 ${
          src.is_trusted ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'
        }`}>
          {src.is_trusted ? '✓ TRUSTED' : src.trust_tier || 'NEWS'}
        </span>
      </div>

      <p className="text-xs font-semibold text-slate-200 line-clamp-2 leading-snug break-words">{src.title}</p>
      
      {/* 4-STATE FINDING STATUS BADGE (Natural Text Wrapping, 0 String Cuts) */}
      <div className={`text-[11px] p-2.5 rounded-lg border flex flex-col sm:flex-row sm:items-start gap-1 font-medium leading-relaxed ${stateConfig.badgeClass}`}>
        <div className="flex items-center gap-1.5 shrink-0">
          <StatusIcon className="w-3.5 h-3.5 shrink-0" />
          <span className="font-extrabold shrink-0">{stateConfig.label}:</span>
        </div>
        <span className="break-words opacity-95 leading-normal">{stateConfig.findingText}</span>
      </div>
    </a>
  );
}
