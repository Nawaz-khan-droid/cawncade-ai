import React from 'react';
import clsx from 'clsx';
import { ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react';

const RadialGauge = ({ value, label, type = 'standard' }) => {
  // Determine colors based on type (risk vs confidence)
  // type 'risk': High value = Red, Low value = Green
  // type 'confidence': High value = Green, Low value = Red
  
  let colorClass = 'text-primary';
  let Icon = null;
  
  if (type === 'risk') {
    if (value > 0.7) { colorClass = 'text-alert'; Icon = ShieldAlert; }
    else if (value > 0.4) { colorClass = 'text-warning'; Icon = AlertTriangle; }
    else { colorClass = 'text-success'; Icon = ShieldCheck; }
  } else {
    if (value > 0.7) { colorClass = 'text-success'; Icon = ShieldCheck; }
    else if (value > 0.4) { colorClass = 'text-warning'; Icon = AlertTriangle; }
    else { colorClass = 'text-alert'; Icon = ShieldAlert; }
  }

  // SVG calculations for a semi-circle
  const radius = 40;
  const circumference = radius * Math.PI;
  const strokeDashoffset = circumference - (value * circumference);
  const percentage = Math.round(value * 100);

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-surface-800 rounded-xl border border-white/5 relative group hover:border-white/10 transition-colors">
      <div className="relative w-32 h-20 overflow-hidden flex justify-center items-end pb-2">
        <svg 
          className="absolute top-0 w-32 h-32 transform -rotate-180" 
          viewBox="0 0 100 100"
          aria-label={`${label} Score: ${percentage}%`}
          role="img"
        >
          {/* Background Track */}
          <circle
            cx="50" cy="50" r={radius}
            fill="transparent"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth="10"
            strokeDasharray={`${circumference} ${circumference}`}
            strokeLinecap="round"
          />
          {/* Progress Arc */}
          <circle
            cx="50" cy="50" r={radius}
            fill="transparent"
            stroke="currentColor"
            strokeWidth="10"
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className={clsx("transition-all duration-1000 ease-out drop-shadow-md", colorClass)}
          />
        </svg>
        <div className="flex flex-col items-center leading-none z-10 translate-y-3">
          <span className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">{percentage}%</span>
        </div>
      </div>
      <div className="flex items-center gap-1.5 mt-4">
        {Icon && <Icon className={clsx("w-3.5 h-3.5", colorClass)} />}
        <span className="metric-label !mt-0 !w-auto">{label}</span>
      </div>
    </div>
  );
};

export default function ReliabilityMatrix({ scores, isLoading }) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 md:p-8">
        <div className="h-6 w-48 bg-surface-700 rounded animate-pulse mb-6"></div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-32 bg-surface-800 rounded-xl border border-white/5 animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!scores) return null;

  return (
    <div className="glass-card p-6 md:p-8">
      <h2 className="text-xl font-semibold mb-6 flex items-center gap-2 text-slate-900 dark:text-white">
        Reliability Matrix
        <span className="text-xs font-normal text-text-muted bg-surface-800 px-2 py-1 rounded-md border border-white/10">Multivector Analysis</span>
      </h2>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <RadialGauge value={scores.confidence_score || 0} label="Confidence" type="confidence" />
        <RadialGauge value={scores.credibility_avg || 0} label="Credibility" type="confidence" />
        <RadialGauge value={scores.recency_score || 0} label="Recency" type="confidence" />
        <RadialGauge value={scores.conflict_score || 0} label="Conflict" type="risk" />
        <RadialGauge value={scores.ai_risk_score || 0} label="AI Risk" type="risk" />
        <RadialGauge value={scores.sensitivity_score || 0} label="Sensitivity" type="risk" />
      </div>
    </div>
  );
}
