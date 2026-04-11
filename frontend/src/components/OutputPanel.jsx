import React from 'react';

export default function OutputPanel({ result }) {
  if (!result) return null;
  const confidence = (result.confidence || 0) * 100;
  const getConfidenceColor = (c) => {
    if (c >= 80) return 'text-green-400';
    if (c >= 60) return 'text-blue-400';
    if (c >= 40) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="glass-card p-6 space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Analysis Result</h3>
        <span className={`text-sm font-medium ${getConfidenceColor(confidence)}`}>{confidence.toFixed(1)}% confidence</span>
      </div>
      {result.answer && (
        <div className="space-y-2">
          <h4 className="text-xs text-gray-500 uppercase tracking-wider">Summary</h4>
          <p className="text-gray-200 text-sm leading-relaxed">{result.answer}</p>
        </div>
      )}
      {result.context_summary && (
        <div className="space-y-2">
          <h4 className="text-xs text-gray-500 uppercase tracking-wider">Verification Context</h4>
          <p className="text-gray-300 text-sm leading-relaxed">{result.context_summary}</p>
        </div>
      )}
      {result.metadata?.input_type === 'url' && result.metadata?.extraction?.safety_warning && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
          <p className="text-red-400 text-xs">Safety Warning: {Array.isArray(result.metadata.extraction.safety_warning) ? result.metadata.extraction.safety_warning.join(', ') : result.metadata.extraction.safety_warning}</p>
        </div>
      )}
      {result.agreements && result.agreements.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs text-gray-500 uppercase tracking-wider">Corroborating Sources</h4>
          <div className="flex flex-wrap gap-2">
            {result.agreements.map((source, i) => (
              <span key={i} className="px-2 py-1 text-xs bg-green-500/10 text-green-400 rounded-full">{source}</span>
            ))}
          </div>
        </div>
      )}
      {result.compute_time_ms && (
        <p className="text-xs text-gray-600">Processed in {result.compute_time_ms}ms across {result.metadata?.sources_retrieved || 0} sources</p>
      )}
    </div>
  );
}
