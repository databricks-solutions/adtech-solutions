/**
 * Hook for managing chat history with agent API integration.
 * Uses the shared SegmentContext for state management.
 */

import { useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { segmentApi } from '../api/segmentApi';
import { useSegmentContext } from '../context/SegmentContext';
import type { ChatMessage, SegmentPreview } from '../types';

export function useChatHistory() {
  const { state, actions } = useSegmentContext();
  const { chatHistory, segment } = state;
  const { addChatMessage, setSegment, setLoading, setPreview } = actions;

  const sendMutation = useMutation({
    mutationFn: async (input: string) => {
      // Convert chat history to API format (map 'agent' to 'assistant' for LLM)
      const history = chatHistory.map((m) => ({
        role: m.role === 'agent' ? 'assistant' : m.role,
        content: m.content,
      }));

      // Get current segment if it has conditions
      const currentSegment = segment.groups.some((g) =>
        g.conditions.some((c) => c.feature && c.values.length > 0)
      )
        ? segment
        : undefined;

      return segmentApi.parseAgentInput(input, history, currentSegment);
    },
    onMutate: () => {
      setLoading(true);
    },
    onSuccess: (data) => {
      // Add agent message with preview and segment
      const preview: SegmentPreview | undefined = data.preview
        ? {
            individual_count: data.preview.individual_count,
            household_count: data.preview.household_count,
            sql: data.sql,
            execution_time_ms: 0,
          }
        : undefined;

      addChatMessage({
        id: crypto.randomUUID(),
        role: 'agent',
        content: data.response_text,
        timestamp: new Date(),
        segment: data.segment || undefined,
        preview,
      });

      // Update segment state if agent returned one
      if (data.segment) {
        setSegment(data.segment);
      }

      // Update preview panel
      if (data.preview) {
        setPreview({
          individual_count: data.preview.individual_count,
          household_count: data.preview.household_count,
          sql: data.sql,
          execution_time_ms: 0,
        });
      }
    },
    onSettled: () => {
      setLoading(false);
    },
  });

  const sendMessage = useCallback(
    async (input: string) => {
      // Add user message first
      addChatMessage({
        id: crypto.randomUUID(),
        role: 'user',
        content: input,
        timestamp: new Date(),
      });

      // Send to agent API
      return sendMutation.mutateAsync(input);
    },
    [addChatMessage, sendMutation]
  );

  return {
    messages: chatHistory,
    sendMessage,
    isLoading: sendMutation.isPending,
    error: sendMutation.error,
  };
}

export default useChatHistory;
