/**
 * Settings page.
 */

import React, { useState, useEffect } from 'react';
import {
  settingsApi,
  DEFAULT_COLUMN_CONFIGS,
  type TablesSettings,
  type ColumnConfigs,
  type GrantsSqlResponse,
} from '@/api/settingsApi';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronDown, faChevronRight, faCopy } from '@fortawesome/free-solid-svg-icons';

const DEFAULT_TABLES: TablesSettings = {
  profiles_table: 'media_advertising.profiles.megacorp_audience_census_profile',
  campaigns_table: 'media_advertising.segments.megacorp_campaigns',
  definitions_table: 'media_advertising.segments.megacorp_segment_definitions',
  column_configs: DEFAULT_COLUMN_CONFIGS,
};

/** UI label (fixed) → default table column name (editable). Count columns use identity columns, not derived "count". */
const SEGMENT_INFO_SLOTS: { label: string; defaultColumn: string }[] = [
  { label: 'Segment Name', defaultColumn: 'segment_name' },
  { label: 'Segment Definition', defaultColumn: 'segment_definition' },
  { label: 'Quarter', defaultColumn: 'quarter' },
  { label: 'Flight Start Date', defaultColumn: 'start_date' },
  { label: 'Flight End Date', defaultColumn: 'end_date' },
  { label: 'Individual Identifier', defaultColumn: 'megacorp_indid' },
  { label: 'Household Identifier', defaultColumn: 'megacorp_hhid' },
];

function ensureColumnConfigs(t: TablesSettings): TablesSettings {
  if (t.column_configs) return t;
  return { ...t, column_configs: DEFAULT_COLUMN_CONFIGS };
}

