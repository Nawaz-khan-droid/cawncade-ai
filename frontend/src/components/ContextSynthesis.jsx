import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
    // Fix broken newline domain list items: "- \n reuters.com" -> "- https://reuters.com"
    .replace(/-\s*\n\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, '- https://$1');

  // Smart Deduplication: If the raw summary contains structured template headers,
  // strip the redundant "Final Verdict", "Confidence Score", and "Verified Sources" blocks
  // (since Verdict/Confidence are shown in the Hero Banner above, and Sources are shown in the Grid below).
  if (/###\s*(?:🏷️\s*)?Final Verdict/i.test(cleanText)) {
    cleanText = cleanText
      .replace(/###\s*(?:🏷️\s*)?Final Verdict[\s\S]*?(?=###|\Z)/gi, '')
      .replace(/###\s*(?:📊\s*)?Confidence Score[\s\S]*?(?=###|\Z)/gi, '')
      .replace(/###\s*(?:🌐\s*)?Verified Sources[\s\S]*?(?=###|\Z)/gi, '')
      .replace(/###\s*(?:🔍\s*)?Concrete Evidence & Findings/gi, '');
  }

  cleanText = cleanText.trim();

  if (!cleanText) return null;

  // Custom components for ReactMarkdown renderer to enforce high-contrast theme styling
  const markdownComponents = {
    h1: ({ children }) => (
      <h2 className="text-lg md:text-xl font-extrabold text-slate-900 dark:text-white mt-5 mb-3 flex items-center gap-2 border-b border-slate-200 dark:border-white/10 pb-2">
        {children}
      </h2>
    ),
    h2: ({ children }) => (
      <h3 className="text-base md:text-lg font-bold text-slate-900 dark:text-white mt-4 mb-2 flex items-center gap-2">
        {children}
      </h3>
    ),
    h3: ({ children }) => {
      const text = String(children);
      const isVerdict = text.includes('Verdict');
      const isConfidence = text.includes('Confidence');
      const isEvidence = text.includes('Evidence') || text.includes('Findings');
      const isSources = text.includes('Sources');

      let icon = <FileText className="w-4 h-4 text-primary" />;
      let badgeStyle = "border-l-4 border-primary bg-primary/5 dark:bg-primary/10 text-slate-900 dark:text-white";

      if (isVerdict) {
        badgeStyle = "border-l-4 border-amber-500 bg-amber-500/10 text-slate-900 dark:text-white";
        icon = <AlertTriangle className="w-4 h-4 text-amber-500" />;
      } else if (isConfidence) {
        badgeStyle = "border-l-4 border-emerald-500 bg-emerald-500/10 text-slate-900 dark:text-white";
        icon = <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      } else if (isEvidence) {
        badgeStyle = "border-l-4 border-sky-500 bg-sky-500/10 text-slate-900 dark:text-white";
        icon = <Info className="w-4 h-4 text-sky-500" />;
      }

      return (
        <h4 className={`text-sm md:text-base font-extrabold mt-5 mb-2.5 p-2.5 rounded-r-lg flex items-center gap-2.5 shadow-sm ${badgeStyle}`}>
          {icon}
          <span>{children}</span>
        </h4>
      );
    },
    h4: ({ children }) => (
      <h5 className="text-xs md:text-sm font-bold uppercase tracking-wider text-primary mt-3 mb-1">
        {children}
      </h5>
    ),
    p: ({ children }) => {
      const strContent = React.Children.toArray(children).map(c => typeof c === 'string' ? c : '').join('').trim();
      
      // Render verdict pills prominently if standalone text matches a known verdict code
      if (strContent === 'FALSE' || strContent === 'FALSE_DEBUNKED' || strContent === 'VERIFIED_FALSE') {
        return (
          <div className="my-2">
            <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-rose-500/15 text-rose-700 dark:text-rose-400 border border-rose-500/30 font-black text-sm tracking-wide shadow-sm">
              <XCircle className="w-4 h-4 text-rose-500" />
              <span>FALSE / DEBUNKED</span>
            </span>
          </div>
        );
      }
      if (strContent === 'TRUE' || strContent === 'VERIFIED_TRUE') {
        return (
          <div className="my-2">
            <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 font-black text-sm tracking-wide shadow-sm">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>VERIFIED TRUE</span>
            </span>
          </div>
        );
      }

      return (
        <p className="text-sm md:text-base text-slate-800 dark:text-slate-200 leading-relaxed mb-3 break-words">
          {children}
        </p>
      );
    },
    ul: ({ children }) => (
      <ul className="my-3 space-y-2 list-none pl-0">
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className="my-3 space-y-2 list-decimal pl-5 text-slate-800 dark:text-slate-200 text-sm">
        {children}
      </ol>
    ),
    li: ({ children }) => {
      return (
        <li className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-100/80 dark:bg-black/30 border border-slate-200 dark:border-white/5 text-xs md:text-sm text-slate-800 dark:text-slate-200 leading-relaxed shadow-xs">
          <span className="text-primary font-black mt-0.5">•</span>
          <div className="flex-1 break-words">{children}</div>
        </li>
      );
    },
    strong: ({ children }) => (
      <strong className="font-bold text-slate-900 dark:text-white">
        {children}
      </strong>
    ),
    a: ({ href, children }) => {
      let label = children;
      let displayUrl = href || '';
      try {
        if (href) {
          displayUrl = href;
          const parsed = new URL(href);
          label = parsed.hostname.replace('www.', '');
        } else if (typeof children === 'string' && children.includes('.')) {
          displayUrl = children.startsWith('http') ? children : `https://${children}`;
          label = children.replace(/^https?:\/\//, '').replace('www.', '');
        }
      } catch (e) {}

      return (
        <a
          href={displayUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 mx-1 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/25 rounded-lg text-xs font-bold transition-all no-underline align-middle shadow-xs"
        >
          <span>{label}</span>
          <ExternalLink className="w-3 h-3 opacity-70" />
        </a>
      );
    },
    code: ({ children }) => (
      <code className="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-primary font-mono text-xs font-bold">
        {children}
      </code>
    )
  };

  return (
    <div className="glass-card p-6 md:p-8 h-full flex flex-col gap-4">
      <div className="flex items-center gap-3 pb-3 border-b border-slate-200 dark:border-white/5">
        <FileText className="w-5 h-5 text-primary" />
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Analysis Summary</h2>
      </div>

      <div className="prose dark:prose-invert max-w-none text-slate-800 dark:text-slate-200 leading-relaxed w-full overflow-hidden">
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
          {cleanText}
        </ReactMarkdown>
      </div>
    </div>
  );
}
