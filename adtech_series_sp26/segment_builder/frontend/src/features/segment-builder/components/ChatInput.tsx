/**
 * Chat input for Agent mode.
 */

import React, { useState, useCallback } from 'react';
import { useChatHistory } from '../hooks/useChatHistory';

export const ChatInput: React.FC = () => {
  const [input, setInput] = useState('');
  const { sendMessage, isLoading, error } = useChatHistory();

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!input.trim() || isLoading) return;

      const message = input.trim();
      setInput('');

      try {
        await sendMessage(message);
      } catch (err) {
        console.error('Failed to send message:', err);
      }
    },
    [input, isLoading, sendMessage]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 bg-white">
      <div className="flex items-center gap-2">
        <div className="flex-1 min-w-0">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your target audience..."
            rows={1}
            className="w-full h-12 min-h-12 max-h-12 px-4 py-3 rounded-xl border border-gray-300 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm leading-[1.25rem] box-border"
            disabled={isLoading}
          />
        </div>
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="shrink-0 flex items-center justify-center size-12 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Send"
        >
          {isLoading ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden>
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 12L3 21l18-9L3 2l3 9" />
            </svg>
          )}
        </button>
      </div>
    </form>
  );
};

export default ChatInput;
