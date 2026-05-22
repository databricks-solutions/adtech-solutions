/**
 * API client for app settings (e.g. table configuration).
 */

import apiClient from '@/lib/apiClient';

export interface ProfileColumnConfig {
  features_layout: 'by_column' | 'by_row';
  identity_household_column: string;
  identity_individual_column: string;
}

export interface SegmentListColumnConfig {
  identity_household_column: string;
  identity_individual_column: string;
  segment_name_column: string;
}

export interface ColumnConfigs {
  profile: ProfileColumnConfig;
  segment_list: SegmentListColumnConfig;
  segment_info_labels: Record<string, string>;
}

export interface TablesSettings {
  profiles_table: string;
  campaigns_table: string;
  definitions_table: string;
  column_configs?: ColumnConfigs;
}

const DEFAULT_COLUMN_CONFIGS: ColumnConfigs = {
  profile: {
    features_layout: 'by_column',
    identity_household_column: 'megacorp_hhid',
    identity_individual_column: 'megacorp_indid',
  },
  segment_list: {
    identity_household_column: 'megacorp_hhid',
    identity_individual_column: 'megacorp_indid',
    segment_name_column: 'campaign_name',
  },
  segment_info_labels: {
    segment_name: 'Segment Name',
    segment_definition: 'Segment Definition',
    quarter: 'Quarter',
    start_date: 'Flight Start Date',
    end_date: 'Flight End Date',
    megacorp_indid: 'Individual Identifier',
    megacorp_hhid: 'Household Identifier',
  },
};

export interface GrantsSqlResponse {
  sql: string;
  principal_placeholder: string;
  /** When running in Databricks Apps, the app's identity (DATABRICKS_CLIENT_ID). */
  principal_detected?: string | null;
}

export const settingsApi = {
  async getTables(): Promise<TablesSettings> {
    const response = await apiClient.get<TablesSettings>('/settings/tables');
    const data = response.data;
    if (!data.column_configs) {
      data.column_configs = DEFAULT_COLUMN_CONFIGS;
    }
    return data;
  },

  async putTables(payload: TablesSettings): Promise<TablesSettings> {
    const response = await apiClient.put<TablesSettings>('/settings/tables', payload);
    const data = response.data;
    if (!data.column_configs) {
      data.column_configs = DEFAULT_COLUMN_CONFIGS;
    }
    return data;
  },

  async getGrantsSql(): Promise<GrantsSqlResponse> {
    const response = await apiClient.get<GrantsSqlResponse>('/settings/grants-sql');
    return response.data;
  },
};

export { DEFAULT_COLUMN_CONFIGS };
