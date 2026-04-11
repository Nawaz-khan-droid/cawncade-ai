import React from 'react';

export default function MetricsPanel({ scores }) {
  if (!scores) return null;

  const metrics = [
    { label: 'Confidence', value: (scores.confidence_score || 0) * 100, suffix: '%', color: 'bg-brand-500' },
    { label: 'Credibility', value: (scores.credibility_avg || 0) * 100, suffix: '%', color: 'bg-green-500' },
    { label: 'Agreement', value: (scores.agreement_score || 0) * 100, suffix: '%', color: 'bg-blue-500' },
    { label: 'Diversity', value: (scores.diversity_score || 0) * 100, suffix: '%', color: 'bg-purple-500' },
    { label: 'Recency', value: (scores.recency_score || 0) * 100, suffix: '%', color: 'bg-yellow-500' },
    { label: 'Grounding', value: (scores.grounding_score || 0) * 100, suffix: '%', color: 'bg-teal-500' },
  ];

  return (
    <div className="glass-card p-5 space-y-4">
      <h4 className="text-sm font-medium text-gray-400">CAWNCADE Scores</h4>
      <div className="space-y-3">
        {metrics.map(({ label, value, color }) => (
          <div key={label} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">{label}</span>
              <span className="text-gray-300 font-medium">{value.toFixed(1)}{suffix}</span>
            </div>
            <div className="w-full bg-white/5 rounded-full h-1.5">
              <div className={`h-1.5 rounded-full ${color} transition-all duration-1000`} style={{ width: `${Math.min(value, 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
      {scores.confidence_label && (
        <p className="text-xs text-gray-500 pt-2 border-t border-white/5">{scores.confidence_label}</p>
      )}
      {scores.dynamic_disclaimers && scores.dynamic_disclaimers.length > 0 && (
        <div className="space-y-1 pt-2 border-t border-white/5">
          {scores.dynamic_disclaimers.map((d, i) => (
            <p key={i} className="text-xs text-yellow-500/80">{d}</p>
          ))}
        </div>
      )}
    </div>
  );
}
