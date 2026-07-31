import React from 'react';
import { Loader2, Search, ShieldCheck, Cpu } from 'lucide-react';

export default function LoadingState({ message = "Analyzing Claim & Cross-Checking Tiers..." }) {
  return (
    <div className="glass-card p-6 md:p-8 rounded-2xl flex flex-col items-center justify-center gap-6 min-h-[220px]">
      <div className="relative flex items-center justify-center">
        <div className="w-14 h-14 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
        <Cpu className="w-6 h-6 text-primary absolute" />
      </div>

      <div className="flex flex-col items-center text-center gap-1.5 max-w-sm">
        <h4 className="text-base font-bold text-slate-900 dark:text-slate-100">{message}</h4>
        <p className="text-xs text-slate-600 dark:text-slate-400">Evaluating web sources, domain trust signatures, and vector index graphs...</p>
      </div>

      <div className="grid grid-cols-3 gap-3 w-full max-w-md pt-2 border-t border-white/5 text-xs text-slate-400 font-medium">
        <div className="flex items-center gap-1.5 justify-center">
          <Search className="w-3.5 h-3.5 text-primary animate-pulse" />
          <span>Searching</span>
        </div>
        <div className="flex items-center gap-1.5 justify-center">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span>Validating</span>
        </div>
        <div className="flex items-center gap-1.5 justify-center">
          <Loader2 className="w-3.5 h-3.5 text-sky-400 animate-spin" />
          <span>Synthesizing</span>
        </div>
      </div>
    </div>
  );
}
