import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Search, BarChart3, Globe, Cpu, Eye, ArrowRight, Sparkles } from 'lucide-react';
import InputBox from '../components/InputBox';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function Landing() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const features = [
    {
      icon: Search,
      title: 'Multi-Source Retrieval',
      desc: 'Searches Google News RSS, GDELT, and 30+ trusted sources simultaneously for comprehensive coverage.',
    },
    {
      icon: Shield,
      title: 'Context-Aware Scoring',
      desc: 'Multi-factor confidence scoring: credibility, agreement, diversity, recency, and grounding — not just true/false.',
    },
    {
      icon: BarChart3,
      title: 'Explainable Output',
      desc: 'Every claim is backed by citations, source comparisons, and conflict detection. Full transparency.',
    },
    {
      icon: Globe,
      title: 'Trusted Source Network',
      desc: 'Administered allowlist of credible outlets: Reuters, BBC, AP, The Hindu, Alt News, Snopes, and more.',
    },
    {
      icon: Cpu,
      title: 'Modular Agent Pipeline',
      desc: 'Researcher → Verifier → Synthesizer agents work independently, each testable and improvable.',
    },
    {
      icon: Eye,
      title: 'Bias & Conflict Detection',
      desc: 'Identifies conflicting narratives, low diversity, and potential bias across sources with dynamic disclaimers.',
    },
  ];

  const handleAnalyze = async (data) => {
    setIsLoading(true);
    try {
      const result = await api.analyze(data);
      // Store result and navigate to dashboard
      sessionStorage.setItem('cawncade_last_result', JSON.stringify(result));
      navigate('/dashboard', { state: { result } });
      toast.success('Analysis complete!');
    } catch (err) {
      toast.error(err.message || 'Analysis failed. Try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero */}
      <section className="relative flex-1 flex items-center justify-center px-4 py-20 overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-4xl mx-auto text-center space-y-8">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-brand-500/10 border border-brand-500/20 rounded-full text-sm text-brand-300">
            <Sparkles className="w-4 h-4" />
            Context-Aware News Verification
          </div>

          {/* Title */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold leading-tight">
            Don't just{' '}
            <span className="gradient-text">believe</span>.<br />
            <span className="gradient-text">Verify</span>.
          </h1>

          {/* Subtitle */}
          <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
            CAWNCADE AI analyzes claims across multiple trusted sources, detects conflicts,
            and provides context-aware confidence scores — never just true or false.
          </p>

          {/* Input Box */}
          <InputBox onSubmit={handleAnalyze} isLoading={isLoading} />
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold text-white mb-3">How It Works</h2>
            <p className="text-gray-400">Three agents, one mission: grounded, transparent analysis.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div key={i} className="glass-card-hover p-6 group">
                <div className="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center mb-4 group-hover:bg-brand-500/20 transition-colors">
                  <f.icon className="w-5 h-5 text-brand-400" />
                </div>
                <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Agent Pipeline */}
      <section className="py-20 px-4 bg-white/[0.02]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-white mb-8">Agent Pipeline</h2>
          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            {[
              { name: 'Researcher', desc: 'Retrieve sources', color: 'from-blue-500 to-blue-600' },
              { name: 'Verifier', desc: 'Detect patterns', color: 'from-purple-500 to-purple-600' },
              { name: 'Synthesizer', desc: 'Generate output', color: 'from-cyan-500 to-cyan-600' },
            ].map((agent, i, arr) => (
              <React.Fragment key={agent.name}>
                <div className="glass-card p-5 w-48 group hover:scale-105 transition-transform">
                  <div className={`w-full h-1 bg-gradient-to-r ${agent.color} rounded-full mb-3`} />
                  <h4 className="font-semibold text-white">{agent.name}</h4>
                  <p className="text-xs text-gray-400 mt-1">{agent.desc}</p>
                </div>
                {i < arr.length - 1 && (
                  <ArrowRight className="w-5 h-5 text-gray-600 hidden md:block" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-white/5 text-center">
        <p className="text-sm text-gray-500">
          CAWNCADE AI — Context Aware Watch News Confirmation Authenticity Detection Engine
        </p>
        <p className="text-xs text-gray-600 mt-1">
          Built with FastAPI, React, Tailwind CSS, and Trust.
        </p>
      </footer>
    </div>
  );
}
