import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { formatDistanceToNow } from "date-fns";

interface Campaign {
  campaign_name: string;
  impression_count: number;
  budget_imps: number;
  budget_dollars: number;
  spend_dollars: number;
  pacing_pct: number;
  status: "ACTIVE" | "PACING_FAST" | "STOPPED";
  last_updated: string | null;
  segment_definition: string | null;
}

async function fetchCampaigns(): Promise<Campaign[]> {
  const res = await fetch("/api/v1/campaigns");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function barColor(pacing_pct: number, status: Campaign["status"]): string {
  if (status === "STOPPED") return "bg-gray-400 dark:bg-gray-600";
  if (pacing_pct >= 80) return "bg-red-500";
  if (pacing_pct >= 50) return "bg-amber-400";
  return "bg-emerald-500";
}

function statusBadge(status: Campaign["status"]) {
  const base =
    "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";
  if (status === "STOPPED")
    return (
      <span
        className={`${base} bg-gray-100 text-gray-600 border border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700`}
      >
        STOPPED
      </span>
    );
  if (status === "PACING_FAST")
    return (
      <span
        className={`${base} bg-red-50 text-red-700 border border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800`}
      >
        PACING FAST
      </span>
    );
  return (
    <span
      className={`${base} bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800`}
    >
      ACTIVE
    </span>
  );
}

function fmt(n: number) {
  return n.toLocaleString();
}

function fmtDollars(n: number) {
  return `$${n.toFixed(2)}`;
}

function CampaignCard({ c }: { c: Campaign }) {
  const pct = Math.min(c.pacing_pct, 100);
  const updatedAgo = c.last_updated
    ? formatDistanceToNow(new Date(c.last_updated), { addSuffix: true })
    : "—";

  const stopped = c.status === "STOPPED";

  return (
    <div
      className={`rounded-lg border p-5 bg-white dark:bg-gray-900 transition-all ${
        stopped
          ? "border-gray-200 dark:border-gray-800 opacity-60"
          : "border-gray-200 hover:border-gray-300 dark:border-gray-800 dark:hover:border-gray-700"
      }`}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <p className="font-medium text-sm leading-snug text-gray-900 dark:text-gray-100">
            {c.campaign_name}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-0.5">
            Updated {updatedAgo}
          </p>
        </div>
        {statusBadge(c.status)}
      </div>

      {c.segment_definition && (
        <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed mb-3 border-l-2 border-gray-200 dark:border-gray-700 pl-3">
          {c.segment_definition}
        </p>
      )}

      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
          <span>Pacing</span>
          <span className="font-mono text-gray-800 dark:text-gray-200">
            {c.pacing_pct.toFixed(1)}%
          </span>
        </div>
        <div className="h-2 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColor(
              c.pacing_pct,
              c.status,
            )}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div className="text-gray-600 dark:text-gray-400">
          Impressions
          <span className="ml-1.5 font-mono text-gray-900 dark:text-gray-100">
            {fmt(c.impression_count)}
            <span className="text-gray-500 dark:text-gray-500">
              {" "}/ {fmt(c.budget_imps)}
            </span>
          </span>
        </div>
        <div className="text-gray-600 dark:text-gray-400">
          Spend
          <span className="ml-1.5 font-mono text-gray-900 dark:text-gray-100">
            {fmtDollars(c.spend_dollars)}
            <span className="text-gray-500 dark:text-gray-500">
              {" "}/ {fmtDollars(c.budget_dollars)}
            </span>
          </span>
        </div>
      </div>
    </div>
  );
}

interface CampaignDashboardProps {
  onNavigateToArchitecture?: () => void;
}

export default function CampaignDashboard({
  onNavigateToArchitecture,
}: CampaignDashboardProps = {}) {
  const queryClient = useQueryClient();
  const [resetting, setResetting] = useState(false);

  const { data: campaigns, isLoading, isError } = useQuery<Campaign[]>({
    queryKey: ["campaigns"],
    queryFn: fetchCampaigns,
    refetchInterval: 2000,
  });

  async function handleReset() {
    setResetting(true);
    try {
      await fetch("/api/v1/campaigns/reset", { method: "POST" });
      queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    } finally {
      setResetting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-32 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (isError || !campaigns) {
    return (
      <p className="text-red-600 dark:text-red-400 text-sm">
        Failed to load campaign data — is the API reachable?
      </p>
    );
  }

  const active = campaigns.filter((c) => c.status !== "STOPPED").length;
  const stopped = campaigns.filter((c) => c.status === "STOPPED").length;
  const sorted = [...campaigns].sort((a, b) => b.pacing_pct - a.pacing_pct);

  return (
    <div>
      <div className="mb-6 rounded-lg border border-blue-300 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-800 p-4 text-sm leading-relaxed text-gray-700 dark:text-gray-300">
        <p>
          <span className="font-medium text-gray-900 dark:text-gray-100">
            Imagine you are a campaign manager
          </span>{" "}
          who cares about whether your live campaigns are burning budget at
          the right rate and staying within their contractual frequency caps.
          This app leverages{" "}
          <span className="font-medium text-gray-900 dark:text-gray-100">
            Lakebase + Spark RTM
          </span>{" "}
          to surface pacing decisions within ~2 seconds of an impression
          being served — fast enough to pause an over-pacing campaign before
          the money is wasted, instead of finding out hours later.
        </p>
        <p className="mt-2">
          To learn more about what's going on under the hood, visit the{" "}
          {onNavigateToArchitecture ? (
            <button
              type="button"
              onClick={onNavigateToArchitecture}
              className="font-medium text-databricks-lava-600 hover:text-databricks-lava-700 hover:underline focus:outline-none focus-visible:underline"
            >
              Architecture page
            </button>
          ) : (
            <span className="font-medium">Architecture page</span>
          )}
          .
        </p>
      </div>

      <div className="flex items-center gap-4 mb-6 text-sm">
        <span className="text-emerald-700 dark:text-emerald-400 font-medium">
          {active} Active
        </span>
        <span className="text-gray-400 dark:text-gray-600">·</span>
        <span className="text-gray-600 dark:text-gray-400">
          {stopped} Stopped
        </span>
        <span className="ml-auto flex items-center gap-4">
          <button
            onClick={handleReset}
            disabled={resetting}
            className="px-3 py-1 rounded text-xs font-medium bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 transition-colors disabled:opacity-50"
          >
            {resetting ? "Resetting..." : "Reset Pacing"}
          </button>
          <span className="text-xs text-gray-500 dark:text-gray-500">
            Refreshes every 2s
          </span>
        </span>
      </div>

      <div className="space-y-3">
        {sorted.map((c) => (
          <CampaignCard key={c.campaign_name} c={c} />
        ))}
      </div>
    </div>
  );
}
