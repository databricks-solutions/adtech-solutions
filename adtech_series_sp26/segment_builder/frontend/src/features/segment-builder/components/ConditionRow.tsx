/**
 * Single condition row in the query builder.
 */

import React, { useMemo } from 'react';
import { useFeatures, useFeatureValues } from '../hooks/useFeatures';
import type { SegmentCondition, OperatorType } from '../types';

/** Display labels for operators in the dropdown (value sent to API unchanged). */
const OPERATOR_LABELS: Record<OperatorType, string> = {
  IS: 'IS',
  IN: 'IN',
  NOT: 'NOT',
  BETWEEN: 'BETWEEN',
  GT: '>',
  LT: '<',
  GTE: '>=',
  LTE: '<=',
};

interface ConditionRowProps {
  condition: SegmentCondition;
  onUpdate: (condition: SegmentCondition) => void;
  onRemove: () => void;
  canRemove: boolean;
}

export const ConditionRow: React.FC<ConditionRowProps> = ({
  condition,
  onUpdate,
  onRemove,
  canRemove,
}) => {
  const { data: features = [] } = useFeatures();

  const selectedFeature = useMemo(
    () => features.find((f) => f.name === condition.feature),
    [features, condition.feature]
  );

  const { data: featureValues = [] } = useFeatureValues(
    condition.feature,
    undefined,
    !!condition.feature && selectedFeature?.type === 'categorical'
  );

  // Get available operators for the selected feature
  const operators = selectedFeature?.operators || ['IS', 'IN', 'NOT'];

  // Check if this is a bracket-based selection
  const isBracketMode = useMemo(
    () =>
      !!selectedFeature?.brackets &&
      (condition.operator === 'IN' || condition.operator === 'NOT'),
    [selectedFeature, condition.operator]
  );

  // Get available values
  const availableValues = useMemo(() => {
    if (isBracketMode && selectedFeature?.brackets) {
      return selectedFeature.brackets.map((b) => b.label);
    }
    if (selectedFeature?.type === 'boolean') {
      return ['true', 'false'];
    }
    if (selectedFeature?.values) {
      return selectedFeature.values;
    }
    return featureValues;
  }, [selectedFeature, featureValues, isBracketMode]);

  const handleFeatureChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newFeature = e.target.value;
    const feature = features.find((f) => f.name === newFeature);

    // Reset operator and values when feature changes
    onUpdate({
      ...condition,
      feature: newFeature,
      operator: feature?.operators[0] || 'IS',
      values: [],
    });
  };

  const handleOperatorChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onUpdate({
      ...condition,
      operator: e.target.value as OperatorType,
    });
  };

  const handleValueChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const value = e.target.value;

    if (selectedFeature?.type === 'boolean') {
      onUpdate({
        ...condition,
        values: [value === 'true'],
      });
    } else if (selectedFeature?.type === 'numeric') {
      onUpdate({
        ...condition,
        values: value ? [Number(value)] : [],
      });
    } else {
      onUpdate({
        ...condition,
        values: value ? [value] : [],
      });
    }
  };

  const handleMultiValueChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
    onUpdate({
      ...condition,
      values: selectedOptions,
    });
  };

  const handleValueToggle = (value: string) => {
    const currentValues = condition.values.map(String);
    const newValues = currentValues.includes(value)
      ? currentValues.filter(v => v !== value)
      : [...currentValues, value];
    onUpdate({
      ...condition,
      values: newValues,
    });
  };

  // Check if operator supports multiple values
  const isMultiSelect = condition.operator === 'IN' || condition.operator === 'NOT';

  const handleBetweenChange = (index: number, value: string) => {
    const newValues = [...condition.values];
    newValues[index] = Number(value) || 0;
    onUpdate({
      ...condition,
      values: newValues,
    });
  };

  return (
    <div className="flex items-center gap-2 p-2 bg-white rounded-lg border border-gray-200">
      {/* Feature Selector */}
      <select
        value={condition.feature}
        onChange={handleFeatureChange}
        className="flex-1 min-w-[140px] px-3 py-2 rounded-md border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">Select feature...</option>
        {features.map((feature) => (
          <option key={feature.name} value={feature.name}>
            {feature.display_name}
          </option>
        ))}
      </select>

      {/* Operator Selector */}
      <select
        value={condition.operator}
        onChange={handleOperatorChange}
        disabled={!condition.feature}
        className="px-3 py-2 rounded-md border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
      >
        {operators.map((op) => (
          <option key={op} value={op}>
            {OPERATOR_LABELS[op]}
          </option>
        ))}
      </select>

      {/* Value Input - depends on feature type and operator */}
      {condition.operator === 'BETWEEN' ? (
        <div className="flex items-center gap-1">
          <input
            type="number"
            value={condition.values[0] || ''}
            onChange={(e) => handleBetweenChange(0, e.target.value)}
            placeholder="Min"
            className="w-20 px-2 py-2 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-gray-500 text-sm">to</span>
          <input
            type="number"
            value={condition.values[1] || ''}
            onChange={(e) => handleBetweenChange(1, e.target.value)}
            placeholder="Max"
            className="w-20 px-2 py-2 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      ) : selectedFeature?.type === 'numeric' && !isBracketMode ? (
        <input
          type="number"
          value={condition.values[0] || ''}
          onChange={handleValueChange}
          placeholder="Value"
          min={selectedFeature.range?.min}
          max={selectedFeature.range?.max}
          className="w-24 px-3 py-2 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      ) : isMultiSelect && availableValues.length > 0 ? (
        <div className="flex-1 min-w-[200px]">
          <div className="flex flex-wrap gap-1 p-2 border border-gray-300 rounded-md bg-white min-h-[38px]">
            {condition.values.length === 0 ? (
              <span className="text-gray-400 text-sm">Select values...</span>
            ) : (
              condition.values.map((val) => (
                <span
                  key={String(val)}
                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full"
                >
                  {String(val)}
                  <button
                    type="button"
                    onClick={() => handleValueToggle(String(val))}
                    className="hover:text-blue-900"
                  >
                    ×
                  </button>
                </span>
              ))
            )}
          </div>
          <select
            value=""
            onChange={(e) => {
              if (e.target.value) handleValueToggle(e.target.value);
            }}
            disabled={!condition.feature}
            className="mt-1 w-full px-3 py-1 rounded-md border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          >
            <option value="">+ Add value</option>
            {availableValues
              .filter((v) => !condition.values.map(String).includes(String(v)))
              .map((value) => (
                <option key={String(value)} value={String(value)}>
                  {String(value)}
                </option>
              ))}
          </select>
        </div>
      ) : (
        <select
          value={String(condition.values[0] || '')}
          onChange={handleValueChange}
          disabled={!condition.feature}
          className="flex-1 min-w-[140px] px-3 py-2 rounded-md border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        >
          <option value="">Select value...</option>
          {availableValues.map((value) => (
            <option key={String(value)} value={String(value)}>
              {String(value)}
            </option>
          ))}
        </select>
      )}

      {/* Remove Button */}
      <button
        onClick={onRemove}
        disabled={!canRemove}
        className="p-2 text-gray-400 hover:text-red-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        title="Remove condition"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
};

export default ConditionRow;
