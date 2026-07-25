import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, ShieldCheck, Zap } from 'lucide-react';

export default function HeroSection() {
  const navigate = useNavigate();

  return (
    <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden flex flex-col items-center justify-center text-center px-6">
      {/* Background gradients for high-contrast minimalistic feel */}
      <div className="absolute inset-0 pointer-events-none bg-slate-50 dark:bg-slate-950 transition-colors duration-300" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-blue-500/10 dark:bg-blue-500/5 blur-[100px] rounded-full pointer-events-none" />
      
      <div className="relative z-10 max-w-4xl mx-auto flex flex-col items-center gap-8">
        
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 dark:bg-slate-900 border border-blue-200 dark:border-slate-800 text-blue-600 dark:text-blue-400 text-sm font-semibold tracking-wide">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          CONTEXT-AWARE INTELLIGENCE v2.1
        </div>

        <h1 className="font-display font-extrabold text-5xl md:text-7xl tracking-tight text-slate-900 dark:text-slate-50 leading-[1.1]">
          Decode Misinformation<br />
          <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
            With Precision.
          </span>
        </h1>

        <p className="text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed">
          CAWNCADE AI performs multi-vector contextual analysis across live web sources — identifying bias, conflict, AI-generation risk, and source credibility simultaneously.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 mt-4">
          <button 
            onClick={() => navigate('/context-lens')}
            className="group flex items-center justify-center gap-3 px-8 py-4 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-display font-bold text-lg transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-600/25 active:scale-95 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-500/50 w-full sm:w-auto"
          >
            Start Verifying
            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
          </button>
          
          <a 
            href="#features"
            className="flex items-center justify-center gap-3 px-8 py-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-display font-bold text-lg transition-all duration-200 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-50 active:scale-95 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-slate-500/50 w-full sm:w-auto"
          >
            View Capabilities
          </a>
        </div>

        <div className="flex flex-wrap justify-center gap-8 md:gap-16 mt-12 pt-8 border-t border-slate-200 dark:border-slate-800/50 w-full max-w-3xl">
          <div className="flex flex-col items-center gap-1">
            <div className="flex items-center gap-2 font-mono font-bold text-2xl text-slate-900 dark:text-slate-50">
              <ShieldCheck className="text-emerald-500" size={24} /> 99.1%
            </div>
            <span className="text-xs font-bold tracking-wider text-slate-500 uppercase">Source Accuracy</span>
          </div>
          <div className="flex flex-col items-center gap-1">
            <div className="flex items-center gap-2 font-mono font-bold text-2xl text-slate-900 dark:text-slate-50">
              <Zap className="text-amber-500" size={24} /> &lt;3s
            </div>
            <span className="text-xs font-bold tracking-wider text-slate-500 uppercase">Analysis Time</span>
          </div>
          <div className="flex flex-col items-center gap-1">
            <div className="flex items-center gap-2 font-mono font-bold text-2xl text-slate-900 dark:text-slate-50">
              <span className="text-blue-500">6</span>
            </div>
            <span className="text-xs font-bold tracking-wider text-slate-500 uppercase">Reliability Vectors</span>
          </div>
        </div>

      </div>
    </section>
  );
}
