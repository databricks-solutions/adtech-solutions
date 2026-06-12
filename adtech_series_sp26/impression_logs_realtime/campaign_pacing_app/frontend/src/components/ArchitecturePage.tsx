import React from "react";
import { PageHeader } from "./PageHeader";

const WORKSPACE_HOST = "https://e2-demo-field-eng.cloud.databricks.com";

interface Node {
  id: string;
  label: string;
  sub: string;
  description?: string;
  tone: "navy" | "blue" | "lava";
  icon?: string;
  href?: string;
}

const TONE_CLASSES: Record<Node["tone"], string> = {
  navy: "border-databricks-navy-300 bg-databricks-navy-300/20 dark:bg-databricks-navy-800/30 dark:border-databricks-navy-700",
  blue: "border-blue-300 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-800",
  lava: "border-databricks-lava-300 bg-databricks-lava-300/20 dark:bg-databricks-lava-800/30 dark:border-databricks-lava-700",
};

const LinkOutIcon: React.FC = () => (
  <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden>
    <path d="M14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7zM19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7z" />
  </svg>
);

const NodeBox: React.FC<{ n: Node }> = ({ n }) => {
  const inner = (
    <div
      className={`rounded-lg border px-4 py-3 ${TONE_CLASSES[n.tone]} w-full flex items-start gap-3 transition-colors ${
        n.href ? "hover:border-gray-500 dark:hover:border-gray-400 cursor-pointer" : ""
      }`}
    >
      {n.icon && (
        <img
          src={n.icon}
          alt=""
          aria-hidden
          className="h-8 w-8 shrink-0 object-contain mt-0.5"
        />
      )}
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-1.5">
          {n.label}
          {n.href && (
            <span className="text-databricks-lava-600">
              <LinkOutIcon />
            </span>
          )}
        </p>
        <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5 font-mono break-all">
          {n.sub}
        </p>
        {n.description && (
          <p className="text-xs text-gray-700 dark:text-gray-300 mt-2 leading-relaxed">
            {n.description}
          </p>
        )}
      </div>
    </div>
  );
  return n.href ? (
    <a
      href={n.href}
      target="_blank"
      rel="noopener noreferrer"
      className="no-underline block"
    >
      {inner}
    </a>
  ) : (
    inner
  );
};

const ArrowDown: React.FC<{ label?: string }> = ({ label }) => (
  <div className="flex flex-col items-center text-gray-400 dark:text-gray-500 py-1">
    {label && (
      <span className="text-[11px] uppercase tracking-wider mb-0.5">
        {label}
      </span>
    )}
    <svg width="14" height="20" viewBox="0 0 14 20" fill="none" aria-hidden>
      <path
        d="M7 1v14m0 0l-5-5m5 5l5-5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  </div>
);

const ArrowRight: React.FC<{ label?: string }> = ({ label }) => (
  <div className="flex flex-col items-center text-gray-400 dark:text-gray-500 px-2">
    {label && (
      <span className="text-[11px] uppercase tracking-wider mb-0.5 whitespace-nowrap">
        {label}
      </span>
    )}
    <svg width="32" height="14" viewBox="0 0 32 14" fill="none" aria-hidden>
      <path
        d="M1 7h28m0 0l-5-5m5 5l-5 5"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  </div>
);

interface KeyTech {
  label: string;
  desc: string;
  href?: string;
  icon?: string;
}

