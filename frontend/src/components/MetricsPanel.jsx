import React from 'react';
import { Activity, Shield, Users, Clock, AlertTriangle, BarChart3 } from 'lucide-react';

export default function MetricsPanel({ scores }) {
  if (!scores) return null;

  const metrics = [
    { label: 'Credibility', value: scores.credibility_avg, icon: Shield, color: 'blue' },
    { label: 'Agreement', value: scores.agreement_score, icon: Users, color: 'green' },
    { label: 'Diversity', value: scores.diversity_score, icon: BarChart3, color: 'purple' },
    { label: 'Recency', value: scores.recency_score, icon: Clock, color: 'cyan' },
    { label: 'Grounding', value: scores.grounding_score, icon: Activity, color: 'amber' },
    { label: 'Conflict', value: scores.conflict_score, icon: AlertTriangle, color: 'red' },
  ];

  const getBarColor = (value, color) => {
    const colors = {
      blue: 'bg-blue-500',
      green: 'bg-emerald-500',
      purple: 'bg-purple-500',
      cyan: 'bg-cyan-500',
      amber: 'bg-amber-500',
      red: 'bg-red-500',
    };
    return colors[color] || 'bg-gray-500';
  };

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">Scoring Metrics</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {metrics.map((m) => (
          <div key={m.label} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <m.icon className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-400">{m.label}</span>
              </div>
              <span className="text-xs font-mono text-gray-300">
                {(m.value * 100).toFixed(1)}%
              </span>
            </div>
            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-1000 ease-out ${getBarColor(m.value, m.color)}`}
                style={{ width: `${(m.value * 100).toFixed(1)}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* TF-IDF Signal */}
      {scores.tfidf_suspicion_score !== undefined && (
        <div className="mt-4 pt-4 border-t border-white/5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">TF-IDF Suspicion Signal</span>
            <span className="text-xs font-mono text-gray-300">
              {(scores.tfidf_suspicion_score * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
