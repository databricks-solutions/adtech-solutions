/**
 * Dialog to view and edit segment metadata (definition, quarter, flight dates).
 * Updates the underlying Delta table on save.
 */

import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { segmentApi } from '../api/segmentApi';

export interface SegmentOverviewRow {
  segment_name: string;
  segment_definition: string;
  quarter: string;
  start_date: string;
  end_date: string;
  individual_count: number;
  household_count: number;
}

const currentYY = new Date().getFullYear() % 100;
const currentQuarter = `${currentYY}Q${Math.ceil((new Date().getMonth() + 1) / 3)}`;

const quarterOptions = [
  { value: `${currentYY}Q1`, label: `${currentYY}Q1 (Jan-Mar)` },
  { value: `${currentYY}Q2`, label: `${currentYY}Q2 (Apr-Jun)` },
  { value: `${currentYY}Q3`, label: `${currentYY}Q3 (Jul-Sep)` },
  { value: `${currentYY}Q4`, label: `${currentYY}Q4 (Oct-Dec)` },
];

function getQuarterDateRange(quarter: string): { startDate: string; endDate: string } {
  const yy = parseInt(quarter.slice(0, 2), 10);
  const year = 2000 + yy;
  const q = parseInt(quarter.replace(/^\d+Q/, ''), 10);
  const startMonth = (q - 1) * 3 + 1;
  const endMonth = q * 3;
  const startDate = new Date(year, startMonth - 1, 1);
  const endDate = new Date(year, endMonth, 0);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { startDate: fmt(startDate), endDate: fmt(endDate) };
}

function formatDate(value: unknown): string {
  if (value == null) return '';
  const s = String(value);
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10);
  return s;
}

export interface EditSegmentDialogProps {
  isOpen: boolean;
  onClose: () => void;
  row: SegmentOverviewRow | null;
}

export const EditSegmentDialog: React.FC<EditSegmentDialogProps> = ({
  isOpen,
  onClose,
  row,
}) => {
  const queryClient = useQueryClient();
  const [description, setDescription] = useState('');
  const [quarter, setQuarter] = useState(currentQuarter);
  const [startDate, setStartDate] = useState(() => getQuarterDateRange(currentQuarter).startDate);
  const [endDate, setEndDate] = useState(() => getQuarterDateRange(currentQuarter).endDate);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!isOpen || !row) return;
    setDescription(row.segment_definition ?? '');
    setQuarter(row.quarter ?? currentQuarter);
    setStartDate(formatDate(row.start_date) || getQuarterDateRange(currentQuarter).startDate);
    setEndDate(formatDate(row.end_date) || getQuarterDateRange(currentQuarter).endDate);
    setSaved(false);
  }, [isOpen, row]);

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!row) throw new Error('No segment selected');
      return segmentApi.updateSegmentMetadata(row.segment_name, {
        segment_definition: description,
        quarter,
        start_date: startDate,
        end_date: endDate,
      });
    },
    onSuccess: () => {
      setSaved(true);
      queryClient.invalidateQueries({ queryKey: ['allSegmentsOverview'] });
    },
  });

  const handleClose = () => {
    updateMutation.reset();
    onClose();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate();
  };

  if (!isOpen || !row) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} aria-hidden />

      <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        {saved ? (
          <div className="text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 mb-4">
              <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Segment updated</h2>
            <p className="text-gray-600 text-sm mb-6">Metadata has been saved to the Delta table.</p>
            <button
              type="button"
              onClick={handleClose}
              className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Done
            </button>
          </div>
        ) : (
          <>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Edit Segment</h2>

            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Segment Name</span>
                <span className="font-semibold text-gray-900">{row.segment_name}</span>
              </div>
              <div className="flex justify-between text-sm mt-1">
                <span className="text-gray-500">Individuals</span>
                <span className="font-semibold">{Number(row.individual_count ?? 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm mt-1">
                <span className="text-gray-500">Households</span>
                <span className="font-semibold">{Number(row.household_count ?? 0).toLocaleString()}</span>
              </div>
            </div>

            {updateMutation.isError && (
              <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {updateMutation.error?.message ?? 'Failed to update segment.'}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Segment Definition / description..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Quarter *</label>
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

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Flight Start Date *</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Flight End Date *</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  disabled={updateMutation.isPending}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {updateMutation.isPending ? (
                    <>
                      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Saving...
                    </>
                  ) : (
                    'Save changes'
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

export default EditSegmentDialog;
