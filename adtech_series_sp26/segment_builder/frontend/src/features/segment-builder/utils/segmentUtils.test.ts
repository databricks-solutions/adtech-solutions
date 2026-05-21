import { describe, it, expect } from 'vitest';
import { filterIncompleteConditions } from './segmentUtils';
import type { SegmentDefinition } from '../types';

function seg(
  groups: Array<{ id: string; logic: 'AND' | 'OR'; conditions: Array<{ id: string; feature: string; operator: string; values: (string | number | boolean)[] }> }>,
  groupLogic: 'AND' | 'OR' = 'AND'
): SegmentDefinition {
  return {
    name: 'test',
    description: '',
    groups,
    groupLogic,
  };
}

describe('filterIncompleteConditions', () => {
  it('removes conditions with empty feature', () => {
    const input = seg([
      {
        id: 'g1',
        logic: 'AND',
        conditions: [
          { id: 'c1', feature: '', operator: 'IS', values: ['CA'] },
          { id: 'c2', feature: 'state', operator: 'IS', values: ['TX'] },
        ],
      },
    ]);
    const result = filterIncompleteConditions(input);
    expect(result.groups).toHaveLength(1);
    expect(result.groups[0].conditions).toHaveLength(1);
    expect(result.groups[0].conditions[0].feature).toBe('state');
  });

  it('removes conditions with no values', () => {
    const input = seg([
      {
        id: 'g1',
        logic: 'AND',
        conditions: [
          { id: 'c1', feature: 'state', operator: 'IS', values: [] },
          { id: 'c2', feature: 'gender', operator: 'IN', values: ['Male', 'Female'] },
        ],
      },
    ]);
    const result = filterIncompleteConditions(input);
    expect(result.groups[0].conditions).toHaveLength(1);
    expect(result.groups[0].conditions[0].feature).toBe('gender');
  });

  it('removes groups that end up with no conditions', () => {
    const input = seg([
      {
        id: 'g1',
        logic: 'AND',
        conditions: [
          { id: 'c1', feature: '', operator: 'IS', values: [] },
        ],
      },
      {
        id: 'g2',
        logic: 'AND',
        conditions: [
          { id: 'c2', feature: 'state', operator: 'IS', values: ['CA'] },
        ],
      },
    ]);
    const result = filterIncompleteConditions(input);
    expect(result.groups).toHaveLength(1);
    expect(result.groups[0].id).toBe('g2');
  });

  it('keeps complete conditions unchanged', () => {
    const input = seg([
      {
        id: 'g1',
        logic: 'AND',
        conditions: [
          { id: 'c1', feature: 'state', operator: 'IS', values: ['CA'] },
          { id: 'c2', feature: 'age', operator: 'BETWEEN', values: [25, 54] },
        ],
      },
    ]);
    const result = filterIncompleteConditions(input);
    expect(result.groups).toHaveLength(1);
    expect(result.groups[0].conditions).toHaveLength(2);
    expect(result.name).toBe('test');
  });

  it('returns empty groups array when all conditions are incomplete', () => {
    const input = seg([
      {
        id: 'g1',
        logic: 'AND',
        conditions: [
          { id: 'c1', feature: '', operator: 'IS', values: ['x'] },
          { id: 'c2', feature: 'state', operator: 'IS', values: [] },
        ],
      },
    ]);
    const result = filterIncompleteConditions(input);
    expect(result.groups).toHaveLength(0);
  });
});
