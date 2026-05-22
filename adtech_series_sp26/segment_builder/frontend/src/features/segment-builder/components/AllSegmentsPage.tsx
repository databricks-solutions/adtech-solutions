/**
 * All Segments page: definitions joined with campaigns, grouped by campaign with counts.
 */

import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleRight } from '@fortawesome/free-solid-svg-icons';
import { PageHeader } from '../../../components/PageHeader';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { settingsApi } from '../../../api/settingsApi';
import { segmentApi } from '../api/segmentApi';
import { EditSegmentDialog, type SegmentOverviewRow } from './EditSegmentDialog';

const DEFAULT_LABELS: Record<string, string> = {
  segment_name: 'Segment Name',
  segment_definition: 'Segment Definition',
  quarter: 'Quarter',
  start_date: 'Flight Start Date',
  end_date: 'Flight End Date',
  megacorp_hhid: 'Household Identifier',
  megacorp_indid: 'Individual Identifier',
};

export const AllSegmentsPage: React.FC = () => {
  const [editRow, setEditRow] = useState<SegmentOverviewRow | null>(null);
  const [quarterFilter, setQuarterFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedDefinitions, setExpandedDefinitions] = useState<Set<string>>(new Set());

  const toggleDefinition = (segmentName: string) => {
    setExpandedDefinitions((prev) => {
      const next = new Set(prev);
      if (next.has(segmentName)) next.delete(segmentName);
      else next.add(segmentName);
      return next;
    });
  };

  const { data: settings } = useQuery({
    queryKey: ['settingsTables'],
    queryFn: () => settingsApi.getTables(),
  });
  const columnLabels = useMemo(
    () => ({ ...DEFAULT_LABELS, ...settings?.column_configs?.segment_info_labels }),
    [settings?.column_configs?.segment_info_labels]
  );
  const segmentListConfig = settings?.column_configs?.segment_list;
  const householdCountHeader =
    columnLabels[segmentListConfig?.identity_household_column ?? 'megacorp_hhid'] ?? 'Household Identifier';
  const individualCountHeader =
    columnLabels[segmentListConfig?.identity_individual_column ?? 'megacorp_indid'] ?? 'Individual Identifier';

  const { data: rows, isLoading, error } = useQuery({
    queryKey: ['allSegmentsOverview'],
    queryFn: () => segmentApi.getAllSegmentsOverview(),
  });

  const rawList = rows ?? [];

  const quarters = useMemo(() => {
    const set = new Set<string>();
    rawList.forEach((row) => {
      if (row.quarter) set.add(row.quarter);
    });
    return Array.from(set).sort();
  }, [rawList]);

  const list = useMemo(() => {
    return rawList.filter((row) => {
      if (quarterFilter && row.quarter !== quarterFilter) return false;
      const q = searchQuery.trim().toLowerCase();
      if (!q) return true;
      const name = (row.segment_name ?? '').toLowerCase();
      const def = (row.segment_definition ?? '').toLowerCase();
      return name.includes(q) || def.includes(q);
    });
  }, [rawList, quarterFilter, searchQuery]);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50 p-8">
        <LoadingSpinner label="Loading segments…" size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50 p-8">
        <p className="text-red-600">
          Failed to load segments: {error instanceof Error ? error.message : 'Unknown error'}
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-50 overflow-auto">
      <PageHeader
        title="All Segments"
        description="Campaigns from megacorp_campaigns joined with megacorp_segment_definitions, with individual and household counts."
      />

      <div className="flex-1 overflow-auto p-4">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <div className="flex items-center gap-2">
            <label htmlFor="quarter-filter" className="text-sm font-medium text-gray-700 whitespace-nowrap">
              Quarter
            </label>
            <select
              id="quarter-filter"
              value={quarterFilter}
              onChange={(e) => setQuarterFilter(e.target.value)}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 min-w-[120px]"
            >
              <option value="">All</option>
              {quarters.map((q) => (
                <option key={q} value={q}>
                  {q}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[200px] max-w-md">
            <label htmlFor="segment-search" className="sr-only">
              Search by segment name or definition
            </label>
            <input
              id="segment-search"
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by segment name or definition…"
              className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-500 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          {(quarterFilter || searchQuery.trim()) && (
            <button
              type="button"
              onClick={() => {
                setQuarterFilter('');
                setSearchQuery('');
              }}
              className="text-sm text-gray-600 hover:text-gray-900 underline"
            >
              Clear filters
            </button>
          )}
        </div>
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    {columnLabels.segment_name}
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    {columnLabels.segment_definition}
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    {columnLabels.quarter}
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    {columnLabels.start_date}
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    {columnLabels.end_date}
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider text-right">
                    {householdCountHeader}
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider text-right">
                    {individualCountHeader}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {list.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                      No segments found.
                    </td>
                  </tr>
                ) : (
                  list.map((row) => (
                    <tr key={row.segment_name} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() => setEditRow(row)}
                          className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline text-left"
                        >
                          {row.segment_name}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700 max-w-md align-top">
                        <div className="flex items-start gap-1">
                          <button
                            type="button"
                            onClick={() => toggleDefinition(row.segment_name)}
                            className="shrink-0 self-start mt-0 p-0.5 rounded text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            aria-expanded={expandedDefinitions.has(row.segment_name)}
                            title={expandedDefinitions.has(row.segment_name) ? 'Collapse definition' : 'Expand definition'}
                          >
                            <FontAwesomeIcon
                              icon={faAngleRight}
                              className={`text-xs transition-transform ${expandedDefinitions.has(row.segment_name) ? 'rotate-90' : ''}`}
                              aria-hidden
                            />
                          </button>
                          <span
                            className={`min-w-0 ${expandedDefinitions.has(row.segment_name) ? 'break-all whitespace-pre-wrap' : 'truncate block'}`}
                            title={!expandedDefinitions.has(row.segment_name) ? (row.segment_definition ?? '') : undefined}
                          >
                            {row.segment_definition ?? '—'}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                        {row.quarter ?? '—'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                        {row.start_date != null ? String(row.start_date) : '—'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                        {row.end_date != null ? String(row.end_date) : '—'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-right tabular-nums">
                        {Number(row.household_count ?? 0).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 text-right tabular-nums">
                        {Number(row.individual_count ?? 0).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <EditSegmentDialog
        isOpen={editRow != null}
        onClose={() => setEditRow(null)}
        row={editRow}
      />
    </div>
  );
};

export default AllSegmentsPage;
