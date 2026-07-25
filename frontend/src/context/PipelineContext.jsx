import React, { createContext, useContext, useState } from 'react';

const PipelineContext = createContext();

export function PipelineProvider({ children }) {
  const [pipelineState, setPipelineState] = useState({
    isLoading: false,
    result: null,
    error: null,
  });

  const startPipeline = () => {
    setPipelineState({ isLoading: true, result: null, error: null });
  };

  const finishPipeline = (result) => {
    setPipelineState({ isLoading: false, result, error: null });
  };

  const failPipeline = (error) => {
    setPipelineState({ isLoading: false, result: null, error });
  };

  const resetPipeline = () => {
    setPipelineState({ isLoading: false, result: null, error: null });
  };

  return (
    <PipelineContext.Provider 
      value={{ 
        ...pipelineState, 
        startPipeline, 
        finishPipeline, 
        failPipeline,
        resetPipeline
      }}
    >
      {children}
    </PipelineContext.Provider>
  );
}

export function usePipeline() {
  const context = useContext(PipelineContext);
  if (!context) {
    throw new Error('usePipeline must be used within a PipelineProvider');
  }
  return context;
}
