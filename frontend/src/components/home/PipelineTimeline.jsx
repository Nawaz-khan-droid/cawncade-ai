import React, { useState } from 'react';
import { Database, Search, Scale, FileOutput } from 'lucide-react';

export default function PipelineTimeline() {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      title: "Data Ingestion",
      description: "Submit a claim, raw text, or a URL. The engine breaks it down into discrete factual assertions.",
      icon: <Database size={20} />,
      activeBg: "bg-blue-500",
      activeShadow: "shadow-blue-500/50",
      activeText: "text-blue-600 dark:text-blue-400"
    },
    {
      title: "Web Verification",
      description: "Agents parallel-search authoritative news, journals, and databases to retrieve context.",
      icon: <Search size={20} />,
      activeBg: "bg-purple-500",
      activeShadow: "shadow-purple-500/50",
      activeText: "text-purple-600 dark:text-purple-400"
    },
    {
      title: "Cross-Examination",
      description: "ML models weigh evidence for bias, conflict, and recency, assigning confidence scores.",
      icon: <Scale size={20} />,
      activeBg: "bg-amber-500",
      activeShadow: "shadow-amber-500/50",
      activeText: "text-amber-600 dark:text-amber-400"
    },
    {
      title: "Report Generation",
      description: "A synthesized intelligence brief is rendered with inline citations and a final verdict.",
      icon: <FileOutput size={20} />,
      activeBg: "bg-emerald-500",
      activeShadow: "shadow-emerald-500/50",
      activeText: "text-emerald-600 dark:text-emerald-400"
    }
  ];

  return (
    <section id="how-it-works" className="py-24 px-6 bg-white dark:bg-slate-900 transition-colors duration-300">
      <div className="max-w-4xl mx-auto">
        
        <div className="text-center mb-16 md:mb-24">
          <span className="inline-block px-3 py-1 mb-4 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono text-xs font-bold tracking-widest uppercase border border-slate-200 dark:border-slate-700">
            Pipeline Architecture
          </span>
          <h2 className="font-display text-4xl md:text-5xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight">
            How it Works
          </h2>
        </div>

        <div className="relative">
          {/* Vertical Line */}
          <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-px bg-slate-200 dark:bg-slate-800 -translate-x-1/2" />

          <div className="flex flex-col gap-12">
            {steps.map((step, idx) => {
              const isActive = idx === activeStep;
              const isEven = idx % 2 === 0;

              return (
                <div 
                  key={idx}
                  onMouseEnter={() => setActiveStep(idx)}
                  className={`relative flex items-center justify-between w-full cursor-default ${
                    isEven ? 'md:flex-row-reverse' : 'md:flex-row'
                  } flex-row`}
                >
                  {/* Empty space for alternating layout on Desktop */}
                  <div className="hidden md:block w-5/12" />

                  {/* Icon Node */}
                  <div className="absolute left-8 md:left-1/2 -translate-x-1/2 flex items-center justify-center">
                    <div className={`
                      w-12 h-12 rounded-full border-4 border-white dark:border-slate-900 flex items-center justify-center z-10 transition-all duration-300
                      ${isActive 
                        ? `${step.activeBg} text-white shadow-lg ${step.activeShadow} scale-110` 
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-400 border-slate-200 dark:border-slate-700'
                      }
                    `}>
                      {step.icon}
                    </div>
                  </div>

                  {/* Content Card */}
                  <div className="w-[calc(100%-5rem)] md:w-5/12 pl-16 md:pl-0">
                    <div className={`
                      p-6 rounded-2xl border transition-all duration-300
                      ${isActive 
                        ? 'bg-slate-50 dark:bg-slate-800/50 border-slate-300 dark:border-slate-700 shadow-xl' 
                        : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                      }
                    `}>
                      <span className={`font-mono text-xs font-bold tracking-wider uppercase mb-2 block ${isActive ? step.activeText : 'text-slate-400'}`}>
                        Step 0{idx + 1}
                      </span>
                      <h3 className="font-display text-xl font-bold text-slate-900 dark:text-slate-50 mb-3">
                        {step.title}
                      </h3>
                      <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  </div>

                </div>
              );
            })}
          </div>
        </div>

      </div>
    </section>
  );
}
