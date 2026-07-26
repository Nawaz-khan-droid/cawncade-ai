import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle, 
  Info, 
  Clock, 
  ShieldCheck, 
  Check, 
  ChevronDown, 
  ChevronUp 
} from 'lucide-react';

export default function ResultHero({ result }) {
  const [showMobileDetails, setShowMobileDetails] = useState(false);

  if (!result) return null;

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
    <div className={`p-4 md:p-6 rounded-2xl border ${themeConfig.stripe} ${themeConfig.borderColor} ${themeConfig.bgGradient} shadow-lg flex flex-col gap-3.5 transition-all`}>
      
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

      {/* Mobile Collapse Toggle Button (<768px) */}
      <div className="md:hidden">
        <button 
          onClick={() => setShowMobileDetails(!showMobileDetails)}
          className="text-xs font-bold text-slate-400 hover:text-slate-200 flex items-center gap-1 py-1 focus:outline-none focus:ring-1 focus:ring-primary/50 rounded"
          aria-expanded={showMobileDetails}
        >
          <span>{showMobileDetails ? 'Hide Verification Details' : 'Show Verification Details'}</span>
          {showMobileDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Why Bullets & Snapshot (Always visible on desktop, collapsible on mobile) */}
      <div className={`${showMobileDetails ? 'flex' : 'hidden md:flex'} flex-col gap-3 pt-2 border-t border-white/10`}>
        <div className="flex flex-col gap-1.5">
          <span className="text-[11px] font-extrabold uppercase tracking-wider text-slate-400">Why?</span>
          <ul className="text-xs space-y-1 list-disc list-inside text-slate-300 font-medium">
            {themeConfig.whyBullets.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </div>

        {/* EVIDENCE SNAPSHOT BADGES */}
        <div className="flex items-center gap-2 pt-2 border-t border-white/10 flex-wrap text-xs font-medium text-slate-300">
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
    </div>
  );
}
