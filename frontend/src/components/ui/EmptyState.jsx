import React from 'react';
import { Search, HelpCircle, ArrowRight } from 'lucide-react';

export default function EmptyState({ 
  title = "No Corroborating Sources Found", 
  description = "No reliable web sources or official announcements were retrieved for this claim.",
  onSuggestionClick 
}) {
  return (
    <div className="glass-card p-6 md:p-8 rounded-2xl flex flex-col items-center text-center gap-4 border border-amber-500/20 bg-amber-500/5">
      <div className="p-3 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400">
        <HelpCircle className="w-8 h-8" />
      </div>

      <div className="flex flex-col gap-1 max-w-md">
        <h4 className="text-base font-bold text-slate-100">{title}</h4>
        <p className="text-xs text-slate-300 leading-relaxed">{description}</p>
      </div>

      <div className="w-full max-w-md p-4 rounded-xl bg-white/5 border border-white/5 flex flex-col gap-2 text-left text-xs">
        <span className="font-extrabold uppercase tracking-wider text-slate-400">Try Refining Your Search:</span>
        <ul className="space-y-1.5 text-slate-300 font-medium">
          <li className="flex items-center gap-2">
            <ArrowRight className="w-3 h-3 text-primary shrink-0" />
            <span>Use specific names or exact quote keywords</span>
          </li>
          <li className="flex items-center gap-2">
            <ArrowRight className="w-3 h-3 text-primary shrink-0" />
            <span>Paste a direct article URL instead of text</span>
          </li>
          <li className="flex items-center gap-2">
            <ArrowRight className="w-3 h-3 text-primary shrink-0" />
            <span>Shorten long social media posts to the core claim</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
