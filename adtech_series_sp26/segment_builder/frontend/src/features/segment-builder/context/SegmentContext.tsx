/**
 * Segment context provider for shared state.
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { useSegmentState, type SegmentActions } from '../hooks/useSegmentState';
import type { SegmentState } from '../types';

interface SegmentContextValue {
  state: SegmentState;
  actions: SegmentActions;
}

const SegmentContext = createContext<SegmentContextValue | null>(null);

interface SegmentProviderProps {
  children: ReactNode;
}

export const SegmentProvider: React.FC<SegmentProviderProps> = ({ children }) => {
  const { state, actions } = useSegmentState();

  return (
    <SegmentContext.Provider value={{ state, actions }}>
      {children}
    </SegmentContext.Provider>
  );
};

export function useSegmentContext(): SegmentContextValue {
  const context = useContext(SegmentContext);
  if (!context) {
    throw new Error('useSegmentContext must be used within a SegmentProvider');
  }
  return context;
}

export default SegmentContext;
