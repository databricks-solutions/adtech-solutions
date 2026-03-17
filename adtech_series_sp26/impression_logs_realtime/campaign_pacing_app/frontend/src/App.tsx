import CampaignDashboard from "./components/CampaignDashboard";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="mx-auto max-w-5xl flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              Campaign Pacing
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Real-time impression tracking · powered by Spark RTM + Lakebase
            </p>
          </div>
          <span className="flex items-center gap-1.5 text-xs text-emerald-400">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            Live
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        <CampaignDashboard />
      </main>
    </div>
  );
}
