import React from 'react';
import ReactMarkdown from 'react-markdown';
import { AlertTriangle, CheckCircle, Info, Zap, Bot } from 'lucide-react';

export default function OutputPanel({ result }) {
  if (!result) return null;

  const { answer, context_summary, agreements, conflicts, sources_cited, confidence, scores, metadata, status, compute_time_ms } = result;

  const getConfidenceColor = (conf) => {
    if (conf >= 0.7) return 'text-emerald-400';
    if (conf >= 0.4) return 'text-amber-400';
    if (conf >= 0.2) return 'text-orange-400';
    return 'text-red-400';
  };

  const getConfidenceBg = (conf) => {
    if (conf >= 0.7) return 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/20';
    if (conf >= 0.4) return 'from-amber-500/20 to-amber-600/5 border-amber-500/20';
    if (conf >= 0.2) return 'from-orange-500/20 to-orange-600/5 border-orange-500/20';
    return 'from-red-500/20 to-red-600/5 border-red-500/20';
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Confidence Score Banner */}
      {status === 'completed' && (
        <div className={`glass-card p-4 bg-gradient-to-r ${getConfidenceBg(confidence)} border`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {confidence >= 0.7 ? (
                <CheckCircle className={`w-6 h-6 ${getConfidenceColor(confidence)}`} />
              ) : confidence >= 0.4 ? (
                <Info className={`w-6 h-6 ${getConfidenceColor(confidence)}`} />
              ) : (
                <AlertTriangle className={`w-6 h-6 ${getConfidenceColor(confidence)}`} />
              )}
              <div>
                <div className={`text-lg font-bold ${getConfidenceColor(confidence)}`}>
                  {(confidence * 100).toFixed(1)}% Confidence
                </div>
                <div className="text-sm text-gray-400">
                  {scores?.confidence_label || 'Unknown'}
                </div>
              </div>
            </div>
            <div className="text-right text-xs text-gray-500">
              {metadata?.sources_retrieved} sources | {compute_time_ms}ms
            </div>
          </div>
        </div>
      )}

      {/* Dynamic Disclaimers */}
      {scores?.dynamic_disclaimers?.length > 0 && (
        <div className="space-y-2">
          {scores.dynamic_disclaimers.map((d, i) => (
            <div key={i} className="flex items-start gap-2 px-3 py-2 bg-white/5 rounded-lg border border-white/5 text-sm">
              <Zap className="w-4 h-4 mt-0.5 text-amber-400 flex-shrink-0" />
              <span className="text-gray-300">{d}</span>
            </div>
          ))}
        </div>
      )}

      {/* AI Synthesis */}
      {answer && (
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Bot className="w-5 h-5 text-brand-400" />
            <h3 className="font-semibold text-white">Analysis</h3>
          </div>
          <div className="markdown-content">
            <ReactMarkdown>{answer}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Context Summary */}
      {context_summary && (
        <div className="glass-card p-4">
          <h4 className="text-sm font-medium text-gray-400 mb-2">Context Summary</h4>
          <p className="text-sm text-gray-300">{context_summary}</p>
        </div>
      )}

      {/* Agreements */}
      {agreements?.length > 0 && (
        <div className="glass-card p-4">
          <h4 className="text-sm font-medium text-emerald-400 mb-3 flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            Source Agreements ({agreements.length})
          </h4>
          <div className="space-y-2">
            {agreements.map((a, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="text-gray-300">{a.source_1}</span>
                <span className="text-gray-500">↔</span>
                <span className="text-gray-300">{a.source_2}</span>
                <span className="text-xs text-gray-500 ml-auto">
                  sim: {(a.similarity * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conflicts */}
      {conflicts?.length > 0 && (
        <div className="glass-card p-4 border-amber-500/20">
          <h4 className="text-sm font-medium text-amber-400 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Potential Conflicts ({conflicts.length})
          </h4>
          <div className="space-y-2">
            {conflicts.map((c, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="text-gray-300">{c.source_1}</span>
                <span className="text-gray-500">↔</span>
                <span className="text-gray-300">{c.source_2}</span>
                <span className="text-xs text-gray-500 ml-auto">
                  sim: {(c.similarity * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
