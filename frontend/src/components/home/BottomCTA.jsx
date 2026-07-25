import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Play } from 'lucide-react';

export default function BottomCTA() {
  const navigate = useNavigate();

  return (
    <section className="py-24 px-6 bg-white dark:bg-slate-950 transition-colors duration-300">
      <div className="max-w-5xl mx-auto">
        <div className="relative w-full rounded-3xl bg-slate-900 dark:bg-slate-900 overflow-hidden px-6 py-20 md:py-32 flex flex-col items-center justify-center text-center border border-slate-800 shadow-2xl">
          
          {/* Decorative glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-2xl h-1/2 bg-blue-500/20 blur-[100px] pointer-events-none rounded-full" />
          
          <div className="relative z-10 flex flex-col items-center gap-6">
            <h2 className="font-display text-4xl md:text-5xl font-extrabold text-white tracking-tight leading-tight max-w-2xl">
              Start with a claim. <span className="text-blue-400">End with a cited verdict.</span>
            </h2>
            
            <p className="text-lg text-slate-400 max-w-xl">
              Run your first analysis in under a minute. No signup, no API key. The demo runs entirely in your browser.
            </p>

            <button 
              onClick={() => navigate('/context-lens')}
              className="mt-6 flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-display font-bold text-lg transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-cyan-500/25 active:scale-95 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-cyan-500/50"
            >
              <Play size={20} className="fill-current" />
              Analyze Context
            </button>
          </div>
          
        </div>
      </div>
    </section>
  );
}
