/**
 * App layout with collapsible left nav and main content area.
 * Uses React Router for deep links and browser back/forward.
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { LeftNav, type NavPage } from './LeftNav';

const PATH_TO_PAGE: Record<string, NavPage> = {
  '/': 'segmentation',
  '/all-segments': 'all-segments',
  '/settings': 'settings',
};

export const AppLayout: React.FC = () => {
  const [navExpanded, setNavExpanded] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const currentPage: NavPage = useMemo(
    () => PATH_TO_PAGE[location.pathname] ?? 'segmentation',
    [location.pathname]
  );

  const handleNavigate = useCallback(
    (next: NavPage) => {
      const path = next === 'segmentation' ? '/' : `/${next}`;
      navigate(path);
    },
    [navigate]
  );

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <LeftNav
        currentPage={currentPage}
        onNavigate={handleNavigate}
        expanded={navExpanded}
        onExpandedChange={setNavExpanded}
      />
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="flex-1 min-h-0 overflow-hidden">
          <Outlet />
        </div>
        <footer className="py-2 text-center text-sm text-gray-500 bg-white border-t border-gray-200 flex items-center justify-center gap-1.5 shrink-0">
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
