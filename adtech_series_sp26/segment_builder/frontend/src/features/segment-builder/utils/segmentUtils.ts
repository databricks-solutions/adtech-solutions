/**
 * Segment helpers (pure functions) for use in API and tests.
 */

import type { SegmentDefinition, SegmentCondition, SegmentGroup } from '../types';

/**
 * Filter out incomplete conditions from a segment.
 * A condition is complete if it has a feature and at least one value.
 */
export function filterIncompleteConditions(
  segment: SegmentDefinition
): SegmentDefinition {
  const filteredGroups = segment.groups
    .map((group): SegmentGroup => ({
      ...group,
      conditions: group.conditions.filter(
        (condition: SegmentCondition) =>
          condition.feature !== '' && condition.values.length > 0
      ),
    }))
    .filter((group) => group.conditions.length > 0);

  return {
    ...segment,
    groups: filteredGroups,
  };
}
