import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';

export default function ErrorState({ 
  error = "Advanced verification is temporarily unavailable. We searched public web sources and generated the best available assessment.", 
  onRetry 
}) {
  return (
    <div className="p-4 rounded-xl bg-alert/10 border border-alert/20 text-alert flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs md:text-sm">
      <div className="flex items-center gap-2.5">
        <AlertCircle className="w-5 h-5 shrink-0 text-alert" />
        <span className="font-semibold">{error}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3 py-1.5 rounded-lg bg-alert/20 hover:bg-alert/30 text-alert border border-alert/30 font-bold flex items-center gap-1.5 transition-colors shrink-0 focus:outline-none focus:ring-2 focus:ring-alert/50"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