const KEY_TECH: KeyTech[] = [
  {
    label: "Real-Time Mode (RTM)",
    desc: "Sub-second Structured Streaming trigger for low-latency ingest.",
    href: "https://docs.databricks.com/aws/en/structured-streaming/real-time",
    icon: "/icons/apache-spark.svg",
  },
  {
    label: "jdbcStreaming Sink (Private Preview)",
    desc: "Streaming connector — upserts each microbatch into Lakebase via Postgres ON CONFLICT.",
    icon: "/icons/databricks-symbol.svg",
  },
  {
    label: "Lakebase Provisioned",
    desc: "Managed Postgres for OLTP. OAuth tokens refreshed automatically each hour.",
    href: "https://docs.databricks.com/aws/en/oltp/instances/about",
    icon: "/icons/lakebase.svg",
  },
  {
    label: "Databricks Apps",
    desc: "Serverless host for the FastAPI + React app. Resources declared in the bundle.",
    href: "https://docs.databricks.com/aws/en/dev-tools/databricks-apps/",
    icon: "/icons/apps.svg",
  },
  {
    label: "Unity Catalog",
    desc: "Governs the Delta table that supplies segment definitions.",
    href: "https://docs.databricks.com/aws/en/data-governance/unity-catalog/",
    icon: "/icons/unity-catalog.svg",
  },
  {
    label: "Delta Lake",
    desc: "Source of segment definitions joined to each campaign at read time.",
    href: "https://docs.databricks.com/aws/en/delta/",
    icon: "/icons/delta-lake.svg",
  },
  {
    label: "Kafka source",
    desc: "Built-in Spark Kafka connector for ingestion in batch or streaming.",
    href: "https://docs.databricks.com/aws/en/structured-streaming/kafka",
    icon: "/icons/kafka.svg",
  },
];

