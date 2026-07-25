import React from 'react';
import { Activity, Settings } from 'lucide-react';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-surface/80 backdrop-blur-md border-b border-white/5 w-full">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        
        {/* Logo & Branding */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-tr from-primary to-cyan-400 flex items-center justify-center shadow-[0_0_15px_rgba(59,130,246,0.5)]">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            CAWNCADE <span className="text-primary font-medium">AI</span>
          </h1>
        </div>

        {/* Right Nav */}
        <div className="flex items-center gap-6">
          <div className="hidden sm:flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-success"></span>
            </span>
            <span className="text-sm font-medium text-text-muted">System Online</span>
          </div>
          
          <button className="p-2 text-text-muted hover:text-white transition-colors hover:bg-white/5 rounded-full" aria-label="Settings">
            <Settings className="w-5 h-5" />
          </button>
        </div>

      </div>
    </header>
  );
}