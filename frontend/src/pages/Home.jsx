import React, { useEffect } from 'react';
import HomeHeader from '../components/home/HomeHeader';
import HeroSection from '../components/home/HeroSection';
import BentoGrid from '../components/home/BentoGrid';
import PipelineTimeline from '../components/home/PipelineTimeline';
import FAQSection from '../components/home/FAQSection';
import BottomCTA from '../components/home/BottomCTA';
import HomeFooter from '../components/home/HomeFooter';
import ScrollToTop from '../components/ui/ScrollToTop';

export default function Home() {
  // Ensure we start at the top when navigating to the page
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-50 transition-colors duration-300 selection:bg-blue-500/30">
      <HomeHeader />
      
      <main className="flex-1 flex flex-col">
        <HeroSection />
        <BentoGrid />
        <PipelineTimeline />
        <FAQSection />
        <BottomCTA />
      </main>

      <HomeFooter />
      <ScrollToTop />
    </div>
  );
}
