import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

export const ChatInterface: React.FC = () => {
  const { messages, addMessage, updateLastMessage, activeTopic, setActiveTopic } = useAppStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsgId = crypto.randomUUID();
    addMessage({ id: userMsgId, role: 'user', content: input, isStreaming: false });
    
    const botMsgId = crypto.randomUUID();
    addMessage({ id: botMsgId, role: 'assistant', content: '', isStreaming: true });

    setActiveTopic(input);
    const queryPayload = { question: input, target_concept: input };
    setInput('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/query/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(queryPayload),
      });

      if (!response.body) throw new Error('No response body');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          updateLastMessage('', false);
          break;
        }
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ') && line !== 'data: [DONE]') {
            updateLastMessage(line.replace('data: ', ''), true);
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      updateLastMessage('\n[Connection Error]', false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 border-r border-gray-800 w-1/3">
      <div className="p-4 border-b border-gray-800 bg-gray-900 shadow-sm flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-100 flex items-center gap-2">
          <Bot className="text-blue-500" /> Luminal AI
        </h2>
        {activeTopic && (
          <span className="text-xs px-2 py-1 rounded-full bg-blue-900/30 text-blue-400 border border-blue-800/50">
            Topic: {activeTopic.substring(0, 15)}...
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
            <Bot size={48} className="text-gray-700" />
            <p>Ready to traverse the knowledge graph.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-800'}`}>
                {msg.role === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-blue-400" />}
              </div>
              <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-200 border border-gray-700'}`}>
                <p className="whitespace-pre-wrap leading-relaxed text-sm">
                  {msg.content}
                  {msg.isStreaming && <span className="inline-block w-2 h-4 ml-1 bg-blue-500 animate-pulse" />}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-gray-900 border-t border-gray-800">
        <form onSubmit={handleSend} className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Query the conceptual graph..."
            className="w-full bg-gray-800 border border-gray-700 text-white rounded-xl pl-4 pr-12 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all shadow-inner"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="absolute right-2 p-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};
