import React from 'react';
import { FileText, ExternalLink } from 'lucide-react';

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

  // DOMParser-based HTML sanitization: extracts text nodes cleanly and eliminates broken HTML tags
  const sanitizeHtmlText = (raw) => {
    if (!raw) return '';
    try {
      const doc = new DOMParser().parseFromString(raw, 'text/html');
      return doc.body.textContent || doc.body.innerText || raw.replace(/<[^>]*>?/gm, '');
    } catch (e) {
      return raw.replace(/<[^>]*>?/gm, '');
    }
  };

  let cleanText = sanitizeHtmlText(summary);

  // Clean internal developer jargon & repetitive system prefixes
  cleanText = cleanText
    .replace(/^VERDICT:\s*[^\n]+\n*/gi, '')
    .replace(/PRELIMINARY ASSESSMENT\s*/gi, '')
    .replace(/Reasoning:\s*The deep-check engine is currently unavailable\.?\s*/gi, '')
    .replace(/Initial data snippet:\s*/gi, '')
    .trim();

  if (!cleanText) return null;

  // Convert URLs or Markdown links into clean UI badges
  const renderFormattedText = (text) => {
    if (!text) return null;

    const urlRegex = /(https?:\/\/[^\s<]+)/g;
    const paragraphs = text.split('\n\n').filter(Boolean);

    return paragraphs.map((para, pIdx) => {
      const parts = para.split(urlRegex);

      return (
        <p key={pIdx} className="mb-3 leading-relaxed whitespace-pre-wrap break-words text-slate-200 text-sm md:text-base">
          {parts.map((part, idx) => {
            if (part.match(/^https?:\/\//)) {
              let domain = part;
              try {
                domain = new URL(part).hostname.replace('www.', '');
              } catch (e) {
                domain = 'Source Link';
              }

              return (
                <a
                  key={idx}
                  href={part}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-2.5 py-0.5 mx-1 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/25 rounded-md text-xs font-medium transition-colors no-underline align-middle"
                >
                  <span>{domain}</span>
                  <ExternalLink className="w-3 h-3 opacity-70" />
                </a>
              );
            }

            // Bold formatting **text**
            const boldParts = part.split(/(\*\*.*?\*\*)/g);
            return boldParts.map((bPart, bIdx) => {
              if (bPart.startsWith('**') && bPart.endsWith('**')) {
                return <strong key={bIdx} className="text-white font-semibold">{bPart.slice(2, -2)}</strong>;
              }
              return <span key={bIdx}>{bPart}</span>;
            });
          })}
        </p>
      );
    });
  };

  return (
    <div className="glass-card p-6 md:p-8 h-full flex flex-col gap-4">
      <div className="flex items-center gap-3 pb-3 border-b border-white/5">
        <FileText className="w-5 h-5 text-primary" />
        <h2 className="text-lg font-bold text-white">Analysis Summary</h2>
      </div>

      <div className="prose prose-invert max-w-none text-text leading-relaxed w-full overflow-hidden">
        {renderFormattedText(cleanText)}
      </div>
    </div>
  );
}
