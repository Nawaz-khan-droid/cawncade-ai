import React from 'react';
import { FileText } from 'lucide-react';

export default function ContextSynthesis({ summary, isLoading }) {
  if (isLoading) {
    return (
      <div className="glass-card p-6 md:p-8 h-full">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-5 h-5 bg-surface-700 rounded animate-pulse"></div>
          <div className="h-6 w-48 bg-surface-700 rounded animate-pulse"></div>
        </div>
        <div className="space-y-4">
          <div className="h-4 bg-surface-700 rounded w-full animate-pulse"></div>
          <div className="h-4 bg-surface-700 rounded w-5/6 animate-pulse"></div>
          <div className="h-4 bg-surface-700 rounded w-4/6 animate-pulse"></div>
          <div className="h-4 bg-surface-700 rounded w-full animate-pulse"></div>
        </div>
      </div>
    );
  }

  if (!summary) return null;

  // Simple Markdown parser for bold and citations
  // Example citation: [1] Reuters -> UI Badge
  const parseMarkdown = (text) => {
    if (!text) return null;
    
    // First, split by bold text
    const parts = text.split(/(\*\*.*?\*\*)/g);
    
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
      }
      
      // Then replace citations [X] Name
      const citationRegex = /(\[\d+\][^\.,\s]*\s[\w\s]+?(?=[,\.]|\s|$))/g;
      const subParts = part.split(citationRegex);
      
      return subParts.map((sub, idx) => {
        const match = sub.match(/^\[(\d+)\]\s*(.*)$/);
        if (match) {
          return (
            <a 
              key={`${index}-${idx}`} 
              href={`#source-${match[1]}`}
              className="inline-flex items-center gap-1 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 px-2 py-0.5 rounded-md text-xs font-medium transition-colors cursor-pointer mx-1 no-underline"
            >
              <span className="opacity-70">[{match[1]}]</span>
              {match[2]}
            </a>
          );
        }
        return <span key={`${index}-${idx}`}>{sub}</span>;
      });
    });
  };

  return (
    <div className="glass-card p-6 md:p-8 h-full flex flex-col">
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/5">
        <FileText className="w-5 h-5 text-primary" />
        <h2 className="text-xl font-semibold text-white">Context Synthesis</h2>
      </div>
      
      <div className="prose prose-invert max-w-none text-text leading-relaxed text-sm md:text-base w-full overflow-hidden">
        <p className="whitespace-pre-wrap break-words">{parseMarkdown(summary)}</p>
      </div>
    </div>
  );
}
