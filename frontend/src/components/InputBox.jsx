import React, { useState } from 'react';
import { Search, Link, FileText, ArrowRight, Loader2 } from 'lucide-react';

export default function InputBox({ onSubmit, isLoading }) {
  const [input, setInput] = useState('');
  const [inputType, setInputType] = useState('text');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSubmit({ input_text: input.trim(), input_type: inputType, max_sources: 8 });
    }
  };

  const detectType = (value) => {
    if (value.match(/^https?:\/\//i)) {
      setInputType('url');
    } else {
      setInputType('text');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div className="glass-card p-2 flex items-center gap-2">
        {/* Type Selector */}
        <div className="flex items-center gap-1 pl-2">
          <button
            type="button"
            onClick={() => setInputType('text')}
            className={`p-2 rounded-lg transition-all ${
              inputType === 'text' ? 'bg-brand-500/20 text-brand-400' : 'text-gray-500 hover:text-gray-300'
            }`}
            title="Text/Claim"
          >
            <FileText className="w-5 h-5" />
          </button>
          <button
            type="button"
            onClick={() => setInputType('url')}
            className={`p-2 rounded-lg transition-all ${
              inputType === 'url' ? 'bg-brand-500/20 text-brand-400' : 'text-gray-500 hover:text-gray-300'
            }`}
            title="URL Analysis"
          >
            <Link className="w-5 h-5" />
          </button>
        </div>

        {/* Input */}
        <input
          type="text"
          value={input}
          onChange={(e) => { setInput(e.target.value); detectType(e.target.value); }}
          placeholder={
            inputType === 'url'
              ? "Paste a news URL to verify..."
              : "Enter a claim, headline, or topic to verify..."
          }
          className="flex-1 bg-transparent px-3 py-3 text-gray-100 placeholder-gray-500 focus:outline-none text-base"
          disabled={isLoading}
        />

        {/* Submit */}
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="btn-primary flex items-center gap-2 px-5 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <Search className="w-5 h-5" />
              <span className="hidden sm:inline">Analyze</span>
            </>
          )}
        </button>
      </div>

      {/* Quick examples */}
      <div className="flex flex-wrap gap-2 mt-3 justify-center">
        {[
          "Did India win the 2024 T20 World Cup?",
          "Is WHO recommending ban on artificial sweeteners?",
          "https://www.bbc.com/news",
        ].map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => { setInput(example); detectType(example); }}
            className="px-3 py-1.5 text-xs bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/15 rounded-full text-gray-400 hover:text-gray-200 transition-all"
          >
            {example.length > 40 ? example.substring(0, 40) + '...' : example}
          </button>
        ))}
      </div>
    </form>
  );
}
