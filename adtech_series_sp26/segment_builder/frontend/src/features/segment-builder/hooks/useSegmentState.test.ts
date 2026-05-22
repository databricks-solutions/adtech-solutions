import { describe, it, expect } from 'vitest';
import { segmentReducer } from './useSegmentState';
import type { SegmentState, SegmentDefinition, SegmentGroup, SegmentCondition } from '../types';

function makeState(overrides: Partial<SegmentState> = {}): SegmentState {
  const segment: SegmentDefinition = {
    name: '',
    description: '',
    groupLogic: 'AND',
    groups: [
      {
        id: 'g1',
        logic: 'AND',
        conditions: [
          { id: 'c1', feature: 'state', operator: 'IS', values: ['CA'] },
        ],
      },
    ],
  };
  return {
    mode: 'builder',
    segment,
    preview: null,
    isLoading: false,
    error: null,
    chatHistory: [],
    ...overrides,
  };
}

describe('segmentReducer', () => {
  it('SET_MODE updates mode', () => {
    const state = makeState({ mode: 'builder' });
    const next = segmentReducer(state, { type: 'SET_MODE', payload: 'agent' });
    expect(next.mode).toBe('agent');
  });

  it('SET_SEGMENT replaces segment', () => {
    const state = makeState();
    const newSegment: SegmentDefinition = {
      name: 'new',
      description: 'd',
      groupLogic: 'OR',
      groups: [],
    };
    const next = segmentReducer(state, { type: 'SET_SEGMENT', payload: newSegment });
    expect(next.segment.name).toBe('new');
    expect(next.segment.groups).toHaveLength(0);
  });

  it('ADD_GROUP appends a new group', () => {
    const state = makeState();
    expect(state.segment.groups).toHaveLength(1);
    const next = segmentReducer(state, { type: 'ADD_GROUP' });
    expect(next.segment.groups).toHaveLength(2);
    expect(next.segment.groups[1].conditions).toHaveLength(1);
    expect(next.segment.groups[1].logic).toBe('AND');
  });

  it('REMOVE_GROUP removes the group by id', () => {
    const state = makeState();
    state.segment.groups.push({
      id: 'g2',
      logic: 'OR',
      conditions: [{ id: 'c2', feature: 'gender', operator: 'IS', values: ['Male'] }],
    });
    const next = segmentReducer(state, { type: 'REMOVE_GROUP', payload: 'g2' });
    expect(next.segment.groups).toHaveLength(1);
    expect(next.segment.groups[0].id).toBe('g1');
  });

  it('SET_GROUP_LOGIC updates logic for the given group', () => {
    const state = makeState();
    const next = segmentReducer(state, {
      type: 'SET_GROUP_LOGIC',
      payload: { groupId: 'g1', logic: 'OR' },
    });
    expect(next.segment.groups[0].logic).toBe('OR');
  });

  it('UPDATE_CONDITION updates the condition in the group', () => {
    const state = makeState();
    const updated: SegmentCondition = {
      id: 'c1',
      feature: 'state',
      operator: 'IN',
      values: ['CA', 'TX'],
    };
    const next = segmentReducer(state, {
      type: 'UPDATE_CONDITION',
      payload: { groupId: 'g1', condition: updated },
    });
    expect(next.segment.groups[0].conditions[0].operator).toBe('IN');
    expect(next.segment.groups[0].conditions[0].values).toEqual(['CA', 'TX']);
  });

  it('REMOVE_CONDITION removes the condition from the group', () => {
    const state = makeState();
    state.segment.groups[0].conditions.push({
      id: 'c2',
      feature: 'gender',
      operator: 'IS',
      values: ['Female'],
    });
    const next = segmentReducer(state, {
      type: 'REMOVE_CONDITION',
      payload: { groupId: 'g1', conditionId: 'c2' },
    });
    expect(next.segment.groups[0].conditions).toHaveLength(1);
    expect(next.segment.groups[0].conditions[0].id).toBe('c1');
  });

  it('SET_PREVIEW updates preview', () => {
    const state = makeState();
    const next = segmentReducer(state, {
      type: 'SET_PREVIEW',
      payload: { individual_count: 100, household_count: 50, sql: null, execution_time_ms: 10 },
    });
    expect(next.preview?.individual_count).toBe(100);
    expect(next.preview?.household_count).toBe(50);
  });

  it('SET_LOADING updates isLoading', () => {
    const state = makeState();
    expect(segmentReducer(state, { type: 'SET_LOADING', payload: true }).isLoading).toBe(true);
    expect(segmentReducer(state, { type: 'SET_LOADING', payload: false }).isLoading).toBe(false);
  });

  it('RESET_SEGMENT resets segment to initial and clears preview', () => {
    const state = makeState();
    state.preview = { individual_count: 1, household_count: 1, sql: null, execution_time_ms: 0 };
    const next = segmentReducer(state, { type: 'RESET_SEGMENT' });
    expect(next.preview).toBeNull();
    expect(next.segment.groups).toHaveLength(1);
expect(next.segment.groupLogic).toBe('AND');
  });

  it('SET_SEGMENT_GROUP_LOGIC updates segment groupLogic', () => {
    const state = makeState();
    const next = segmentReducer(state, { type: 'SET_SEGMENT_GROUP_LOGIC', payload: 'OR' });
    expect(next.segment.groupLogic).toBe('OR');
  });
});
