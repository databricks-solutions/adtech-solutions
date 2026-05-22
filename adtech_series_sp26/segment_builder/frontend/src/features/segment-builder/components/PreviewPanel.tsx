/**
 * Preview panel showing segment counts and SQL.
 */

import React, { useState } from 'react';
import { useSegmentPreview } from '../hooks/useSegmentPreview';
import { BuildSegmentDialog } from './BuildSegmentDialog';

export const PreviewPanel: React.FC = () => {
  const { preview, isLoading, error } = useSegmentPreview();
  const [showSql, setShowSql] = useState(false);
  const [showBuildDialog, setShowBuildDialog] = useState(false);

  return (
    <div className="bg-white border-t border-gray-200 shadow-lg">
      {/* Main Preview */}
      <div className="px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Counts */}
          <div className="flex items-center gap-6">
            <div>
              <span className="text-xs text-gray-500 uppercase tracking-wide">Individuals</span>
              <div className="text-2xl font-bold text-gray-900">
                {isLoading ? (
                  <span className="text-gray-300">---</span>
                ) : preview ? (
                  preview.individual_count.toLocaleString()
                ) : (
                  '0'
                )}
              </div>
            </div>
            <div className="h-10 w-px bg-gray-200" />
            <div>
              <span className="text-xs text-gray-500 uppercase tracking-wide">Households</span>
              <div className="text-2xl font-bold text-gray-900">
                {isLoading ? (
                  <span className="text-gray-300">---</span>
                ) : preview ? (
                  preview.household_count.toLocaleString()
                ) : (
                  '0'
                )}
              </div>
            </div>
            {isLoading && (
              <div className="ml-4">
                <svg className="w-5 h-5 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSql(!showSql)}
              disabled={!preview?.sql}
              className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {showSql ? 'Hide SQL' : 'View SQL'}
            </button>
            <button
              onClick={() => setShowBuildDialog(true)}
              disabled={!preview || preview.individual_count === 0}
              className="px-4 py-2 bg-blue-500 text-white text-sm font-medium rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Build Segment
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-2 px-3 py-2 bg-red-50 text-red-600 text-sm rounded-lg">
            {error}
          </div>
        )}

        {/* Execution Time */}
        {preview && !isLoading && (
          <div className="mt-1 text-xs text-gray-400">
            Query executed in {preview.execution_time_ms.toFixed(0)}ms
          </div>
        )}
      </div>

      {/* SQL Viewer */}
      {showSql && preview?.sql && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Generated SQL
            </span>
            <button
              onClick={() => navigator.clipboard.writeText(preview.sql || '')}
              className="text-xs text-blue-500 hover:text-blue-600 font-medium"
            >
              Copy
            </button>
          </div>
          <pre className="text-xs text-gray-700 bg-white p-3 rounded-lg border border-gray-200 overflow-x-auto whitespace-pre-wrap font-mono">
            {preview.sql}
          </pre>
        </div>
      )}

      {/* Build Segment Dialog */}
      <BuildSegmentDialog
        isOpen={showBuildDialog}
        onClose={() => setShowBuildDialog(false)}
        individualCount={preview?.individual_count || 0}
        householdCount={preview?.household_count || 0}
      />
    </div>
  );
};

export default PreviewPanel;
