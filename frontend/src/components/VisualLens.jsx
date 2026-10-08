import React from 'react';
import { Shield, ShieldAlert, ShieldCheck, Loader2, Image as ImageIcon } from 'lucide-react';

export default function VisualLens({ result, isLoading }) {
  if (isLoading) {
    return (
      <div className="glass-card p-12 text-center">
        <Loader2 className="w-8 h-8 animate-spin text-brand-400 mx-auto mb-4" />
        <p className="text-gray-400">Analyzing image with AI vision model...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="glass-card p-12 text-center space-y-4">
        <ImageIcon className="w-12 h-12 text-gray-600 mx-auto" />
        <div>
          <h3 className="text-lg font-medium text-gray-300">Visual Lens</h3>
          <p className="text-gray-500 mt-2">Upload an image to detect AI-generated content or deepfakes.</p>
        </div>
      </div>
    );
  }

  const getStatusConfig = (label) => {
    const l = label?.toLowerCase() || '';
    if (l.includes('real')) return { icon: ShieldCheck, color: 'text-green-400', bg: 'bg-green-500/10', label: 'Verified Real' };
    if (l.includes('deepfake') || l.includes('morphed')) return { icon: ShieldAlert, color: 'text-red-400', bg: 'bg-red-500/10', label: 'Manipulation Detected' };
    return { icon: Shield, color: 'text-yellow-400', bg: 'bg-yellow-500/10', label: 'AI Generated' };
  };

  const status = getStatusConfig(result.label);
  const confidence = (result.score || 0) * 100;

  return (
    <div className="glass-card p-6 animate-fade-in space-y-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-xl ${status.bg}`}><status.icon className={`w-6 h-6 ${status.color}`} /></div>
          <div>
            <h3 className="text-lg font-bold text-white">{status.label}</h3>
            <p className="text-xs text-gray-500">Classification</p>
          </div>
        </div>
        <div className="text-right">
          <span className={`text-xl font-bold ${status.color}`}>{confidence.toFixed(1)}%</span>
        </div>
      </div>

      {result.all_predictions && (
        <div className="space-y-3 pt-4 border-t border-white/5">
          <h4 className="text-xs font-semibold text-gray-500 uppercase">Detection Breakdown</h4>
          <div className="space-y-3">
            {result.all_predictions.slice(0, 5).map((pred, i) => {
              const pLabel = typeof pred === 'object' ? pred.label : pred[0];
              const pScore = (typeof pred === 'object' ? pred.score : pred[1]) * 100;
              return (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-gray-400">{pLabel}</span>
                    <span className="text-gray-500">{pScore.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-1">
                    {/* FIX: Changed pConf to pScore */}
                    <div className="h-full bg-brand-500 transition-all duration-700" style={{ width: `${pScore}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}