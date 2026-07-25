import React from 'react';
import { Link } from 'react-router-dom';

export default function HomeFooter() {
  return (
    <footer className="bg-[#0b101e] border-t border-slate-800 pt-16 pb-8 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-6 lg:px-12">
        
        {/* Main Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 lg:gap-8 mb-16">
          
          {/* Col 1 */}
          <div className="flex flex-col gap-4">
            <h3 className="font-display font-bold text-sm tracking-widest text-blue-500 uppercase">
              CAWNCADE AI
            </h3>
            <p className="text-[13px] text-slate-400 leading-relaxed font-sans max-w-xs">
              Context Aware Watch News Confirmation Authenticity Detection Engine. Results are grounded in live web sources and fact-check data. They support human judgment, never replace it.
            </p>
          </div>

          {/* Col 2 */}
          <div className="flex flex-col gap-4">
            <h3 className="font-display font-semibold text-xs tracking-widest text-slate-500 uppercase">
              Platform
            </h3>
            <ul className="flex flex-col gap-3">
              <li><a href="#features" className="text-[13px] text-slate-400 hover:text-blue-400 transition-colors">Features</a></li>
              <li><a href="#how-it-works" className="text-[13px] text-slate-400 hover:text-blue-400 transition-colors">How it works</a></li>
              <li><a href="#faq" className="text-[13px] text-slate-400 hover:text-blue-400 transition-colors">FAQ</a></li>
            </ul>
          </div>

          {/* Col 3 */}
          <div className="flex flex-col gap-4">
            <h3 className="font-display font-semibold text-xs tracking-widest text-slate-500 uppercase">
              Modules
            </h3>
            <ul className="flex flex-col gap-3">
              <li><Link to="/context-lens" className="text-[13px] text-slate-400 hover:text-blue-400 transition-colors">ContextLens</Link></li>
              <li><Link to="/visual-lens" className="text-[13px] text-slate-400 hover:text-blue-400 transition-colors">VisualLens</Link></li>
              <li><Link to="/agent-chat" className="text-[13px] text-slate-400 hover:text-blue-400 transition-colors">Agent Chat</Link></li>
            </ul>
          </div>

          {/* Col 4 */}
          <div className="flex flex-col gap-4">
            <h3 className="font-display font-semibold text-xs tracking-widest text-slate-500 uppercase">
              Disclaimer
            </h3>
            <p className="text-[13px] text-slate-400 leading-relaxed font-sans max-w-xs">
              CAWNCADE AI grounds every result in live web sources and fact-check data. It does not determine absolute truth. Always exercise independent judgment.
            </p>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-8 border-t border-slate-800/60">
          <p className="text-xs font-mono text-slate-500">
            © {new Date().getFullYear()} CAWNCADE AI · Cited verdicts from live web evidence
          </p>
          <span className="text-xs font-mono text-slate-600 tracking-wider">
            v1.0.0
          </span>
        </div>

      </div>
    </footer>
  );
}
