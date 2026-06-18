import React from 'react';
import { createRoot } from 'react-dom/client';
import { ChatInterface } from './components/ChatInterface';
import { KnowledgeGraphViewer } from './components/KnowledgeGraphViewer';
import './index.css';

const App = () => {
  return (
    <div className="flex w-screen h-screen overflow-hidden bg-gray-950 font-sans">
      <ChatInterface />
      <KnowledgeGraphViewer />
    </div>
  );
};

const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(<App />);
}
