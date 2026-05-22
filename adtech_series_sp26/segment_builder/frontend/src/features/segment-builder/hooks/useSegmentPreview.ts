/**
 * Hook for auto-previewing segments with debounce.
 */

import { useEffect, useRef, useCallback } from 'react';
import { segmentApi } from '../api/segmentApi';
import { useSegmentContext } from '../context/SegmentContext';
import type { SegmentDefinition } from '../types';

const DEBOUNCE_MS = 500;

/**
 * Check if a segment has valid conditions to preview.
 */
function hasValidConditions(segment: SegmentDefinition): boolean {
  return segment.groups.some((group) =>
    group.conditions.some(
      (condition) =>
        condition.feature !== '' &&
        condition.values.length > 0
    )
  );
}

export function useSegmentPreview() {
  const { state, actions } = useSegmentContext();
  const { segment, isLoading } = state;
  const { setPreview, setLoading, setError } = actions;

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const runPreview = useCallback(async () => {
    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Check if segment has valid conditions
    if (!hasValidConditions(segment)) {
      setPreview(null);
      return;
    }

    abortControllerRef.current = new AbortController();
    setLoading(true);
    setError(null);

    try {
      const preview = await segmentApi.previewSegment(segment, true);
      setPreview(preview);
    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        return; // Ignore aborted requests
      }
      const message = error instanceof Error ? error.message : 'Preview failed';
      setError(message);
      setPreview(null);
    } finally {
      setLoading(false);
    }
  }, [segment, setPreview, setLoading, setError]);

  // Debounced preview on segment change
  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      runPreview();
    }, DEBOUNCE_MS);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [segment, runPreview]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    preview: state.preview,
    isLoading,
    error: state.error,
    refresh: runPreview,
  };
}
