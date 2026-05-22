/**
 * Chat history display for Agent mode.
 */

import React from 'react';
import { useSegmentContext } from '../context/SegmentContext';
import { useChatHistory } from '../hooks/useChatHistory';

const EXAMPLE_PROMPTS = [
  'I want to target affluent people in the NE United States who are in the market for a vehicle.',
  'M18-34 who are in the market for dog food.',
];

export const ChatHistory: React.FC = () => {
  const { state } = useSegmentContext();
  const { chatHistory } = state;
  const { sendMessage, isLoading } = useChatHistory();

  if (chatHistory.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <div className="w-16 h-16 mb-4 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
          <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-700 mb-2">
          Let's start building your segment!
        </h3>
        <p className="text-sm text-gray-500 max-w-sm">
          Describe your target audience in natural language. <br></br> For example:
        </p>
        <div className="mt-4 space-y-2">
          {EXAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={isLoading}
              onClick={() => sendMessage(prompt)}
              className="block w-full text-left text-sm text-blue-600 italic hover:text-blue-700 hover:bg-blue-50 rounded-lg px-3 py-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              &ldquo;{prompt}&rdquo;
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 space-y-4">
      {chatHistory.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[80%] rounded-2xl px-4 py-3 ${
              message.role === 'user'
                ? 'bg-blue-500 text-white'
                : 'bg-white border border-gray-200 text-gray-800'
            }`}
          >
            <p className="text-sm">{message.content}</p>
            {message.preview && (
              <div className="mt-2 pt-2 border-t border-gray-200/50">
                <div className="flex gap-4 text-xs mb-2">
                  <span>
                    <strong>{message.preview.individual_count.toLocaleString()}</strong> individuals
                  </span>
                  <span>
                    <strong>{message.preview.household_count.toLocaleString()}</strong> households
                  </span>
                </div>
                {message.preview.sql && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-blue-600 hover:text-blue-700">
                      View SQL
                    </summary>
                    <pre className="mt-2 p-2 bg-gray-100 rounded text-gray-700 overflow-x-auto text-[11px] leading-relaxed">
                      {message.preview.sql}
                    </pre>
                  </details>
                )}
              </div>
            )}
            <p className="text-xs opacity-60 mt-1">
              {message.timestamp.toLocaleTimeString()}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ChatHistory;
