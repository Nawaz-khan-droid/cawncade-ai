import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

export default function FAQSection() {
  const [openIndex, setOpenIndex] = useState(0);

  const faqs = [
    {
      question: "Does CAWNCADE AI determine absolute truth?",
      answer: "No. CAWNCADE retrieves live sources, cross-checks them against fact-check databases, and scores cross-source agreement. The verdict reflects what the evidence supports. You still make the final call."
    },
    {
      question: "What modules are available?",
      answer: "We offer ContextLens for text and URL analysis, VisualLens for image forensics and deepfake detection, and AgentChat for conversational deep-dives into the generated reports."
    },
    {
      question: "What inputs can I analyze?",
      answer: "You can analyze raw text claims, social media excerpts, live news URLs (HTTPS), and images (PNG/JPG). Video forensic support via YouTube URLs is also available."
    },
    {
      question: "Where do the sources come from?",
      answer: "Sources are retrieved in real-time across authoritative news outlets, academic journals, and recognized fact-checking databases using live ML inference."
    },
    {
      question: "Is my data sent anywhere?",
      answer: "Your analysis inputs are processed securely and discarded post-inference. We do not use your proprietary prompts or uploaded files to train our foundational models."
    },
    {
      question: "Can I use this on mobile?",
      answer: "Yes, the CAWNCADE AI dashboard is fully responsive and optimized for mobile devices, allowing you to run fact-verification pipelines on the go."
    }
  ];

  return (
    <section id="faq" className="py-24 px-6 bg-slate-50 dark:bg-slate-950 transition-colors duration-300">
      <div className="max-w-3xl mx-auto flex flex-col items-center">
        
        <span className="inline-block px-3 py-1 mb-6 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono text-xs font-bold tracking-widest uppercase border border-slate-200 dark:border-slate-700">
          FAQ
        </span>
        <h2 className="font-display text-3xl md:text-5xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight text-center mb-12">
          Questions, <span className="text-blue-500">answered</span>
        </h2>

        <div className="w-full flex flex-col gap-3">
          {faqs.map((faq, idx) => {
            const isOpen = openIndex === idx;
            return (
              <div 
                key={idx} 
                className={`w-full overflow-hidden rounded-2xl border transition-all duration-200 ${
                  isOpen 
                    ? 'bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 shadow-sm' 
                    : 'bg-white/50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? -1 : idx)}
                  className="w-full px-6 py-5 flex items-center justify-between text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded-xl"
                >
                  <span className="font-display font-semibold text-slate-900 dark:text-slate-50 text-lg">
                    {faq.question}
                  </span>
                  <ChevronDown 
                    size={20} 
                    className={`text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180 text-blue-500' : ''}`} 
                  />
                </button>
                
                <div 
                  className={`px-6 overflow-hidden transition-all duration-300 ease-in-out ${
                    isOpen ? 'max-h-40 pb-5 opacity-100' : 'max-h-0 opacity-0'
                  }`}
                >
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                    {faq.answer}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
