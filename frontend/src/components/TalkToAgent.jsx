import React, { useState } from 'react';
import { Send, Bot, User } from 'lucide-react';

const TalkToAgent = () => {
  const [messages, setMessages] = useState([
    { role: 'bot', content: "I'm CAWNCADE's internal agent. I have access to Serper and Tavily. How can I help you research today?" }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const newMsg = { role: 'user', content: input };
    setMessages([...messages, newMsg]);
    setInput("");
    setIsTyping(true);

    try {
      // Call your new /api/v1/chat endpoint
      const response = await fetch('/api/v1/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: input, session_id: 'default' })
      });
      const data = await response.json();

      setMessages(prev => [...prev, { role: 'bot', content: data.output }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'bot', content: "Chat service unavailable." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[500px] bg-slate-900 rounded-xl border border-slate-700">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-lg ${m.role === 'user' ? 'bg-blue-600' : 'bg-slate-800 border border-slate-700'}`}>
              <p className="text-sm text-white">{m.content}</p>
            </div>
          </div>
        ))}
        {isTyping && <div className="text-slate-500 text-xs animate-pulse">Agent is thinking and researching...</div>}
      </div>
      <div className="p-4 border-t border-slate-700 flex gap-2">
        <input 
          value={input} 
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          className="flex-1 bg-slate-800 text-white p-2 rounded-md outline-none"
          placeholder="Ask a follow-up question..."
        />
        <button onClick={handleSend} className="bg-blue-600 p-2 rounded-md hover:bg-blue-500">
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

export default TalkToAgent;
