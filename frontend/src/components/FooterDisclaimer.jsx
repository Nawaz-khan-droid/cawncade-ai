import React from 'react';
import { Info } from 'lucide-react';

export default function FooterDisclaimer() {
  return (
    <footer className="mt-auto py-8 border-t border-white/5 bg-surface-900/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 flex flex-col items-center text-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-brand-500/10 text-primary mb-2">
          <Info className="w-4 h-4" />
        </div>
        <p className="text-sm text-text-muted max-w-3xl leading-relaxed">
          <strong className="text-white font-medium">Disclaimer:</strong> CAWNCADE AI provides probabilistic insights based on retrieved data and multi-vector analysis. It does not determine absolute truth. Results should be used to assist human judgment, not replace it.
        </p>
        <p className="text-xs text-text-muted/50 mt-2">
          &copy; {new Date().getFullYear()} CAWNCADE AI Platform. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
