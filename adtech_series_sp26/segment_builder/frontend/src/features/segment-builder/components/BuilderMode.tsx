/**
 * Visual query builder mode.
 */

import React from 'react';
import { useSegmentContext } from '../context/SegmentContext';
import { useFeatures } from '../hooks/useFeatures';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { ConditionGroup } from './ConditionGroup';

export const BuilderMode: React.FC = () => {
  const { state, actions } = useSegmentContext();
  const { segment } = state;
  const { addGroup, setSegmentGroupLogic } = actions;
  const { data: features, isLoading: featuresLoading, isError: featuresError } = useFeatures();

  return (
    <div className="flex flex-col h-full">
      {/* Instructions */}
      <div className="px-4 py-3 bg-blue-50 border-b border-blue-100">
        <p className="text-sm text-blue-700">
          Build your audience segment by adding conditions. Use AND/OR logic to combine them.
        </p>
      </div>

      {/* Loading features (e.g. first visit) */}
      {featuresLoading && (
        <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
          <LoadingSpinner size="sm" label="Loading features…" />
        </div>
      )}

      {/* Features failed to load */}
      {featuresError && !featuresLoading && (
        <div className="px-4 py-3 border-b border-red-200 bg-red-50 flex items-center gap-2">
          <span className="text-sm text-red-700">
            Features could not be loaded. Check the connection and try again.
          </span>
        </div>
      )}

      {/* Condition Groups */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {segment.groups.map((group, index) => (
            <div key={group.id}>
              {index > 0 && (
                <div className="flex items-center justify-center my-4">
                  <div className="flex-1 h-px bg-gray-200" />
                  <button
                    type="button"
                    onClick={() =>
                      setSegmentGroupLogic(segment.groupLogic === 'AND' ? 'OR' : 'AND')
                    }
                    className={`px-3 py-1 mx-2 text-xs font-bold rounded cursor-pointer transition-colors ${
                      segment.groupLogic === 'AND'
                        ? 'bg-blue-100 text-blue-700 border border-blue-300 hover:bg-blue-200'
                        : 'bg-purple-100 text-purple-700 border border-purple-300 hover:bg-purple-200'
                    }`}
                  >
                    {segment.groupLogic}
                  </button>
                  <div className="flex-1 h-px bg-gray-200" />
                </div>
              )}
              <ConditionGroup
                group={group}
                groupIndex={index}
                canRemove={segment.groups.length > 1}
              />
            </div>
          ))}
        </div>

        {/* Add Group Button */}
        <button
          onClick={addGroup}
          className="mt-4 w-full py-3 border-2 border-dashed border-gray-300 rounded-xl text-sm font-medium text-gray-500 hover:border-blue-400 hover:text-blue-500 transition-colors"
        >
          + Add Criteria
        </button>
      </div>
    </div>
  );
};

export default BuilderMode;
