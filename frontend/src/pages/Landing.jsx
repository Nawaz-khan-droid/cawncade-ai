import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Search, Eye, Zap, Globe, Brain, ArrowRight } from 'lucide-react';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-surface-950">
      {/* Hero */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-brand-500/10 to-transparent" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 relative">
          <div className="text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-sm">
              <Zap className="w-4 h-4" />
              v3.0 — Powered by Llama 3.1 ReAct Agent
            </div>
            <h1 className="text-4xl sm:text-6xl font-bold text-white tracking-tight">
              CAWNCADE <span className="text-brand-400">AI</span>
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Context Aware Watch News Confirmation Authenticity Detection Engine.
              Verify news, fact-check claims, detect deepfakes — all in one platform.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="btn-primary inline-flex items-center gap-2 px-8 py-4 text-lg"
            >
              Start Verifying <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid md:grid-cols-3 gap-6">
          <div className="glass-card p-6 space-y-3">
            <Search className="w-8 h-8 text-brand-400" />
            <h3 className="text-lg font-semibold text-white">ContextLens</h3>
            <p className="text-gray-400 text-sm">
              Analyze text claims, news URLs, and YouTube videos against 50 trusted sources
              using a 5-tier search engine with circuit breaker resilience.
            </p>
          </div>
          <div className="glass-card p-6 space-y-3">
            <Eye className="w-8 h-8 text-purple-400" />
            <h3 className="text-lg font-semibold text-white">Visual Lens</h3>
            <p className="text-gray-400 text-sm">
              Upload images to detect AI-generated content, deepfakes, or manipulated media
              using ViT/Siglip2 vision models via HuggingFace Inference API.
            </p>
          </div>
          <div className="glass-card p-6 space-y-3">
            <Brain className="w-8 h-8 text-green-400" />
            <h3 className="text-lg font-semibold text-white">AI Reasoning</h3>
            <p className="text-gray-400 text-sm">
              Llama 3.1 8B ReAct agent performs autonomous multi-step investigation,
              searching DuckDuckGo, analyzing evidence, and producing detailed verification reports.
            </p>
          </div>
        </div>
      </div>

      {/* Tech Stack */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="glass-card p-8">
          <h3 className="text-center text-sm font-medium text-gray-500 uppercase tracking-wider mb-6">Verification Pipeline</h3>
          <div className="flex flex-wrap justify-center gap-3">
            {['Google Fact Check', 'Google CSE', 'Tavily', 'NewsData.io', 'DuckDuckGo', 'Google News RSS', 'GDELT', 'YouTube Transcript', 'Safe Browsing', 'ChromaDB', 'Circuit Breaker', 'Webshare Proxy'].map((tech) => (
              <span key={tech} className="px-3 py-1.5 text-xs bg-white/5 border border-white/10 rounded-full text-gray-400">
                {tech}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center text-xs text-gray-600">
        CAWNCADE AI v3.0 | Deployed on Hugging Face Spaces
      </div>
    </div>
  );
}
