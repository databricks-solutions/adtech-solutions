/**
 * Toggle between Agent and Builder modes.
 */

import React from 'react';
import { useSegmentContext } from '../context/SegmentContext';
import type { ModeType } from '../types';

export const ModeToggle: React.FC = () => {
  const { state, actions } = useSegmentContext();
  const { mode } = state;
  const { setMode } = actions;

  const handleModeChange = (newMode: ModeType) => {
    setMode(newMode);
  };

  return (
    <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
      <button
        onClick={() => handleModeChange('agent')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          mode === 'agent'
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        Agent
      </button>
      <button
        onClick={() => handleModeChange('builder')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          mode === 'builder'
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        Builder
      </button>
    </div>
  );
};

export default ModeToggle;
