import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import InputBox from '../components/InputBox';
import OutputPanel from '../components/OutputPanel';
import MetricsPanel from '../components/MetricsPanel';
import SourceCard from '../components/SourceCard';
import api from '../services/api';
import toast from 'react-hot-toast';
import { ArrowLeft } from 'lucide-react';

export default function Dashboard() {
  const location = useLocation();
  const navigate = useNavigate();
  const [result, setResult] = useState(location.state?.result || null);
  const [isLoading, setIsLoading] = useState(false);

  // Restore from sessionStorage if page refreshed
  useEffect(() => {
    if (!result) {
      const saved = sessionStorage.getItem('cawncade_last_result');
      if (saved) {
        try { setResult(JSON.parse(saved)); } catch {}
      }
    }
  }, []);

  const handleAnalyze = async (data) => {
    setIsLoading(true);
    setResult(null);
    try {
      const res = await api.analyze(data);
      setResult(res);
      sessionStorage.setItem('cawncade_last_result', JSON.stringify(res));
      toast.success('Analysis complete!');
    } catch (err) {
      toast.error(err.message || 'Analysis failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Input */}
      <InputBox onSubmit={handleAnalyze} isLoading={isLoading} />

      {/* Results */}
      {!result && !isLoading && (
        <div className="glass-card p-12 text-center">
          <p className="text-gray-500 text-lg">
            Enter a claim, news headline, or URL above to begin verification.
          </p>
        </div>
      )}

      {result && (
        <div className="grid lg:grid-cols-3 gap-6 animate-fade-in">
          {/* Main Output */}
          <div className="lg:col-span-2 space-y-4">
            <OutputPanel result={result} />
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            <MetricsPanel scores={result.scores} />
            <SourceCard sources={result.sources_cited} />

            {/* Feedback */}
            <div className="glass-card p-5">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Was this helpful?</h4>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    onClick={() => toast.success(`Rated ${n} stars. Thank you!`)}
                    className="w-8 h-8 rounded-lg bg-white/5 hover:bg-brand-500/20 hover:text-brand-400 text-gray-500 transition-all text-sm font-medium"
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