export const SettingsPage: React.FC = () => {
  const [tables, setTables] = useState<TablesSettings>(DEFAULT_TABLES);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [configOpen, setConfigOpen] = useState<{
    profile: boolean;
    segment_list: boolean;
    segment_info: boolean;
    permissions: boolean;
  }>({ profile: false, segment_list: false, segment_info: false, permissions: false });
  const [grantsSql, setGrantsSql] = useState<GrantsSqlResponse | null>(null);
  const [grantsLoading, setGrantsLoading] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    settingsApi
      .getTables()
      .then((data) => {
        if (!cancelled) setTables(ensureColumnConfigs(data));
      })
      .catch(() => {
        if (!cancelled) setTables(DEFAULT_TABLES);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSaveTables = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await settingsApi.putTables(tables);
      setMessage({ type: 'success', text: 'Table settings saved.' });
      setGrantsSql(null);
    } catch {
      setMessage({ type: 'error', text: 'Failed to save table settings.' });
    } finally {
      setSaving(false);
    }
  };

  const togglePermissionsSection = () => {
    const next = !configOpen.permissions;
    setConfigOpen((o) => ({ ...o, permissions: next }));
    if (next && grantsSql === null) {
      setGrantsLoading(true);
      settingsApi
        .getGrantsSql()
        .then(setGrantsSql)
        .catch(() => setGrantsSql({ sql: '-- Failed to load. Save table settings and try again.', principal_placeholder: '<id>' }))
        .finally(() => setGrantsLoading(false));
    }
  };

  const copyGrantsSql = async () => {
    if (!grantsSql?.sql) return;
    setCopyFeedback(null);
    try {
      await navigator.clipboard.writeText(grantsSql.sql);
      setCopyFeedback('Copied!');
      setTimeout(() => setCopyFeedback(null), 2000);
    } catch {
      setCopyFeedback('Copy failed');
    }
  };

  const configs: ColumnConfigs = tables.column_configs ?? DEFAULT_COLUMN_CONFIGS;

  const setProfileConfig = (updates: Partial<ColumnConfigs['profile']>) => {
    setTables((prev) => ({
      ...prev,
      column_configs: {
        ...(prev.column_configs ?? DEFAULT_COLUMN_CONFIGS),
        profile: { ...(prev.column_configs?.profile ?? DEFAULT_COLUMN_CONFIGS.profile), ...updates },
      },
    }));
  };

  const setSegmentListConfig = (updates: Partial<ColumnConfigs['segment_list']>) => {
    setTables((prev) => ({
      ...prev,
      column_configs: {
        ...(prev.column_configs ?? DEFAULT_COLUMN_CONFIGS),
        segment_list: {
          ...(prev.column_configs?.segment_list ?? DEFAULT_COLUMN_CONFIGS.segment_list),
          ...updates,
        },
      },
    }));
  };

  /** Get the table column name that currently maps to this UI label. */
  const getColumnNameForLabel = (label: string, defaultColumn: string): string => {
    const labels = configs.segment_info_labels;
    const entry = Object.entries(labels).find(([, v]) => v === label);
    return entry ? entry[0] : defaultColumn;
  };

  /** Set the table column name for a UI label (user edits the column name, not the label). */
  const setSegmentInfoColumnForLabel = (label: string, newColumnName: string) => {
    setTables((prev) => {
      const labels = prev.column_configs?.segment_info_labels ?? DEFAULT_COLUMN_CONFIGS.segment_info_labels;
      const oldColumn = Object.entries(labels).find(([, v]) => v === label)?.[0];
      const next = { ...labels, [newColumnName]: label };
      if (oldColumn && oldColumn !== newColumnName) delete next[oldColumn];
      return {
        ...prev,
        column_configs: {
          ...(prev.column_configs ?? DEFAULT_COLUMN_CONFIGS),
          segment_info_labels: next,
        },
      };
    });
  };

  return (
    <div className="h-full flex flex-col overflow-auto bg-white">
      <div className="p-6 max-w-2xl">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Settings</h1>
        <p className="text-sm text-gray-500 mb-6">
          Configure your preferences for the audience segmentation app.
        </p>
        <div className="space-y-6">
          <section>
            <h2 className="text-sm font-medium text-gray-700 mb-3">Tables</h2>
            <p className="text-sm text-gray-600 mb-4">
              Unity Catalog table names and column configs. Use fully qualified names
              (catalog.schema.table) for tables.
            </p>
            {loading ? (
              <p className="text-sm text-gray-500">Loading…</p>
            ) : (
              <div className="space-y-5">
                {/* Audience Profile Table */}
                <div className="border border-gray-200 rounded-lg p-3 bg-gray-50/50">
                  <label htmlFor="profiles_table" className="block text-sm font-medium text-gray-700 mb-1">
                    Audience Profile Table
                  </label>
                  <input
                    id="profiles_table"
                    type="text"
                    value={tables.profiles_table}
                    onChange={(e) =>
                      setTables((prev) => ({ ...prev, profiles_table: e.target.value }))
                    }
                    placeholder={DEFAULT_TABLES.profiles_table}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-gray-500 focus:border-gray-500 mb-3"
                  />
                  <div>
                    <button
                      type="button"
                      onClick={() => setConfigOpen((o) => ({ ...o, profile: !o.profile }))}
                      className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                    >
                      <FontAwesomeIcon
                        icon={configOpen.profile ? faChevronDown : faChevronRight}
                        className="w-3.5"
                      />
                      Column Configs
                    </button>
                    {configOpen.profile && (
                      <div className="mt-3 pl-5 space-y-3 border-l-2 border-gray-200">
                        <div>
                          <span className="block text-xs font-medium text-gray-600 mb-1">
                            Features are
                          </span>
                          <div className="flex gap-4">
                            <label className="flex items-center gap-2 text-sm">
                              <input
                                type="radio"
                                name="features_layout"
                                checked={configs.profile.features_layout === 'by_column'}
                                onChange={() => setProfileConfig({ features_layout: 'by_column' })}
                                className="rounded border-gray-300"
                              />
                              By Column
                            </label>
                            <label className="flex items-center gap-2 text-sm">
                              <input
                                type="radio"
                                name="features_layout"
                                checked={configs.profile.features_layout === 'by_row'}
                                onChange={() => setProfileConfig({ features_layout: 'by_row' })}
                                className="rounded border-gray-300"
                              />
                              By Row
                            </label>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label
                              htmlFor="profile_household"
                              className="block text-xs font-medium text-gray-600 mb-1"
                            >
                              Household Identifier
                            </label>
                            <input
                              id="profile_household"
                              type="text"
                              value={configs.profile.identity_household_column}
                              onChange={(e) =>
                                setProfileConfig({ identity_household_column: e.target.value })
                              }
                              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                            />
                          </div>
                          <div>
                            <label
                              htmlFor="profile_individual"
                              className="block text-xs font-medium text-gray-600 mb-1"
                            >
                              Individual Identifier
                            </label>
                            <input
                              id="profile_individual"
                              type="text"
                              value={configs.profile.identity_individual_column}
                              onChange={(e) =>
                                setProfileConfig({ identity_individual_column: e.target.value })
                              }
                              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Audience Segment List Table */}
                <div className="border border-gray-200 rounded-lg p-3 bg-gray-50/50">
                  <label
                    htmlFor="campaigns_table"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Audience Segment List Table
                  </label>
                  <input
                    id="campaigns_table"
                    type="text"
                    value={tables.campaigns_table}
                    onChange={(e) =>
                      setTables((prev) => ({ ...prev, campaigns_table: e.target.value }))
                    }
                    placeholder={DEFAULT_TABLES.campaigns_table}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-gray-500 focus:border-gray-500 mb-3"
                  />
                  <div>
                    <button
                      type="button"
                      onClick={() =>
                        setConfigOpen((o) => ({ ...o, segment_list: !o.segment_list }))
                      }
                      className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                    >
                      <FontAwesomeIcon
                        icon={configOpen.segment_list ? faChevronDown : faChevronRight}
                        className="w-3.5"
                      />
                      Column Configs
                    </button>
                    {configOpen.segment_list && (
                      <div className="mt-3 pl-5 space-y-3 border-l-2 border-gray-200">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label
                              htmlFor="seglist_household"
                              className="block text-xs font-medium text-gray-600 mb-1"
                            >
                              Household Identifier
                            </label>
                            <input
                              id="seglist_household"
                              type="text"
                              value={configs.segment_list.identity_household_column}
                              onChange={(e) =>
                                setSegmentListConfig({
                                  identity_household_column: e.target.value,
                                })
                              }
                              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                            />
                          </div>
                          <div>
                            <label
                              htmlFor="seglist_individual"
                              className="block text-xs font-medium text-gray-600 mb-1"
                            >
                              Individual Identifier
                            </label>
                            <input
                              id="seglist_individual"
                              type="text"
                              value={configs.segment_list.identity_individual_column}
                              onChange={(e) =>
                                setSegmentListConfig({
                                  identity_individual_column: e.target.value,
                                })
                              }
                              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                            />
                          </div>
                        </div>
                        <div>
                          <label
                            htmlFor="seglist_segment_name"
                            className="block text-xs font-medium text-gray-600 mb-1"
                          >
                            Segment Name column
                          </label>
                          <input
                            id="seglist_segment_name"
                            type="text"
                            value={configs.segment_list.segment_name_column}
                            onChange={(e) =>
                              setSegmentListConfig({ segment_name_column: e.target.value })
                            }
                            placeholder="campaign_name"
                            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Audience Segment Info Table */}
                <div className="border border-gray-200 rounded-lg p-3 bg-gray-50/50">
                  <label
                    htmlFor="definitions_table"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Audience Segment Info Table
                  </label>
                  <input
                    id="definitions_table"
                    type="text"
                    value={tables.definitions_table}
                    onChange={(e) =>
                      setTables((prev) => ({ ...prev, definitions_table: e.target.value }))
                    }
                    placeholder={DEFAULT_TABLES.definitions_table}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-gray-500 focus:border-gray-500 mb-3"
                  />
                  <div>
                    <button
                      type="button"
                      onClick={() =>
                        setConfigOpen((o) => ({ ...o, segment_info: !o.segment_info }))
                      }
                      className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                    >
                      <FontAwesomeIcon
                        icon={configOpen.segment_info ? faChevronDown : faChevronRight}
                        className="w-3.5"
                      />
                      Column Configs
                    </button>
                    {configOpen.segment_info && (
                      <div className="mt-3 pl-5 space-y-2 border-l-2 border-gray-200">
                        <p className="text-xs text-gray-600 mb-2">
                          Map UI labels (fixed) to table column names (editable). Column names must match the Audience Segment Info table.
                        </p>
                        {SEGMENT_INFO_SLOTS.map(({ label, defaultColumn }) => (
                          <div key={label} className="flex items-center gap-2">
                            <span className="text-sm text-gray-700 w-40 shrink-0">
                              {label}
                            </span>
                            <input
                              type="text"
                              value={getColumnNameForLabel(label, defaultColumn)}
                              onChange={(e) => setSegmentInfoColumnForLabel(label, e.target.value)}
                              placeholder={defaultColumn}
                              className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm font-mono"
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleSaveTables}
                  disabled={saving}
                  className="px-4 py-2 bg-gray-800 text-white text-sm font-medium rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving…' : 'Save table settings'}
                </button>
                {message && (
                  <p
                    className={
                      message.type === 'success'
                        ? 'text-sm text-green-600'
                        : 'text-sm text-red-600'
                    }
                  >
                    {message.text}
                  </p>
                )}
              </div>
            )}
          </section>

          <section className="border border-gray-200 rounded-lg overflow-hidden">
            <button
              type="button"
              onClick={togglePermissionsSection}
              className="w-full flex items-center justify-between px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <span className="text-sm font-medium text-gray-700">
                Required permissions (Unity Catalog)
              </span>
              <FontAwesomeIcon
                icon={configOpen.permissions ? faChevronDown : faChevronRight}
                className="w-3.5 text-gray-500"
              />
            </button>
            {configOpen.permissions && (
              <div className="p-4 pt-0 space-y-3">
                <p className="text-sm text-gray-600">
                  {grantsSql?.principal_detected
                    ? "This app's identity was detected. Copy the SQL below and run it in a SQL warehouse to grant the required permissions."
                    : "Grant these to your app's service principal so it can read profiles and read/write segments. Copy and run in a SQL warehouse. When running in Databricks Apps, the identity is detected automatically."}
                </p>
                {grantsLoading ? (
                  <p className="text-sm text-gray-500">Loading…</p>
                ) : grantsSql ? (
                  <div className="relative">
                    <pre className="p-4 bg-gray-900 text-gray-100 text-xs rounded-md overflow-x-auto whitespace-pre-wrap font-mono">
                      {grantsSql.sql}
                    </pre>
                    <button
                      type="button"
                      onClick={copyGrantsSql}
                      className="absolute top-2 right-2 flex items-center gap-2 px-2 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded transition-colors"
                    >
                      <FontAwesomeIcon icon={faCopy} className="w-3" />
                      {copyFeedback ?? 'Copy SQL'}
                    </button>
                  </div>
                ) : null}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
