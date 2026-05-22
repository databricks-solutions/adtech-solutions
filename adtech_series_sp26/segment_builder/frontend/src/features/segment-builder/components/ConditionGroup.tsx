/**
 * Group of conditions with AND/OR logic.
 */

import React from 'react';
import { useSegmentContext } from '../context/SegmentContext';
import { ConditionRow } from './ConditionRow';
import type { SegmentGroup, LogicType } from '../types';

interface ConditionGroupProps {
  group: SegmentGroup;
  groupIndex: number;
  canRemove: boolean;
}

export const ConditionGroup: React.FC<ConditionGroupProps> = ({
  group,
  groupIndex,
  canRemove,
}) => {
  const { actions } = useSegmentContext();
  const { setGroupLogic, addCondition, updateCondition, removeCondition, removeGroup } = actions;

  const handleLogicToggle = () => {
    const newLogic: LogicType = group.logic === 'AND' ? 'OR' : 'AND';
    setGroupLogic(group.id, newLogic);
  };

  return (
    <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
      {/* Group Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500 tracking-wide">
            Segment Criteria {groupIndex + 1}
          </span>
          <button
            onClick={handleLogicToggle}
            className={`px-2 py-0.5 text-xs font-medium rounded transition-colors ${
              group.logic === 'AND'
                ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
            }`}
          >
            {group.logic}
          </button>
        </div>
        {canRemove && (
          <button
            onClick={() => removeGroup(group.id)}
            className="text-xs text-gray-400 hover:text-red-500 transition-colors"
          >
            Remove group
          </button>
        )}
      </div>

      {/* Conditions */}
      <div className="space-y-2">
        {group.conditions.map((condition, condIndex) => (
          <div key={condition.id}>
            {condIndex > 0 && (
              <div className="flex items-center justify-center my-2">
                <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                  group.logic === 'AND'
                    ? 'bg-blue-50 text-blue-600'
                    : 'bg-purple-50 text-purple-600'
                }`}>
                  {group.logic}
                </span>
              </div>
            )}
            <ConditionRow
              condition={condition}
              onUpdate={(updated) => updateCondition(group.id, updated)}
              onRemove={() => removeCondition(group.id, condition.id)}
              canRemove={group.conditions.length > 1}
            />
          </div>
        ))}
      </div>

      {/* Add Condition Button */}
      <button
        onClick={() => addCondition(group.id)}
        className="mt-3 w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-blue-400 hover:text-blue-500 transition-colors"
      >
        + Add Condition
      </button>
    </div>
  );
};

export default ConditionGroup;
