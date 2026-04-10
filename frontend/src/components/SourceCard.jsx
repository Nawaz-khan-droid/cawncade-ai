import React from 'react';
import { ExternalLink, Globe, Newspaper, Shield } from 'lucide-react';

export default function SourceCard({ sources }) {
  if (!sources?.length) return null;

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">
        Sources ({sources.length})
      </h3>
      <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
        {sources.map((source, i) => (
          <a
            key={i}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-3 bg-white/5 hover:bg-white/8 rounded-xl border border-white/5 hover:border-white/10 transition-all group"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Newspaper className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
                  <span className="text-sm font-medium text-white truncate">
                    {source.name || 'Unknown Source'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 truncate">{source.url}</p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {/* Credibility Badge */}
                <div
                  className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                    source.credibility >= 0.8
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : source.credibility >= 0.6
                      ? 'bg-amber-500/20 text-amber-400'
                      : 'bg-red-500/20 text-red-400'
                  }`}
                >
                  <Shield className="w-3 h-3" />
                  {(source.credibility * 100).toFixed(0)}
                </div>
                <ExternalLink className="w-4 h-4 text-gray-600 group-hover:text-gray-400 transition-colors" />
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
