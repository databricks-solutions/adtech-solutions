import React from "react";

export type NavPage = "monitoring" | "architecture" | "settings";

export interface LeftNavProps {
  currentPage: NavPage;
  onNavigate: (page: NavPage) => void;
  expanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
}

const ChevronLeft = () => (
  <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
    <path d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6z" />
  </svg>
);

const ChevronRight = () => (
  <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
    <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z" />
  </svg>
);

const PulseIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
);

const ArchitectureIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1" />
    <rect x="14" y="3" width="7" height="7" rx="1" />
    <rect x="3" y="14" width="7" height="7" rx="1" />
    <rect x="14" y="14" width="7" height="7" rx="1" />
    <path d="M10 6.5h4M10 17.5h4M6.5 10v4M17.5 10v4" />
  </svg>
);

const GearIcon = () => (
  <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
    <path d="M19.14 12.94a7.014 7.014 0 0 0 0-1.88l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.61-.22l-2.39.96a6.998 6.998 0 0 0-1.62-.94l-.36-2.54a.488.488 0 0 0-.5-.42h-3.84a.488.488 0 0 0-.5.42l-.36 2.54c-.59.24-1.13.55-1.62.94l-2.39-.96a.5.5 0 0 0-.61.22L2.65 8.84a.5.5 0 0 0 .12.64l2.03 1.58c-.05.31-.07.62-.07.94 0 .32.02.63.07.94l-2.03 1.58a.5.5 0 0 0-.12.64l1.92 3.32c.14.24.42.34.66.22l2.39-.96c.49.39 1.03.7 1.62.94l.36 2.54c.05.24.27.42.5.42h3.84c.24 0 .45-.18.5-.42l.36-2.54c.59-.24 1.13-.55 1.62-.94l2.39.96c.24.1.52 0 .66-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58zM12 15.5A3.5 3.5 0 1 1 12 8.5a3.5 3.5 0 0 1 0 7z" />
  </svg>
);

const NAV_ITEMS: { id: NavPage; label: string; icon: React.FC }[] = [
  { id: "monitoring", label: "Realtime Monitoring", icon: PulseIcon },
  { id: "architecture", label: "Architecture", icon: ArchitectureIcon },
];

export const LeftNav: React.FC<LeftNavProps> = ({
  currentPage,
  onNavigate,
  expanded,
  onExpandedChange,
}) => {
  return (
    <nav
      className={`flex flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-[width] duration-200 ease-out shrink-0 ${
        expanded ? "w-48" : "w-14"
      }`}
      onMouseEnter={() => onExpandedChange(true)}
      onMouseLeave={() => onExpandedChange(false)}
    >
      <div
        className={`h-12 flex items-center border-b border-gray-200 dark:border-gray-800 cursor-pointer text-gray-600 dark:text-gray-400 ${
          expanded ? "px-3" : "justify-center"
        }`}
        onClick={() => onExpandedChange(!expanded)}
        role="button"
        aria-label={expanded ? "Collapse sidebar" : "Expand sidebar"}
      >
        <span className="text-lg leading-none select-none w-5 flex items-center justify-center shrink-0">
          {expanded ? <ChevronLeft /> : <ChevronRight />}
        </span>
        {expanded && (
          <span className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
            Menu
          </span>
        )}
      </div>

      <ul className="py-2 flex flex-col gap-0.5 flex-1 min-h-0">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <li key={id}>
            <button
              type="button"
              onClick={() => onNavigate(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 text-left text-sm transition-colors ${
                expanded ? "min-w-0" : "justify-center"
              } ${
                currentPage === id
                  ? "bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
              }`}
            >
              <span
                className={`shrink-0 w-5 flex items-center justify-center ${
                  currentPage === id
                    ? "text-gray-700 dark:text-gray-200"
                    : "text-gray-500 dark:text-gray-500"
                }`}
                aria-hidden
              >
                <Icon />
              </span>
              {expanded && <span className="truncate">{label}</span>}
            </button>
          </li>
        ))}
      </ul>

      <div className="border-t border-gray-200 dark:border-gray-800 h-14 flex items-stretch">
        <button
          type="button"
          onClick={() => onNavigate("settings")}
          className={`w-full flex items-center gap-3 px-3 text-left text-sm transition-colors ${
            expanded ? "min-w-0" : "justify-center"
          } ${
            currentPage === "settings"
              ? "bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100"
              : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
          }`}
        >
          <span
            className={`shrink-0 w-5 flex items-center justify-center ${
              currentPage === "settings"
                ? "text-gray-700 dark:text-gray-200"
                : "text-gray-500 dark:text-gray-500"
            }`}
            aria-hidden
          >
            <GearIcon />
          </span>
          {expanded && <span className="truncate">Settings</span>}
        </button>
      </div>
    </nav>
  );
};

export default LeftNav;