export const ArchitecturePage: React.FC = () => {
  return (
    <div className="h-full flex flex-col overflow-hidden">
      <PageHeader
        title="Architecture"
        description="Data flow from impression events to the realtime dashboard."
      />
      <div className="flex-1 overflow-auto bg-white dark:bg-gray-900">
        <div className="p-6 max-w-4xl mx-auto">
          {/* Main vertical flow */}
          <div className="flex flex-col items-center">
            <div className="w-full max-w-md">
              <NodeBox
                n={{
                  id: "producer",
                  label: "kafka_producer_job",
                  sub: "Databricks Job · synthetic events",
                  description:
                    "A Databricks Job that stands in for a live ad server, generating synthetic impressions and publishing them to Kafka so the rest of the pipeline has something realistic to consume.",
                  tone: "navy",
                  icon: "/icons/kafka.svg",
                  href: `${WORKSPACE_HOST}/jobs?searchTerm=kafka_producer_job`,
                }}
              />
            </div>

            <ArrowDown label="produces" />

            <div className="w-full max-w-md">
              <NodeBox
                n={{
                  id: "kafka",
                  label: "Kafka Topic",
                  sub: "tanner_wendland_adtech_impressions_realtime_v3",
                  description:
                    "The message bus where impressions land the instant they're served. In production this is your ad server's existing Kafka topic — nothing about the downstream pipeline changes.",
                  tone: "navy",
                  icon: "/icons/kafka.svg",
                }}
              />
            </div>

            <ArrowDown label="consumes" />

            <div className="w-full max-w-md">
              <NodeBox
                n={{
                  id: "rtm",
                  label: "campaign_pacing_job",
                  sub: "Spark Structured Streaming · RTM · jdbcStreaming sink",
                  description:
                    "A Spark Structured Streaming job running in Real-Time Mode (RTM) that reads each impression from Kafka, aggregates per-campaign delivery and spend on the fly, and upserts the running totals into Lakebase. P99 latency for this kind of stateful aggregation is sub-300ms.",
                  tone: "blue",
                  icon: "/icons/data-streaming.svg",
                  href: `${WORKSPACE_HOST}/jobs?searchTerm=campaign_pacing_job`,
                }}
              />
            </div>

            <ArrowDown label="upserts" />

            <div className="w-full max-w-md">
              <NodeBox
                n={{
                  id: "lakebase",
                  label: "Lakebase (Postgres)",
                  sub: "campaign-pacing · public.campaigns",
                  description:
                    "A serverless managed Postgres database that holds the live pacing state — one row per campaign (Happy Dogs, Terrific Tacos, Best Burgers, Cool Car, Super Savings, Fresh Flowers, Moving Movie) with current impressions, spend, and pacing status. Because it's OLTP, the streaming job can update rows in place every few milliseconds; a Delta table isn't built for that write pattern.",
                  tone: "blue",
                  icon: "/icons/lakebase.svg",
                  href: `${WORKSPACE_HOST}/compute/database-instances/campaign-pacing/databases/databricks_postgres/schemas/public/tables/campaigns`,
                }}
              />
            </div>

            <ArrowDown label="reads" />

            <div className="w-full max-w-3xl">
              <div className="flex items-start gap-3">
                {/* Databricks App container — wraps backend + frontend */}
                <div className="flex-1 min-w-0 rounded-xl border-2 border-dashed border-databricks-lava-300 dark:border-databricks-lava-700 bg-databricks-lava-300/10 dark:bg-databricks-lava-800/10 px-4 pb-4 pt-6 relative">
                  <div className="absolute -top-3 left-4 px-2 bg-white dark:bg-gray-900 flex items-center gap-1.5">
                    <img
                      src="/icons/apps.svg"
                      alt=""
                      aria-hidden
                      className="h-4 w-4"
                    />
                    <span className="text-xs font-semibold text-databricks-lava-700 dark:text-databricks-lava-400 uppercase tracking-wider">
                      Databricks App
                    </span>
                  </div>

                  <NodeBox
                    n={{
                      id: "api",
                      label: "FastAPI Backend",
                      sub: "src/main.py · /api/v1/campaigns",
                      description:
                        "A thin Python API that reads the current pacing row for each campaign out of Lakebase and joins it with the campaign's segment definition before returning it to the dashboard.",
                      tone: "lava",
                    }}
                  />
                  <ArrowDown label="serves" />
                  <NodeBox
                    n={{
                      id: "ui",
                      label: "React dashboard",
                      sub: "Vite SPA · TanStack Query · polls every 2s",
                      description:
                        "The campaign manager's view: a single page that polls the FastAPI backend every 2 seconds and shows each campaign's live impressions, spend-against-budget, and pacing status (Active / Pacing Fast / Stopped).",
                      tone: "lava",
                    }}
                  />
                </div>

                {/* joins arrow — vertically aligned with FastAPI row */}
                <div className="pt-12 shrink-0">
                  <ArrowRight label="joins" />
                </div>

                {/* Delta table — external (UC-governed) */}
                <div className="flex-1 min-w-0 pt-7">
                  <NodeBox
                    n={{
                      id: "delta",
                      label: "Delta table",
                      sub: "media_advertising.segments.megacorp_segment_definitions",
                      description:
                        "The Unity-Catalog–governed source of truth for who each campaign is targeting — e.g. the audience definition for Happy Dogs vs. Terrific Tacos. The backend joins this table at read time so the dashboard can show audience context alongside the live pacing numbers.",
                      tone: "lava",
                      icon: "/icons/delta-lake.svg",
                      href: `${WORKSPACE_HOST}/explore/data/media_advertising/segments/megacorp_segment_definitions`,
                    }}
                  />
                </div>
              </div>
              <p className="text-[11px] text-gray-500 dark:text-gray-500 mt-3 text-center">
                The FastAPI backend reads pacing state from Lakebase and joins
                each campaign with its segment_definition from the
                Unity Catalog–governed Delta table via a SQL warehouse.
              </p>
            </div>
          </div>

          {/* Legend */}
          <div className="mt-10 border-t border-gray-200 dark:border-gray-800 pt-6">
            <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Key technologies
            </h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4 text-sm">
              {KEY_TECH.map((t) => (
                <div key={t.label} className="flex items-start gap-3">
                  {t.icon && (
                    <img
                      src={t.icon}
                      alt=""
                      aria-hidden
                      className="h-6 w-6 shrink-0 object-contain mt-0.5"
                    />
                  )}
                  <div className="min-w-0">
                    <dt className="font-medium text-gray-900 dark:text-gray-100">
                      {t.href ? (
                        <a
                          href={t.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-databricks-lava-600 hover:text-databricks-lava-700 hover:underline"
                        >
                          {t.label}
                        </a>
                      ) : (
                        t.label
                      )}
                    </dt>
                    <dd className="text-gray-600 dark:text-gray-400 mt-0.5">
                      {t.desc}
                    </dd>
                  </div>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArchitecturePage;
