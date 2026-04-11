import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import InputBox from '../components/InputBox';
import OutputPanel from '../components/OutputPanel';
import MetricsPanel from '../components/MetricsPanel';
import SourceCard from '../components/SourceCard';
import VisualLens from '../components/VisualLens';
import TransparencyPanel from '../components/TransparencyPanel';
import api from '../services/api';
import toast from 'react-hot-toast';
import { ArrowLeft } from 'lucide-react';

export default function Dashboard() {
  const location = useLocation();
  const navigate = useNavigate();
  const [result, setResult] = useState(location.state?.result || null);
  const [imageResult, setImageResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('context');

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
    setImageResult(null);
    setActiveTab('context');
    try {
      if (data.input_type === 'image' || data.image_base64) {
        const res = await api.analyzeImage(data);
        setImageResult(res);
        setActiveTab('visual');
        toast.success('Image analysis complete!');
      } else {
        const res = await api.analyze(data);
        setResult(res);
        sessionStorage.setItem('cawncade_last_result', JSON.stringify(res));
        toast.success('Analysis complete!');
      }
    } catch (err) {
      toast.error(err.message || 'Analysis failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <button onClick={() => navigate('/')} className="flex items-center gap-2 text-gray-400 hover:text-gray-200 transition-colors text-sm">
        <ArrowLeft className="w-4 h-4" />
        Back to Home
      </button>
      <InputBox onSubmit={handleAnalyze} isLoading={isLoading} />
      <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl w-fit">
        <button onClick={() => setActiveTab('context')} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'context' ? 'bg-brand-500/20 text-brand-400' : 'text-gray-500 hover:text-gray-300'}`}>
          ContextLens
        </button>
        <button onClick={() => setActiveTab('visual')} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'visual' ? 'bg-brand-500/20 text-brand-400' : 'text-gray-500 hover:text-gray-300'}`}>
          Visual Lens
        </button>
      </div>

      {!result && !imageResult && !isLoading && (
        <div className="glass-card p-12 text-center">
          <p className="text-gray-500 text-lg">Enter a claim, news URL, YouTube link, or upload an image to begin verification.</p>
        </div>
      )}

      {activeTab === 'context' && result && (
        <div className="grid lg:grid-cols-3 gap-6 animate-fade-in">
          <div className="lg:col-span-2 space-y-4">
            <OutputPanel result={result} />
            {result.metadata?.tier_stats && (
              <TransparencyPanel tierStats={result.metadata.tier_stats} factCheck={result.metadata.fact_check} extraction={result.metadata.extraction} inputType={result.metadata.input_type} />
            )}
            {result.agent_deep_dive && (
              <div className="glass-card p-6 space-y-3">
                <h4 className="text-sm font-medium text-green-400 flex items-center gap-2">
                  AI Agent Deep Dive (Llama 3.1)
                </h4>
                <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">{result.agent_deep_dive}</div>
              </div>
            )}
          </div>
          <div className="space-y-4">
            <MetricsPanel scores={result.scores} />
            <SourceCard sources={result.sources_cited} />
            <div className="glass-card p-5">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Was this helpful?</h4>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button key={n} onClick={() => toast.success(`Rated ${n} stars. Thank you!`)}
                    className="w-8 h-8 rounded-lg bg-white/5 hover:bg-brand-500/20 hover:text-brand-400 text-gray-500 transition-all text-sm font-medium">
                    {n}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'visual' && <VisualLens result={imageResult} isLoading={isLoading} />}

      {isLoading && (
        <div className="glass-card p-12 text-center animate-pulse">
          <div className="flex items-center justify-center gap-3">
            <div className="w-5 h-5 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-400 text-lg">Analyzing across multiple sources...</p>
          </div>
        </div>
      )}
    </div>
  );
}
