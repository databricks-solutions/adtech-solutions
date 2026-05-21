/**
 * Zod schemas for validating API responses at the boundary.
 * Provides runtime safety when the backend contract changes or returns unexpected data.
 */

import { z } from 'zod';

const operatorType = z.enum(['IS', 'IN', 'NOT', 'BETWEEN', 'GT', 'LT', 'GTE', 'LTE']);
const logicType = z.enum(['AND', 'OR']);
const featureType = z.enum(['categorical', 'numeric', 'boolean']);

export const segmentConditionSchema = z.object({
  id: z.string(),
  feature: z.string(),
  operator: operatorType,
  values: z.array(z.union([z.string(), z.number(), z.boolean()])),
});

export const segmentGroupSchema = z.object({
  id: z.string(),
  logic: logicType,
  conditions: z.array(segmentConditionSchema),
});

export const segmentDefinitionSchema = z.object({
  name: z.string(),
  description: z.string(),
  groups: z.array(segmentGroupSchema),
  group_logic: logicType,
});

export const featureSchema = z.object({
  name: z.string(),
  display_name: z.string(),
  column: z.string(),
  type: featureType,
  operators: z.array(operatorType),
  description: z.string(),
  nullable: z.boolean(),
  null_rate: z.number().nullish(),
  distinct_values: z.number().nullish(),
  values: z.array(z.string()).nullish(),
  searchable: z.boolean().optional(),
  range: z.object({ min: z.number(), max: z.number() }).nullish(),
  brackets: z
    .array(z.object({ label: z.string(), min: z.number().optional(), max: z.number().optional() }))
    .nullish(),
});

export const featuresListResponseSchema = z.object({
  features: z.array(featureSchema),
});

export const featureValuesResponseSchema = z.object({
  values: z.array(z.string()),
  total: z.number(),
});

export const segmentPreviewResponseSchema = z.object({
  individual_count: z.number(),
  household_count: z.number(),
  sql: z.string().nullable(),
  execution_time_ms: z.number(),
});

export const segmentBuildResponseSchema = z.object({
  segment_id: z.string(),
  rows_inserted: z.number(),
  campaign_name: z.string(),
});

export const segmentListItemSchema = z.object({
  segment_name: z.string(),
  segment_definition: z.string(),
  quarter: z.string(),
  start_date: z.string(),
  end_date: z.string(),
});

export const listSegmentsResponseSchema = z.object({
  segments: z.array(segmentListItemSchema),
});

export const allSegmentsOverviewRowSchema = z.object({
  segment_name: z.string(),
  segment_definition: z.string(),
  quarter: z.string(),
  start_date: z.string(),
  end_date: z.string(),
  individual_count: z.number(),
  household_count: z.number(),
});

export const allSegmentsOverviewResponseSchema = z.object({
  rows: z.array(allSegmentsOverviewRowSchema),
});

export const segmentUpdateResponseSchema = z.object({
  status: z.string(),
  segment_name: z.string(),
});

export const agentParseResponseSchema = z.object({
  response_text: z.string(),
  segment: segmentDefinitionSchema.nullable().optional(),
  preview: z
    .object({
      individual_count: z.number(),
      household_count: z.number(),
    })
    .nullable()
    .optional(),
  sql: z.string().nullable().optional(),
});

export const agentSummarizeResponseSchema = z.object({
  summary: z.string(),
  suggested_name: z.string(),
});
