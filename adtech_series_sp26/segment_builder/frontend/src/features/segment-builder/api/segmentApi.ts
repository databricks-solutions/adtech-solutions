/**
 * API client for segment builder.
 * Validates API responses with Zod at the boundary for runtime safety.
 */

import apiClient from '@/lib/apiClient';
import {
  featuresListResponseSchema,
  featureValuesResponseSchema,
  segmentPreviewResponseSchema,
  segmentBuildResponseSchema,
  listSegmentsResponseSchema,
  allSegmentsOverviewResponseSchema,
  segmentUpdateResponseSchema,
  agentParseResponseSchema,
  agentSummarizeResponseSchema,
} from './schemas';
import type {
  Feature,
  SegmentDefinition,
  SegmentPreviewResponse,
} from '../types';
import { filterIncompleteConditions } from '../utils/segmentUtils';

export const segmentApi = {
  /**
   * Get all available features.
   */
  async getFeatures(): Promise<Feature[]> {
    const response = await apiClient.get('/features');
    const parsed = featuresListResponseSchema.safeParse(response.data);
    if (!parsed.success) {
      throw new Error(`Invalid features response: ${parsed.error.message}`);
    }
    return parsed.data.features;
  },

  /**
   * Get distinct values for a feature.
   */
  async getFeatureValues(
    featureName: string,
    search?: string,
    limit: number = 100
  ): Promise<string[]> {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', limit.toString());

    const response = await apiClient.get(
      `/features/${featureName}/values?${params.toString()}`
    );
    const parsed = featureValuesResponseSchema.safeParse(response.data);
    if (!parsed.success) {
      throw new Error(`Invalid feature values response: ${parsed.error.message}`);
    }
    return parsed.data.values;
  },

  /**
   * Preview a segment - get counts and SQL.
   */
  async previewSegment(
    segment: SegmentDefinition,
    includeSql: boolean = true
  ): Promise<SegmentPreviewResponse> {
    // Filter out incomplete conditions before sending
    const cleanSegment = filterIncompleteConditions(segment);

    // If no valid conditions after filtering, return zeros
    if (cleanSegment.groups.length === 0) {
      return {
        individual_count: 0,
        household_count: 0,
        sql: null,
        execution_time_ms: 0,
      };
    }

    const response = await apiClient.post('/segment/preview', {
      segment: {
        name: cleanSegment.name,
        description: cleanSegment.description,
        groups: cleanSegment.groups,
        group_logic: cleanSegment.groupLogic,
      },
      include_sql: includeSql,
    });
    const parsed = segmentPreviewResponseSchema.safeParse(response.data);
    if (!parsed.success) {
      throw new Error(`Invalid preview response: ${parsed.error.message}`);
    }
    return parsed.data;
  },

  /**
   * Build and save a segment.
   */
  async buildSegment(
    segment: SegmentDefinition,
    name: string,
    quarter: string,
    startDate: string,
    endDate: string
  ): Promise<{ segment_id: string; rows_inserted: number; campaign_name: string }> {
    // Filter out incomplete conditions before sending
    const cleanSegment = filterIncompleteConditions(segment);

    if (cleanSegment.groups.length === 0) {
      throw new Error('Cannot build segment with no valid conditions');
    }

    const response = await apiClient.post('/segment/build', {
      segment: {
        name: cleanSegment.name,
        description: cleanSegment.description,
        groups: cleanSegment.groups,
        group_logic: cleanSegment.groupLogic,
      },
      name,
      quarter,
      start_date: startDate,
      end_date: endDate,
    });
    const parsed = segmentBuildResponseSchema.safeParse(response.data);
    if (!parsed.success) {
      throw new Error(`Invalid build response: ${parsed.error.message}`);
    }
    return parsed.data;
  },

  /**
   * List existing segments.
   */
  async listSegments(): Promise<Array<{
    segment_name: string;
    segment_definition: string;
    quarter: string;
    start_date: string;
    end_date: string;
  }>> {
    const response = await apiClient.get('/segment');
    const parsed = listSegmentsResponseSchema.safeParse(response.data);
    if (!parsed.success) {
      throw new Error(`Invalid list segments response: ${parsed.error.message}`);
    }
    return parsed.data.segments;
  },

  /**
   * All segments overview: definitions joined with campaigns, grouped by campaign with counts.
   */
  async getAllSegmentsOverview(): Promise<Array<{
    segment_name: string;
    segment_definition: string;
    quarter: string;
    start_date: string;
    end_date: string;
    individual_count: number;
    household_count: number;
  }>> {
    const response = await apiClient.get('/segment/all');
    const parsed = allSegmentsOverviewResponseSchema.safeParse(response.data);
    if (!parsed.success) {
      throw new Error(`Invalid all segments response: ${parsed.error.message}`);
    }
    return parsed.data.rows;
  },

  /**
   * Update segment metadata (definition, quarter, flight dates) in the Delta table.
   */
  async updateSegmentMetadata(
    segmentName: string,
    payload: {
      segment_definition: string;
      quarter: string;
      start_date: string;
      end_date: string;
    }
  ): Promise<{ status: string; segment_name: string }> {
    const response = await apiClient.patch(
      `/segment/${encodeURIComponent(segmentName)}`,
      payload
    );
    const parsed = segmentUpdateResponseSchema.safeParse(response.data);
    if (!parsed.success) {
      throw new Error(`Invalid update response: ${parsed.error.message}`);
    }
    return parsed.data;
  },

  /**
   * Parse natural language input using LLM agent.
   */
  async parseAgentInput(
    input: string,
    conversationHistory: Array<{ role: string; content: string }>,
    currentSegment?: SegmentDefinition
  ): Promise<{
    response_text: string;
    segment: SegmentDefinition | null;
    preview: { individual_count: number; household_count: number } | null;
    sql: string | null;
  }> {
    // Filter incomplete conditions from current segment if provided
    const cleanSegment = currentSegment
      ? filterIncompleteConditions(currentSegment)
      : null;

    const response = await apiClient.post('/agent/parse', {
      input,
      conversation_history: conversationHistory,
      current_segment: cleanSegment && cleanSegment.groups.length > 0 ? {
        name: cleanSegment.name,
        description: cleanSegment.description,
        groups: cleanSegment.groups,
        group_logic: cleanSegment.groupLogic,
      } : null,
    });

    const parsed = agentParseResponseSchema.safeParse(response.data);
    if (!parsed.success) {
      throw new Error(`Invalid agent parse response: ${parsed.error.message}`);
    }
    const data = parsed.data;

    // Convert snake_case to camelCase for segment in return value
    return {
      response_text: data.response_text,
      segment: data.segment
        ? {
            name: data.segment.name,
            description: data.segment.description,
            groups: data.segment.groups,
            groupLogic: data.segment.group_logic,
          }
        : null,
      preview: data.preview ?? null,
      sql: data.sql ?? null,
    };
  },

  /**
   * Generate a 1-2 sentence segment description and suggested name from chat context using the LLM.
   */
  async summarizeSegment(
    segment: SegmentDefinition,
    conversationHistory: Array<{ role: string; content: string }>
  ): Promise<{ summary: string; suggested_name: string }> {
    const response = await apiClient.post('/agent/summarize', {
      segment: {
        name: segment.name,
        description: segment.description,
        groups: segment.groups,
        group_logic: segment.groupLogic,
      },
      conversation_history: conversationHistory,
    });
    const parsed = agentSummarizeResponseSchema.safeParse(response.data);
    if (!parsed.success) {
      throw new Error(`Invalid agent summarize response: ${parsed.error.message}`);
    }
    return parsed.data;
  },
};

export default segmentApi;
