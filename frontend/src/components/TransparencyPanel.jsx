import React from 'react';
import { Globe, Shield, Clock, Layers, AlertTriangle } from 'lucide-react';

export default function TransparencyPanel({ tierStats, factCheck, extraction, inputType }) {
  if (!tierStats && !factCheck && !extraction) return null;

  const getTierLabel = (key) => {
    const labels = {
      tier_1_google_cse_walled_garden: { label: 'Google CSE (50-Site Walled Garden)', color: 'text-green-400' },
      tier_1_google_trusted: { label: 'Google Trusted Sites', color: 'text-green-400' },
      tier_2_tavily_global: { label: 'Tavily AI Search (Global)', color: 'text-blue-400' },
      tier_2_tavily: { label: 'Tavily AI Search', color: 'text-blue-400' },
      tier_3_newsdata: { label: 'NewsData.io', color: 'text-purple-400' },
      tier_3_newsapi: { label: 'NewsAPI.org', color: 'text-purple-400' },
      tier_4_duckduckgo: { label: 'DuckDuckGo (Unlimited)', color: 'text-orange-400' },
      tier_5_google_news_rss: { label: 'Google News RSS', color: 'text-gray-400' },
      tier_5_google_news: { label: 'Google News RSS', color: 'text-gray-400' },
      tier_5_gdelt: { label: 'GDELT', color: 'text-gray-400' },
    };
    return labels[key] || { label: key, color: 'text-gray-500' };
  };

  return (
    <div className="glass-card p-5 space-y-4">
      <h4 className="text-sm font-medium text-gray-400 flex items-center gap-2">
        <Shield className="w-4 h-4" />
        Verification Transparency
      </h4>
      {extraction && (
        <div className="space-y-1">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Input Method</p>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-brand-400">{inputType === 'url' ? 'URL Analysis' : inputType === 'youtube' ? 'YouTube Transcript' : 'Text Input'}</span>
            <span className="text-gray-600">-</span>
            <span className="text-gray-300">{extraction.method?.replace(/_/g, ' ') || extraction.method}</span>
          </div>
          {extraction.title && <p className="text-xs text-gray-500 truncate">Source: {extraction.title}</p>}
          {extraction.safety_warning && (
            <p className="text-xs text-red-400">Safety Warning: {Array.isArray(extraction.safety_warning) ? extraction.safety_warning.join(', ') : extraction.safety_warning}</p>
          )}
        </div>
      )}
      {factCheck && factCheck.total > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Fact Check API</p>
          <p className="text-sm text-yellow-400">Found {factCheck.total} existing fact-check(s) {factCheck.cached && '(cached)'}</p>
        </div>
      )}
      {tierStats && Object.keys(tierStats).length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Search Sources Used</p>
          <div className="grid grid-cols-2 gap-1">
            {Object.entries(tierStats).map(([key, value]) => {
              const tier = getTierLabel(key);
              return (
                <div key={key} className="flex items-center gap-2 text-xs">
                  <div className={`w-1.5 h-1.5 rounded-full ${tier.color.replace('text-', 'bg-')}`} />
                  <span className="text-gray-400">{tier.label}:</span>
                  <span className="text-gray-300 font-medium">{value}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
      <div className="pt-2 border-t border-white/5 text-xs text-gray-600 space-y-0.5">
        <p>Green = Trusted sources | Blue = AI-enhanced | Orange = Free fallback</p>
        <p>Higher tier = Higher confidence in source reliability</p>
      </div>
    </div>
  );
}
