import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Send, Bot, User, Activity, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function AgentChat() {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'agent', text: 'Hello. I am the CAWNCADE Agent. I have analyzed the context provided in your previous sessions. What specific assertions or sources would you like me to clarify?' }
  ]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const userText = input;
    setMessages(prev => [...prev, { role: 'user', text: userText }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText, session_id: 'default' })
      });
      
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'agent', text: data.output || "No response received." }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'agent', text: `Error: Could not connect to the agent backend. (${error.message})` }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-5 w-full max-w-5xl mx-auto h-[75vh] px-2 md:px-0"
    >
      <div className="flex flex-col gap-1">
        <h2 className="text-2xl md:text-3xl font-display font-bold text-slate-900 dark:text-slate-50">Agent Chat</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">Conversational deep-dive into multi-vector analysis results.</p>
      </div>

      <div className="glass-card flex-1 flex flex-col overflow-hidden rounded-2xl">
        
        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 flex flex-col gap-5 custom-scrollbar">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 max-w-[90%] md:max-w-[85%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
              <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'agent' ? 'bg-gradient-to-tr from-primary to-accent shadow-md' : 'bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark'}`}>
                {msg.role === 'agent' ? <Bot className="w-4 h-4 text-white" /> : <User className="w-4 h-4 text-textMuted-light dark:text-textMuted-dark" />}
              </div>
              <div className={`p-3.5 md:p-4 rounded-2xl ${msg.role === 'user' ? 'bg-primary text-white rounded-tr-sm' : 'bg-surface-light dark:bg-surface-dark border border-borderBase-light dark:border-borderBase-dark text-textMain-light dark:text-textMain-dark rounded-tl-sm w-full overflow-hidden'}`}>
                {msg.role === 'agent' ? (
                  <div className="prose prose-sm prose-slate dark:prose-invert max-w-none prose-p:leading-relaxed text-xs md:text-sm">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.text}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="leading-relaxed text-xs md:text-sm">{msg.text}</p>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Input Area */}
        <div className="p-3 md:p-4 border-t border-borderBase-light dark:border-borderBase-dark bg-surface-light/50 dark:bg-surface-dark/50 backdrop-blur-md">
          <div className="flex items-center gap-3 relative">
            <textarea 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder="Ask the agent about source credibility or specific claims..." 
              className="w-full bg-background-light dark:bg-background-dark border border-borderBase-light dark:border-borderBase-dark rounded-xl pl-3.5 pr-12 py-2.5 text-xs md:text-sm text-textMain-light dark:text-textMain-dark placeholder-textMuted-light/50 dark:placeholder-textMuted-dark/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all resize-none min-h-[45px] max-h-[120px]"
            />
            <button 
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="absolute right-2.5 bottom-2 p-2 bg-primary hover:bg-primary-hover disabled:opacity-50 text-white rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
          <div className="flex items-center gap-2 mt-2 pl-1">
            <Activity className="w-3 h-3 text-primary animate-pulse" />
            <span className="text-[10px] text-textMuted-light dark:text-textMuted-dark uppercase tracking-widest font-bold">Context Model: CAWNCADE-Pro</span>
          </div>
        </div>

      </div>
    </motion.div>
  );
}
