/**
 * Main container for the segment builder (chatbot layout).
 */

import React from 'react';
import { PageHeader } from '../../../components/PageHeader';
import { SegmentProvider, useSegmentContext } from '../context/SegmentContext';
import { ModeToggle } from './ModeToggle';
import { BuilderMode } from './BuilderMode';
import { ChatHistory } from './ChatHistory';
import { ChatInput } from './ChatInput';
import { PreviewPanel } from './PreviewPanel';

const SegmentBuilderContent: React.FC = () => {
  const { state } = useSegmentContext();
  const { mode } = state;

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <PageHeader title="Audience Segmentation">
        <ModeToggle />
      </PageHeader>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {mode === 'agent' ? (
            <div className="flex flex-col h-full">
              <ChatHistory />
              <ChatInput />
            </div>
          ) : (
            <BuilderMode />
          )}
        </div>

        {/* Preview Panel (always visible) */}
        <PreviewPanel />
      </div>
    </div>
  );
};

export const SegmentBuilder: React.FC = () => {
  return (
    <SegmentProvider>
      <SegmentBuilderContent />
    </SegmentProvider>
  );
};

export default SegmentBuilder;
