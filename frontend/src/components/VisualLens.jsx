import React from 'react';
import { Shield, ShieldAlert, ShieldCheck, Loader2, Image as ImageIcon } from 'lucide-react';

export default function VisualLens({ result, isLoading }) {
  if (isLoading) {
    return (
      <div className="glass-card p-12 text-center">
        <Loader2 className="w-8 h-8 animate-spin text-brand-400 mx-auto mb-4" />
        <p className="text-gray-400">Analyzing image with AI vision model...</p>
        <p className="text-gray-600 text-sm mt-2">This may take 10-30 seconds on first use</p>
      </div>
    );
  }
  if (!result) {
    return (
      <div className="glass-card p-12 text-center space-y-4">
        <ImageIcon className="w-12 h-12 text-gray-600 mx-auto" />
        <div>
          <h3 className="text-lg font-medium text-gray-300">Visual Lens</h3>
          <p className="text-gray-500 mt-2">Upload an image to detect AI-generated content, deepfakes, or manipulated media.</p>
        </div>
        <div className="text-sm text-gray-600 space-y-1">
          <p>Detects: AI-Generated | Deepfake | Morphed | Real</p>
          <p>Model: prithivMLmods/AI-vs-Deepfake-vs-Real-Siglip2</p>
        </div>
      </div>
    );
  }
  if (result.status === 'failed' || result.error) {
    return (
      <div className="glass-card p-8 text-center space-y-3">
        <ShieldAlert className="w-10 h-10 text-red-400 mx-auto" />
        <h3 className="text-lg font-medium text-red-400">Analysis Failed</h3>
        <p className="text-gray-400 text-sm">{result.error}</p>
      </div>
    );
  }
  const label = result.label || 'Unknown';
  const confidence = (result.confidence || 0) * 100;
  const getStatusConfig = (lbl) => {
    const l = lbl.toLowerCase();
    if (l.includes('real') || l.includes('authentic')) return { color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30', icon: ShieldCheck };
    if (l.includes('deepfake') || l.includes('ai-generated') || l.includes('fake') || l.includes('synthetic')) return { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', icon: ShieldAlert };
    if (l.includes('morphed') || l.includes('manipulated')) return { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', icon: Shield };
    return { color: 'text-gray-400', bg: 'bg-gray-500/10', border: 'border-gray-500/30', icon: Shield };
  };
  const config = getStatusConfig(label);
  const StatusIcon = config.icon;
  return (
    <div className="glass-card p-8 space-y-6 animate-fade-in">
      <div className={`flex items-center gap-4 p-4 rounded-xl border ${config.bg} ${config.border}`}>
        <StatusIcon className={`w-10 h-10 ${config.color}`} />
        <div>
          <h3 className={`text-xl font-bold ${config.color}`}>{label}</h3>
          <p className="text-gray-400 text-sm">Confidence: {confidence.toFixed(1)}% | Model: {result.model_used}</p>
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Confidence Score</span>
          <span className={`${config.color} font-medium`}>{confidence.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-white/5 rounded-full h-2.5">
          <div className={`h-2.5 rounded-full transition-all duration-1000 ${confidence > 70 ? 'bg-green-500' : confidence > 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
            style={{ width: `${Math.min(confidence, 100)}%` }} />
        </div>
      </div>
      {result.all_predictions && result.all_predictions.length > 1 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-400">All Predictions</h4>
          <div className="space-y-2">
            {result.all_predictions.slice(0, 5).map((pred, i) => {
              const pLabel = typeof pred === 'object' ? pred.label : pred[0];
              const pScore = (typeof pred === 'object' ? pred.score : pred[1]) * 100;
              const pConfig = getStatusConfig(pLabel);
              return (
                <div key={i} className="flex items-center gap-3">
                  <span className={`text-xs font-medium px-2 py-1 rounded ${pConfig.bg} ${pConfig.color}`}>{pLabel}</span>
                  <div className="flex-1 bg-white/5 rounded-full h-1.5">
                    <div className="h-1.5 rounded-full bg-gray-400" style={{ width: `${pConf}%` }} />
                  </div>
                  <span className="text-xs text-gray-500 w-12 text-right">{pScore.toFixed(1)}%</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
      {result.metadata?.format && (
        <div className="flex items-center gap-4 text-xs text-gray-500 pt-2 border-t border-white/5">
          <span>Format: {result.metadata.format}</span>
          {result.compute_time_ms && <span>Analysis: {result.compute_time_ms}ms</span>}
        </div>
      )}
    </div>
  );
}
