import React from 'react';
import { Globe, Shield, Clock, Layers } from 'lucide-react';

export default function TransparencyPanel({ tierStats, factCheck, extraction, inputType }) {
  if (!tierStats && !factCheck && !extraction) return null;

  const getTierLabel = (key) => {
    const labels = {
      serper: { label: 'Serper.dev (Google Proxy)', color: 'text-green-400' },
      tavily: { label: 'Tavily (Deep Research)', color: 'text-blue-400' },
      you_com: { label: 'You.com (AI Search)', color: 'text-teal-400' },
      newsdata: { label: 'NewsData.io', color: 'text-purple-400' },
      rss: { label: 'Google News RSS', color: 'text-gray-400' },
      google: { label: 'Google CSE', color: 'text-gray-500' },
      duckduckgo: { label: 'DuckDuckGo', color: 'text-orange-400' },
    };
    return labels[key] || { label: key, color: 'text-gray-500' };
  };

  return (
    <div className="glass-card p-5 space-y-4 animate-fade-in">
      <div className="flex items-center gap-2 text-brand-400">
        <Shield className="w-4 h-4" />
        <h4 className="text-sm font-bold uppercase tracking-wider">Transparency Log</h4>
      </div>
      
      {factCheck && factCheck.total > 0 && (
        <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <p className="text-xs text-yellow-500 font-medium">Fact-Check Hit: {factCheck.total} records found</p>
        </div>
      )}

      {tierStats && (
        <div className="space-y-2">
          <p className="text-[10px] text-gray-500 uppercase font-bold">Data Retrieval Layers</p>
          <div className="grid grid-cols-1 gap-2">
            {Object.entries(tierStats).map(([key, value]) => {
              const tier = getTierLabel(key);
              return (
                <div key={key} className="flex items-center justify-between text-xs p-2 bg-white/5 rounded border border-white/5">
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${tier.color.replace('text-', 'bg-')}`} />
                    <span className="text-gray-400">{tier.label}</span>
                  </div>
                  <span className="text-gray-300">{value}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}