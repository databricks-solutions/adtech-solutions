import React, { useState } from "react";
import { LeftNav, type NavPage } from "./LeftNav";
import CampaignDashboard from "./CampaignDashboard";
import { SettingsPage } from "./SettingsPage";
import { ArchitecturePage } from "./ArchitecturePage";
import { PageHeader } from "./PageHeader";
import { useTheme } from "../lib/theme";

export const AppLayout: React.FC = () => {
  const [navExpanded, setNavExpanded] = useState(false);
  const [page, setPage] = useState<NavPage>("monitoring");
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
      <LeftNav
        currentPage={page}
        onNavigate={setPage}
        expanded={navExpanded}
        onExpandedChange={setNavExpanded}
      />
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
          {page === "monitoring" && (
            <>
              <PageHeader
                title="Campaign Pacing"
                description="Real-time impression tracking — Spark RTM + Lakebase"
              >
                <span className="flex items-center gap-1.5 text-xs font-medium text-databricks-lava-600">
                  <span className="inline-block h-2 w-2 rounded-full bg-databricks-lava-600 animate-pulse" />
                  Live
                </span>
              </PageHeader>
              <div className="flex-1 overflow-auto">
                <div className="mx-auto max-w-5xl px-6 py-6">
                  <CampaignDashboard
                    onNavigateToArchitecture={() => setPage("architecture")}
                  />
                </div>
              </div>
            </>
          )}
          {page === "architecture" && <ArchitecturePage />}
          {page === "settings" && (
            <SettingsPage theme={theme} onToggleTheme={toggleTheme} />
          )}
        </div>
        <footer className="h-14 text-center text-sm text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 flex items-center justify-center gap-1.5 shrink-0">
          Powered by Databricks
          <img
            src="https://cdn.bfldr.com/9AYANS2F/at/k5sfk4xt8n4xpxpgxxr9rkjh/databricks-symbol-navy-900.svg?auto=webp"
            alt="Databricks"
            className="h-4 w-auto inline-block"
          />
        </footer>
      </main>
    </div>
  );
};

export default AppLayout;
