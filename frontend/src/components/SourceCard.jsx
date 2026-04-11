import React from 'react';
import { ExternalLink } from 'lucide-react';

export default function SourceCard({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="glass-card p-5 space-y-3">
      <h4 className="text-sm font-medium text-gray-400">Sources ({sources.length})</h4>
      <div className="space-y-2 max-h-80 overflow-y-auto">
        {sources.map((source, i) => (
          <a key={i} href={source.url} target="_blank" rel="noopener noreferrer"
            className="block p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors group">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 truncate group-hover:text-brand-400 transition-colors">{source.title || 'Untitled'}</p>
                <p className="text-xs text-gray-500 mt-1 truncate">{source.source_name || source.url}</p>
              </div>
              {source.is_trusted && (
                <span className="shrink-0 px-1.5 py-0.5 text-[10px] bg-green-500/10 text-green-400 rounded font-medium">TRUSTED</span>
              )}
            </div>
            {source.snippet && <p className="text-xs text-gray-500 mt-1 line-clamp-2">{source.snippet}</p>}
            {source.retrieval_tier && (
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] text-gray-600">{source.retrieval_tier}</span>
                {source.channel && <span className="text-[10px] text-gray-600">{source.channel}</span>}
              </div>
            )}
          </a>
        ))}
      </div>
    </div>
  );
}
