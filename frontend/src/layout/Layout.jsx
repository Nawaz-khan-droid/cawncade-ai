import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Activity, Sun, Moon, Search, Image as ImageIcon, MessageSquare, Settings } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import Logo from '../components/ui/Logo';

export default function Layout() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen flex flex-col font-sans transition-colors duration-300 pb-16 md:pb-0 relative">
      <header className="sticky top-0 z-50 bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-md border-b border-borderBase-light dark:border-borderBase-dark w-full">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          
          <div className="flex items-center gap-8">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <Logo size={32} />
              <h1 className="text-xl font-bold tracking-tight text-textMain-light dark:text-textMain-dark font-display">
                CAWNCADE <span className="text-primary font-medium">AI</span>
              </h1>
            </div>

            {/* Main Navigation */}
            <nav className="hidden md:flex items-center gap-2">
              <NavLink to="/" className={({isActive}) => `nav-tab flex items-center gap-2 ${isActive ? 'active' : ''}`}>
                <Activity className="w-4 h-4" /> Dashboard
              </NavLink>
              <NavLink to="/context-lens" className={({isActive}) => `nav-tab flex items-center gap-2 ${isActive ? 'active' : ''}`}>
                <Search className="w-4 h-4" /> ContextLens
              </NavLink>
              <NavLink to="/visual-lens" className={({isActive}) => `nav-tab flex items-center gap-2 ${isActive ? 'active' : ''}`}>
                <ImageIcon className="w-4 h-4" /> VisualLens
              </NavLink>
              <NavLink to="/agent-chat" className={({isActive}) => `nav-tab flex items-center gap-2 ${isActive ? 'active' : ''}`}>
                <MessageSquare className="w-4 h-4" /> Agent Chat
              </NavLink>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <button 
              onClick={toggleTheme}
              className="p-2 text-textMuted-light dark:text-textMuted-dark hover:text-primary transition-colors hover:bg-cardHover-light dark:hover:bg-cardHover-dark rounded-full"
              title="Toggle Theme"
            >
              {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <button className="p-2 text-textMuted-light dark:text-textMuted-dark hover:text-primary transition-colors hover:bg-cardHover-light dark:hover:bg-cardHover-dark rounded-full">
              <Settings className="w-5 h-5" />
            </button>
          </div>

        </div>
      </header>

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 py-8 flex flex-col gap-10">
        <Outlet />
      </main>

      <footer className="mt-auto border-t border-borderBase-light dark:border-borderBase-dark bg-card-light dark:bg-card-dark py-6">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-xs text-textMuted-light dark:text-textMuted-dark flex items-center justify-center gap-2">
            <Logo size={16} className="shadow-none rounded-sm" />
            <strong>DISCLAIMER:</strong> CAWNCADE AI provides probabilistic insights based on retrieved data. It does not determine absolute truth.
          </p>
        </div>
      </footer>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-background-light/95 dark:bg-background-dark/95 backdrop-blur-lg border-t border-borderBase-light dark:border-borderBase-dark flex items-center justify-around h-16 px-2 pb-safe">
        <NavLink to="/" className={({isActive}) => `flex flex-col items-center justify-center gap-1 w-full h-full text-[10px] font-bold tracking-wider transition-colors ${isActive ? 'text-primary' : 'text-textMuted-light dark:text-textMuted-dark'}`}>
          <Activity className="w-5 h-5" />
          <span>Dash</span>
        </NavLink>
        <NavLink to="/context-lens" className={({isActive}) => `flex flex-col items-center justify-center gap-1 w-full h-full text-[10px] font-bold tracking-wider transition-colors ${isActive ? 'text-primary' : 'text-textMuted-light dark:text-textMuted-dark'}`}>
          <Search className="w-5 h-5" />
          <span>Context</span>
        </NavLink>
        <NavLink to="/visual-lens" className={({isActive}) => `flex flex-col items-center justify-center gap-1 w-full h-full text-[10px] font-bold tracking-wider transition-colors ${isActive ? 'text-primary' : 'text-textMuted-light dark:text-textMuted-dark'}`}>
          <ImageIcon className="w-5 h-5" />
          <span>Visual</span>
        </NavLink>
        <NavLink to="/agent-chat" className={({isActive}) => `flex flex-col items-center justify-center gap-1 w-full h-full text-[10px] font-bold tracking-wider transition-colors ${isActive ? 'text-primary' : 'text-textMuted-light dark:text-textMuted-dark'}`}>
          <MessageSquare className="w-5 h-5" />
          <span>Agent</span>
        </NavLink>
      </nav>
    </div>
  );
}
