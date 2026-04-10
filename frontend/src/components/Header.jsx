import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, LayoutDashboard, LogOut } from 'lucide-react';

export default function Header() {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-50 bg-surface-950/80 backdrop-blur-xl border-b border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 bg-gradient-to-br from-brand-500 to-cyan-500 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg gradient-text">CAWNCADE AI</span>
              <span className="text-xs text-gray-500 block -mt-1">Context-Aware Verification</span>
            </div>
          </Link>

          {/* Nav */}
          <nav className="flex items-center gap-4">
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
