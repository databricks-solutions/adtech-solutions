/**
 * TypeScript types for segment builder.
 */

export type OperatorType = 'IS' | 'IN' | 'NOT' | 'BETWEEN' | 'GT' | 'LT' | 'GTE' | 'LTE';
export type LogicType = 'AND' | 'OR';
export type FeatureType = 'categorical' | 'numeric' | 'boolean';
export type ModeType = 'agent' | 'builder';

export interface SegmentCondition {
  id: string;
  feature: string;
  operator: OperatorType;
  values: (string | number | boolean)[];
}

export interface SegmentGroup {
  id: string;
  logic: LogicType;
  conditions: SegmentCondition[];
}

export interface SegmentDefinition {
  name: string;
  description: string;
  groups: SegmentGroup[];
  groupLogic: LogicType;
}

export interface Feature {
  name: string;
  display_name: string;
  column: string;
  type: FeatureType;
  operators: OperatorType[];
  description: string;
  nullable: boolean;
  null_rate?: number;
  distinct_values?: number;
  values?: string[];
  searchable?: boolean;
  range?: { min: number; max: number };
  brackets?: Array<{ label: string; min?: number; max?: number }>;
}

export interface SegmentPreview {
  individual_count: number;
  household_count: number;
  sql: string | null;
  execution_time_ms: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
  segment?: SegmentDefinition;
  preview?: SegmentPreview;
}

// API Response types
export interface FeaturesListResponse {
  features: Feature[];
}

export interface SegmentPreviewRequest {
  segment: SegmentDefinition;
  include_sql: boolean;
}

export interface SegmentPreviewResponse extends SegmentPreview {}

// State types
export interface SegmentState {
  mode: ModeType;
  segment: SegmentDefinition;
  preview: SegmentPreview | null;
  isLoading: boolean;
  error: string | null;
  chatHistory: ChatMessage[];
}

export type SegmentAction =
  | { type: 'SET_MODE'; payload: ModeType }
  | { type: 'SET_SEGMENT'; payload: SegmentDefinition }
  | { type: 'ADD_GROUP' }
  | { type: 'REMOVE_GROUP'; payload: string }
  | { type: 'SET_GROUP_LOGIC'; payload: { groupId: string; logic: LogicType } }
  | { type: 'ADD_CONDITION'; payload: { groupId: string } }
  | { type: 'UPDATE_CONDITION'; payload: { groupId: string; condition: SegmentCondition } }
  | { type: 'REMOVE_CONDITION'; payload: { groupId: string; conditionId: string } }
  | { type: 'SET_PREVIEW'; payload: SegmentPreview | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_CHAT_MESSAGE'; payload: ChatMessage }
  | { type: 'CLEAR_CHAT' }
  | { type: 'RESET_SEGMENT' }
  | { type: 'SET_SEGMENT_GROUP_LOGIC'; payload: LogicType };
