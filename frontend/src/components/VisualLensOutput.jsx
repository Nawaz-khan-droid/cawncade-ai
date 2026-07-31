import React from 'react';
import { Image as ImageIcon, ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

export default function VisualLensOutput({ result, isLoading }) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 md:p-8 h-full">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-5 h-5 bg-surface-700 rounded animate-pulse"></div>
          <div className="h-6 w-48 bg-surface-700 rounded animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="aspect-square bg-surface-700 rounded-xl animate-pulse"></div>
          <div className="flex flex-col gap-6">
            <div className="h-24 bg-surface-800 rounded-xl animate-pulse"></div>
            <div className="h-32 bg-surface-800 rounded-xl animate-pulse"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!result) return null;

  const isFake = result.classification?.toLowerCase().includes('ai') || result.classification?.toLowerCase().includes('deepfake');
  const Icon = isFake ? ShieldAlert : ShieldCheck;
  const colorClass = isFake ? 'text-alert' : 'text-success';
  const bgColorClass = isFake ? 'bg-alert/10 border-alert/20' : 'bg-success/10 border-success/20';

  return (
    <div className="glass-card p-6 md:p-8">
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/5">
        <ImageIcon className="w-5 h-5 text-primary" />
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">VisualLens Analysis</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left: Image Preview */}
        <div className="relative rounded-xl overflow-hidden border border-white/10 bg-surface-900 group">
          {result.imageUrl ? (
            <img 
              src={result.imageUrl} 
              alt="Analyzed subject" 
              className="w-full h-auto object-contain max-h-[500px]"
            />
          ) : (
            <div className="w-full aspect-square flex flex-col items-center justify-center text-text-muted">
              <ImageIcon className="w-12 h-12 mb-2 opacity-50" />
              <span>Image not provided by backend</span>
            </div>
          )}
          
          {/* Overlay scanning effect */}
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/20 to-transparent opacity-0 group-hover:opacity-100 group-hover:animate-scan pointer-events-none"></div>
        </div>

        {/* Right: Results */}
        <div className="flex flex-col gap-6">
          
          <div className={clsx("p-6 rounded-xl border flex flex-col items-center justify-center text-center gap-3", bgColorClass)}>
            <div className={clsx("p-3 rounded-full bg-surface-900 shadow-lg", colorClass)}>
              <Icon className="w-8 h-8" />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white uppercase tracking-wider">{result.classification}</h3>
            <p className="text-sm font-medium text-text-muted">
              Confidence: <span className={clsx("font-bold text-lg", colorClass)}>{Math.round((result.confidence || 0) * 100)}%</span>
            </p>
          </div>

          <div className="bg-surface-800 rounded-xl p-6 border border-white/5">
            <h4 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning" /> Forensic Details
            </h4>
            <p className="text-text-muted text-sm leading-relaxed">
              {result.details || "No significant artifacts detected. The image appears to be naturally captured with no obvious signs of generative AI upscaling or deepfake manipulation signatures."}
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
