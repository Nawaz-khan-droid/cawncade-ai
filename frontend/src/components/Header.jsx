import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, LayoutDashboard, LogOut } from 'lucide-react';

export default function Header() {
  const navigate = useNavigate();

  useEffect(() => {
    // Inject the Google CSE script dynamically
    const script = document.createElement('script');
    script.src = "https://cse.google.com/cse.js?cx=a5402f5fbb52144cb";
    script.async = true;
    document.head.appendChild(script);

    return () => {
      // Cleanup script if necessary when component unmounts
      document.head.removeChild(script);
    };
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-surface-950/80 backdrop-blur-xl border-b border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group shrink-0">
            <div className="w-9 h-9 bg-gradient-to-br from-brand-500 to-cyan-500 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div className="hidden sm:block">
              <span className="font-bold text-lg gradient-text">CAWNCADE AI</span>
              <span className="text-xs text-gray-500 block -mt-1">Context-Aware Verification</span>
            </div>
          </Link>

          {/* Google Search Bar - Center Integration */}
          <div className="flex-1 max-w-md hidden md:block">
            <div className="gcse-search" data-resultsUrl="/dashboard" data-newWindow="false"></div>
          </div>

          {/* Nav */}
          <nav className="flex items-center gap-4 shrink-0">
            <button
              onClick={() => navigate('/dashboard')}
              className="btn-secondary text-sm flex items-center gap-2"
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>
            <button
              onClick={() => navigate('/')}
              className="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Home
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}