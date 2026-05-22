import React from "react";
import { PageHeader } from "./PageHeader";
import type { Theme } from "../lib/theme";

const WORKSPACE_HOST = "https://e2-demo-field-eng.cloud.databricks.com";
const LAKEBASE_INSTANCE_NAME = "campaign-pacing";

interface ResourceLink {
  label: string;
  description: string;
  href: string;
  detail?: string;
}

const LAKEBASE_RESOURCES: ResourceLink[] = [
  {
    label: "Lakebase instance",
    description: `PostgreSQL state store — ${LAKEBASE_INSTANCE_NAME}`,
    href: `${WORKSPACE_HOST}/compute/database-instances/${LAKEBASE_INSTANCE_NAME}`,
    detail: "databricks_postgres",
  },
  {
    label: "campaigns table",
    description: "Per-campaign pacing state (impressions, budget, status)",
    href: `${WORKSPACE_HOST}/compute/database-instances/${LAKEBASE_INSTANCE_NAME}/databases/databricks_postgres/schemas/public/tables/campaigns`,
    detail: "databricks_postgres.public.campaigns",
  },
  {
    label: "segment_definitions (Delta / UC)",
    description: "Source of segment_definition text shown on each card",
    href: `${WORKSPACE_HOST}/explore/data/media_advertising/segments/megacorp_segment_definitions`,
    detail: "media_advertising.segments.megacorp_segment_definitions",
  },
];

const PIPELINE_RESOURCES: ResourceLink[] = [
  {
    label: "kafka_producer_job",
    description: "Generates synthetic impression events into Kafka",
    href: `${WORKSPACE_HOST}/jobs?searchTerm=kafka_producer_job`,
    detail: "Topic: tanner_wendland_adtech_impressions_realtime_v3",
  },
  {
    label: "campaign_pacing_job",
    description: "Real-Time Mode stream — Kafka → Lakebase via jdbcStreaming",
    href: `${WORKSPACE_HOST}/jobs?searchTerm=campaign_pacing_job`,
    detail: "Sink: campaign-pacing (Lakebase)",
  },
];

const ExternalLinkIcon = () => (
  <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden>
    <path d="M14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7zM19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7z" />
  </svg>
);

const SunIcon = () => (
  <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden>
    <path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.79 1.42-1.41zM4 10.5H1v2h3v-2zm9-9.95h-2V3.5h2V.55zm7.45 3.91l-1.41-1.41-1.79 1.79 1.41 1.41 1.79-1.79zm-3.21 13.7l1.79 1.8 1.41-1.41-1.8-1.79-1.4 1.4zM20 10.5v2h3v-2h-3zm-8-5c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm-1 16.95h2V19.5h-2v2.95zm-7.45-3.91l1.41 1.41 1.79-1.8-1.41-1.41-1.79 1.8z" />
  </svg>
);

const MoonIcon = () => (
  <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden>
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

const ResourceRow: React.FC<{ r: ResourceLink }> = ({ r }) => (
  <a
    href={r.href}
    target="_blank"
    rel="noopener noreferrer"
    className="flex items-start justify-between gap-4 px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50/50 dark:bg-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-colors no-underline"
  >
    <div className="min-w-0">
      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center gap-1.5">
        {r.label}
        <span className="text-databricks-lava-600">
          <ExternalLinkIcon />
        </span>
      </p>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
        {r.description}
      </p>
      {r.detail && (
        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1 font-mono">
          {r.detail}
        </p>
      )}
    </div>
  </a>
);

interface SettingsPageProps {
  theme: Theme;
  onToggleTheme: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  theme,
  onToggleTheme,
}) => {
  const isDark = theme === "dark";

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <PageHeader
        title="Settings"
        description="Backing infrastructure and app preferences."
      />
      <div className="flex-1 overflow-auto bg-white dark:bg-gray-900">
        <div className="p-6 max-w-2xl">
          <section className="mb-8">
            <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Appearance
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Switch between light and dark themes. Preference is saved locally.
            </p>
            <div className="flex items-center justify-between px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50/50 dark:bg-gray-800/50">
              <div className="flex items-center gap-2">
                <span className="text-gray-500 dark:text-gray-400">
                  {isDark ? <MoonIcon /> : <SunIcon />}
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {isDark ? "Dark mode" : "Light mode"}
                </span>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={isDark}
                onClick={onToggleTheme}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-databricks-lava-600 ${
                  isDark ? "bg-databricks-lava-600" : "bg-gray-300"
                }`}
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
                    isDark ? "translate-x-5" : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Lakebase &amp; Unity Catalog
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Tables read by this app. OAuth tokens to Lakebase are refreshed
              automatically each hour.
            </p>
            <div className="space-y-2">
              {LAKEBASE_RESOURCES.map((r) => (
                <ResourceRow key={r.label} r={r} />
              ))}
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Pipelines
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Jobs that feed the pacing dashboard. Deploy via{" "}
              <code className="font-mono text-xs bg-gray-100 dark:bg-gray-800 dark:text-gray-200 px-1 py-0.5 rounded">
                bash scripts/deploy.sh deploy
              </code>{" "}
              from the bundle root.
            </p>
            <div className="space-y-2">
              {PIPELINE_RESOURCES.map((r) => (
                <ResourceRow key={r.label} r={r} />
              ))}
            </div>
          </section>

        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
