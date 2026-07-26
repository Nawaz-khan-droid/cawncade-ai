import React from 'react';
import { FileText, ExternalLink, CheckCircle2, XCircle, AlertTriangle, Info } from 'lucide-react';

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

  // DOMParser-based HTML sanitization: extracts text nodes cleanly and eliminates broken tags
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

  // Extract explicit VERDICT if present at the top
  let verdictType = null;
  let verdictText = null;
  const verdictMatch = cleanText.match(/^VERDICT:\s*([^\n]+)/i);

  if (verdictMatch) {
    verdictText = verdictMatch[1].trim();
    cleanText = cleanText.replace(/^VERDICT:\s*[^\n]+\n*/i, '');

    const upper = verdictText.toUpperCase();
    if (upper.includes('TRUE') || upper.includes('VERIFIED') || upper.includes('CORROBORATED')) {
      verdictType = 'true';
    } else if (upper.includes('FALSE') || upper.includes('DEBUNKED') || upper.includes('FAKE')) {
      verdictType = 'false';
    } else if (upper.includes('PRELIMINARY')) {
      verdictType = 'preliminary';
    } else {
      verdictType = 'unverified';
    }
  }

  // Render Verdict Badge
  const renderVerdictBadge = () => {
    if (!verdictText) return null;

    const styles = {
      true: {
        bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
        icon: CheckCircle2,
        label: 'VERIFIED TRUE',
      },
      false: {
        bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
        icon: XCircle,
        label: 'VERIFIED FALSE / DEBUNKED',
      },
      preliminary: {
        bg: 'bg-sky-500/10 border-sky-500/30 text-sky-400',
        icon: Info,
        label: 'PRELIMINARY ASSESSMENT',
      },
      unverified: {
        bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
        icon: AlertTriangle,
        label: 'UNVERIFIED / UNCONFIRMED',
      },
    };

    const current = styles[verdictType] || styles.unverified;
    const Icon = current.icon;

    return (
      <div className={`flex items-center gap-3 p-4 rounded-xl border ${current.bg} mb-6 transition-all shadow-sm`}>
        <Icon className="w-6 h-6 shrink-0" />
        <div className="flex flex-col">
          <span className="text-xs font-bold tracking-wider uppercase opacity-80">{current.label}</span>
          <span className="text-sm font-semibold">{verdictText}</span>
        </div>
      </div>
    );
  };

  // Convert URLs or Markdown links into clean UI badges
  const renderFormattedText = (text) => {
    if (!text) return null;

    const urlRegex = /(https?:\/\/[^\s<]+)/g;
    const paragraphs = text.split('\n\n').filter(Boolean);

    return paragraphs.map((para, pIdx) => {
      const parts = para.split(urlRegex);

      return (
        <p key={pIdx} className="mb-4 leading-relaxed whitespace-pre-wrap break-words">
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
                  <span>🔗 {domain}</span>
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
    <div className="glass-card p-6 md:p-8 h-full flex flex-col">
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/5">
        <FileText className="w-5 h-5 text-primary" />
        <h2 className="text-xl font-semibold text-white">Context Synthesis</h2>
      </div>

      {renderVerdictBadge()}

      <div className="prose prose-invert max-w-none text-text leading-relaxed text-sm md:text-base w-full overflow-hidden">
        {renderFormattedText(cleanText)}
      </div>
    </div>
  );
}
