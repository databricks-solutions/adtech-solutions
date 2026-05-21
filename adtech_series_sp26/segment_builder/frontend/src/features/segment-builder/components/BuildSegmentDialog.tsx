/**
 * Dialog for building and saving a segment.
 */

import React, { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { segmentApi } from '../api/segmentApi';
import { useSegmentContext } from '../context/SegmentContext';

interface BuildResult {
  campaign_name: string;
  rows_inserted: number;
}

interface BuildSegmentDialogProps {
  isOpen: boolean;
  onClose: () => void;
  individualCount: number;
  householdCount: number;
}

const currentYY = new Date().getFullYear() % 100;
const currentQuarter = `${currentYY}Q${Math.ceil((new Date().getMonth() + 1) / 3)}`;

const quarterOptions = [
  { value: `${currentYY}Q1`, label: `${currentYY}Q1 (Jan-Mar)` },
  { value: `${currentYY}Q2`, label: `${currentYY}Q2 (Apr-Jun)` },
  { value: `${currentYY}Q3`, label: `${currentYY}Q3 (Jul-Sep)` },
  { value: `${currentYY}Q4`, label: `${currentYY}Q4 (Oct-Dec)` },
];

/** Return start and end dates (YYYY-MM-DD) for a quarter string e.g. "25Q1". */
function getQuarterDateRange(quarter: string): { startDate: string; endDate: string } {
  const yy = parseInt(quarter.slice(0, 2), 10);
  const year = 2000 + yy;
  const q = parseInt(quarter.replace(/^\d+Q/, ''), 10);
  const startMonth = (q - 1) * 3 + 1;
  const endMonth = q * 3;
  const startDate = new Date(year, startMonth - 1, 1);
  const endDate = new Date(year, endMonth, 0); // last day of endMonth
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { startDate: fmt(startDate), endDate: fmt(endDate) };
}

export const BuildSegmentDialog: React.FC<BuildSegmentDialogProps> = ({
  isOpen,
  onClose,
  individualCount,
  householdCount,
}) => {
  const { state } = useSegmentContext();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [quarter, setQuarter] = useState(currentQuarter);
  const [startDate, setStartDate] = useState(() => getQuarterDateRange(currentQuarter).startDate);
  const [endDate, setEndDate] = useState(() => getQuarterDateRange(currentQuarter).endDate);
  const [buildResult, setBuildResult] = useState<BuildResult | null>(null);
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);

  // When dialog opens, auto-populate description and suggested name from LLM summary of segment + chat
  useEffect(() => {
    if (!isOpen) return;
    const segment = state.segment;
    const hasConditions = segment.groups.some((g) =>
      g.conditions.some((c) => c.feature && c.values.length > 0)
    );
    if (!hasConditions) return;
    setName('');
    setDescription('');
    let cancelled = false;
    const history = state.chatHistory.map((m) => ({
      role: m.role === 'agent' ? 'assistant' : m.role,
      content: m.content,
    }));
    segmentApi
      .summarizeSegment(segment, history)
      .then(({ summary, suggested_name }) => {
        if (cancelled) return;
        if (summary) setDescription(summary);
        if (suggested_name) setName(suggested_name);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  const resetForm = () => {
    setName('');
    setDescription('');
    setDescriptionExpanded(false);
    setQuarter(currentQuarter);
    const range = getQuarterDateRange(currentQuarter);
    setStartDate(range.startDate);
    setEndDate(range.endDate);
    setBuildResult(null);
    buildMutation.reset();
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const buildMutation = useMutation({
    mutationFn: async () => {
      return segmentApi.buildSegment(
        { ...state.segment, description },
        name,
        quarter,
        startDate,
        endDate
      );
    },
    onSuccess: (data) => {
      setBuildResult({
        campaign_name: data.campaign_name,
        rows_inserted: data.rows_inserted,
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    buildMutation.mutate();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={handleClose}
      />

      {/* Dialog */}
      <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        {buildResult ? (
          /* Success Summary */
          <div className="text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 mb-4">
              <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Segment Built Successfully
            </h2>
            <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Segment Name</span>
                <span className="font-semibold text-gray-900">{buildResult.campaign_name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Rows Inserted</span>
                <span className="font-semibold text-gray-900">{buildResult.rows_inserted.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Quarter</span>
                <span className="font-semibold text-gray-900">{quarter}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Date Range</span>
                <span className="font-semibold text-gray-900">{startDate} — {endDate}</span>
              </div>
              {description && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Description</span>
                  <span className="font-semibold text-gray-900 text-right max-w-[60%]">{description}</span>
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={handleClose}
              className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Done
            </button>
          </div>
        ) : (
          /* Build Form */
          <>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Build Segment
            </h2>

            {/* Preview Summary */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Individuals:</span>
                <span className="font-semibold">{individualCount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm mt-1">
                <span className="text-gray-500">Households:</span>
                <span className="font-semibold">{householdCount.toLocaleString()}</span>
              </div>
            </div>

            {/* Inline Error Banner */}
            {buildMutation.isError && (
              <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {buildMutation.error?.message ?? 'An error occurred while building the segment.'}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              {/* Segment Name */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Segment Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., CA_Dog_Owners_25_54"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {/* Description */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <div className="relative">
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe the target audience..."
                    rows={descriptionExpanded ? 6 : 2}
                    className={`w-full px-3 py-2 pr-9 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${descriptionExpanded ? 'resize-y min-h-[120px]' : 'resize-none'}`}
                  />
                  <button
                    type="button"
                    onClick={() => setDescriptionExpanded((e) => !e)}
                    className="absolute bottom-2 right-2 p-1 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                    title={descriptionExpanded ? 'Collapse' : 'Expand to see more'}
                    aria-label={descriptionExpanded ? 'Collapse description' : 'Expand description'}
                  >
                    {descriptionExpanded ? (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 15.75l7.5-7.5 7.5 7.5" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Quarter */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quarter *
                </label>
                <select
                  value={quarter}
                  onChange={(e) => {
                    const q = e.target.value;
                    setQuarter(q);
                    const range = getQuarterDateRange(q);
                    setStartDate(range.startDate);
                    setEndDate(range.endDate);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  {quarterOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Date Range */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date *
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date *
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  disabled={buildMutation.isPending}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={buildMutation.isPending}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {buildMutation.isPending ? (
                    <>
                      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Building...
                    </>
                  ) : (
                    'Build Segment'
                  )}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default BuildSegmentDialog;
