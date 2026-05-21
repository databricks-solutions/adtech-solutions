/**
 * Hook for fetching and caching feature metadata.
 */

import { useQuery } from '@tanstack/react-query';
import { segmentApi } from '../api/segmentApi';
import type { Feature } from '../types';

export function useFeatures() {
  return useQuery<Feature[]>({
    queryKey: ['features'],
    queryFn: () => segmentApi.getFeatures(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

export function useFeatureValues(featureName: string, search?: string, enabled: boolean = true) {
  return useQuery<string[]>({
    queryKey: ['featureValues', featureName, search],
    queryFn: () => segmentApi.getFeatureValues(featureName, search),
    enabled: enabled && !!featureName,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}
