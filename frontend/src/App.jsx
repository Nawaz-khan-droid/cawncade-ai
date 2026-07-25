import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { PipelineProvider } from './context/PipelineContext';
import Layout from './layout/Layout';

// Placeholder Pages
import Home from './pages/Home';
import ContextLens from './pages/ContextLens';
import VisualLens from './pages/VisualLens';
import AgentChat from './pages/AgentChat';

function App() {
  return (
    <ThemeProvider>
      <PipelineProvider>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            <Route path="/" element={<Home />} />
            
            <Route element={<Layout />}>
              <Route path="context-lens" element={<ContextLens />} />
              <Route path="visual-lens" element={<VisualLens />} />
              <Route path="agent-chat" element={<AgentChat />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </PipelineProvider>
    </ThemeProvider>
  );
}

export default App;
