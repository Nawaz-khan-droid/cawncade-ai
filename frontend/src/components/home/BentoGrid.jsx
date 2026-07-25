import React from 'react';
import { Target, Shield, ImageIcon, FileText, PieChart, Zap } from 'lucide-react';

export default function BentoGrid() {
  const features = [
    {
      title: "Multi-Vector Analysis",
      description: "", // Removed from here, handled in customNode
      icon: <Target size={24} className="text-blue-500" />,
      colSpan: "md:col-span-2 md:row-span-2",
      bgClass: "bg-gradient-to-br from-blue-50 to-white dark:from-slate-900 dark:to-slate-950",
      accentGlow: "bg-blue-500/5 dark:bg-blue-500/10",
      customNode: (
        <div className="flex flex-col w-full mt-2">
          <p className="text-slate-600 dark:text-slate-400 leading-relaxed text-lg mb-8">
            Simultaneously scores Confidence, Bias, Conflict, Sensitivity, AI-Risk, and Recency using ML inference on retrieved live sources — not static databases.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6 w-full">
            {[
              { label: 'Confidence', score: 72, color: 'bg-emerald-500', desc: 'How well-grounded the verdict is across all sources.' },
              { label: 'Bias', score: 18, color: 'bg-amber-500', desc: 'Detected leaning. Lower is more neutral.' },
              { label: 'Conflict', score: 34, color: 'bg-orange-500', desc: 'Disagreement between sources.' },
              { label: 'Sensitivity', score: 55, color: 'bg-rose-500', desc: 'Potential real-world impact of the claim.' },
              { label: 'AI-Risk', score: 12, color: 'bg-blue-500', desc: 'Likelihood the content is AI-generated.' },
              { label: 'Recency', score: 88, color: 'bg-emerald-400', desc: 'How fresh the supporting evidence is.' }
            ].map((metric, i) => (
              <div key={i} className="flex flex-col gap-1.5 w-full">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-widest">
                  <span>{metric.label}</span>
                  <span>{metric.score}%</span>
                </div>
                <div className="h-2 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${metric.color} rounded-full`} 
                    style={{ width: `${metric.score}%` }} 
                  />
                </div>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                  {metric.desc}
                </span>
              </div>
            ))}
          </div>
        </div>
      )
    },
    {
      title: "Reliability Matrix",
      description: "Six animated semi-circular gauges visualize each metric at-a-glance. Color-coded automatically.",
      icon: <PieChart size={24} className="text-emerald-500" />,
      colSpan: "col-span-1",
      bgClass: "bg-white dark:bg-slate-900",
      accentGlow: "bg-emerald-500/5 dark:bg-emerald-500/10"
    },
    {
      title: "Source Verification Feed",
      description: "Retrieves and ranks articles from authoritative domains with publish recency badges.",
      icon: <Shield size={24} className="text-purple-500" />,
      colSpan: "col-span-1",
      bgClass: "bg-white dark:bg-slate-900",
      accentGlow: "bg-purple-500/5 dark:bg-purple-500/10"
    },
    {
      title: "Context Synthesis (RAG)",
      description: "An LLM synthesizes retrieved evidence into a structured intelligence brief — citing sources inline, never fabricating claims.",
      icon: <FileText size={24} className="text-amber-500" />,
      colSpan: "md:col-span-2",
      bgClass: "bg-gradient-to-tr from-amber-50 to-white dark:from-slate-900 dark:to-slate-950",
      accentGlow: "bg-amber-500/5 dark:bg-amber-500/10"
    },
    {
      title: "VisualLens™ Image Analysis",
      description: "Upload any image to detect AI-generation or deepfakes. Returns a confidence score and heatmap.",
      icon: <ImageIcon size={24} className="text-cyan-500" />,
      colSpan: "col-span-1",
      bgClass: "bg-white dark:bg-slate-900",
      accentGlow: "bg-cyan-500/5 dark:bg-cyan-500/10"
    },
    {
      title: "Real-Time Processing",
      description: "FastAPI ML inference pipeline returns results in under 10 seconds.",
      icon: <Zap size={24} className="text-rose-500" />,
      colSpan: "md:col-span-3",
      bgClass: "bg-gradient-to-r from-white via-rose-50 to-white dark:from-slate-900 dark:via-slate-800 dark:to-slate-900",
      accentGlow: "bg-rose-500/5 dark:bg-rose-500/10"
    }
  ];

  return (
    <section id="features" className="py-24 px-6 bg-slate-50 dark:bg-slate-950 transition-colors duration-300">
      <div className="max-w-7xl mx-auto">
        
        <div className="mb-16 md:mb-20">
          <span className="inline-block px-3 py-1 mb-4 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-mono text-xs font-bold tracking-widest uppercase border border-blue-200 dark:border-blue-800/50">
            Capabilities
          </span>
          <h2 className="font-display text-4xl md:text-5xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight leading-tight max-w-2xl">
            Six vectors. One verdict.
          </h2>
          <p className="mt-4 text-lg text-slate-600 dark:text-slate-400 max-w-xl leading-relaxed">
            Every analysis triangulates across confidence, bias, conflict, sensitivity, AI-generation risk, and source recency — simultaneously.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-[minmax(200px,auto)]">
          {features.map((feature, idx) => (
            <div 
              key={idx} 
              className={`
                group relative p-8 rounded-3xl border border-slate-200 dark:border-slate-800 
                ${feature.colSpan} ${feature.bgClass}
                hover:-translate-y-1 hover:shadow-xl hover:shadow-slate-200/50 dark:hover:shadow-black/50 
                transition-all duration-300 overflow-hidden flex flex-col justify-between gap-6
              `}
            >
              {/* Subtle background glow effect on hover */}
              <div className={`absolute top-0 right-0 w-32 h-32 ${feature.accentGlow} rounded-full blur-3xl group-hover:scale-150 transition-transform duration-500`} />
              
              <div className="relative z-10 flex items-center justify-center w-14 h-14 rounded-2xl bg-white dark:bg-slate-950 border border-slate-100 dark:border-slate-800 shadow-sm">
                {feature.icon}
              </div>
              
              <div className="relative z-10 flex-1">
                <h3 className="font-display text-xl font-bold text-slate-900 dark:text-slate-50 mb-3 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  {feature.description}
                </p>
                {feature.customNode && feature.customNode}
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
