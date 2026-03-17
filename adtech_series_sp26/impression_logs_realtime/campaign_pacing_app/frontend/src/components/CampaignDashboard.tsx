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
}

async function fetchCampaigns(): Promise<Campaign[]> {
  const res = await fetch("/api/v1/campaigns");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Color helpers
// ---------------------------------------------------------------------------

function barColor(pacing_pct: number, status: Campaign["status"]): string {
  if (status === "STOPPED") return "bg-gray-600";
  if (pacing_pct >= 80) return "bg-red-500";
  if (pacing_pct >= 50) return "bg-amber-400";
  return "bg-emerald-500";
}

function statusBadge(status: Campaign["status"]) {
  const base = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";
  if (status === "STOPPED")
    return <span className={`${base} bg-gray-700 text-gray-400`}>STOPPED</span>;
  if (status === "PACING_FAST")
    return <span className={`${base} bg-red-900/60 text-red-300`}>PACING FAST</span>;
  return <span className={`${base} bg-emerald-900/60 text-emerald-300`}>ACTIVE</span>;
}

function fmt(n: number) {
  return n.toLocaleString();
}

function fmtDollars(n: number) {
  return `$${n.toFixed(2)}`;
}

// ---------------------------------------------------------------------------
// Card
// ---------------------------------------------------------------------------

function CampaignCard({ c }: { c: Campaign }) {
  const pct = Math.min(c.pacing_pct, 100);
  const updatedAgo =
    c.last_updated
      ? formatDistanceToNow(new Date(c.last_updated), { addSuffix: true })
      : "—";

  const stopped = c.status === "STOPPED";

  return (
    <div
      className={`rounded-lg border p-5 transition-all ${
        stopped
          ? "border-gray-700 bg-gray-900/40 opacity-60"
          : "border-gray-700 bg-gray-900"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <p className="font-medium text-sm leading-snug">{c.campaign_name}</p>
          <p className="text-xs text-gray-500 mt-0.5">Updated {updatedAgo}</p>
        </div>
        {statusBadge(c.status)}
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Pacing</span>
          <span className="font-mono">{c.pacing_pct.toFixed(1)}%</span>
        </div>
        <div className="h-2 rounded-full bg-gray-800 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColor(c.pacing_pct, c.status)}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div className="text-gray-400">
          Impressions
          <span className="ml-1.5 font-mono text-gray-200">
            {fmt(c.impression_count)}
            <span className="text-gray-500"> / {fmt(c.budget_imps)}</span>
          </span>
        </div>
        <div className="text-gray-400">
          Spend
          <span className="ml-1.5 font-mono text-gray-200">
            {fmtDollars(c.spend_dollars)}
            <span className="text-gray-500"> / {fmtDollars(c.budget_dollars)}</span>
          </span>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export default function CampaignDashboard() {
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
          <div key={i} className="h-32 rounded-lg bg-gray-800 animate-pulse" />
        ))}
      </div>
    );
  }

  if (isError || !campaigns) {
    return (
      <p className="text-red-400 text-sm">
        Failed to load campaign data — is the API reachable?
      </p>
    );
  }

  const active = campaigns.filter((c) => c.status !== "STOPPED").length;
  const stopped = campaigns.filter((c) => c.status === "STOPPED").length;

  // Already sorted by pacing_pct desc from API, but sort here too for safety
  const sorted = [...campaigns].sort((a, b) => b.pacing_pct - a.pacing_pct);

  return (
    <div>
      {/* Summary bar */}
      <div className="flex items-center gap-4 mb-6 text-sm">
        <span className="text-emerald-400 font-medium">{active} Active</span>
        <span className="text-gray-600">·</span>
        <span className="text-gray-400">{stopped} Stopped</span>
        <span className="ml-auto flex items-center gap-4">
          <button
            onClick={handleReset}
            disabled={resetting}
            className="px-3 py-1 rounded text-xs font-medium bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors disabled:opacity-50"
          >
            {resetting ? "Resetting..." : "Reset Pacing"}
          </button>
          <span className="text-xs text-gray-600">Refreshes every 2s</span>
        </span>
      </div>

      {/* Campaign cards */}
      <div className="space-y-3">
        {sorted.map((c) => (
          <CampaignCard key={c.campaign_name} c={c} />
        ))}
      </div>
    </div>
  );
}
