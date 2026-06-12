import React from "react";

const LOGO_SRC = "/MegaCorp_Logo_-_Transparent.png";

export interface PageHeaderProps {
  title: string;
  description?: string;
  children?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  children,
}) => {
  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3 shrink-0 flex items-center justify-between gap-4">
      <div className="flex items-center gap-4 min-w-0">
        <div className="py-2 pl-1 flex-shrink-0">
          <img
            src={LOGO_SRC}
            alt="MegaCorp"
            className="h-10 w-auto object-contain"
          />
        </div>
        <div className="min-w-0">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            {title}
          </h1>
          {description && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              {description}
            </p>
          )}
        </div>
      </div>
      {children != null && <div className="flex-shrink-0">{children}</div>}
    </header>
  );
};

export default PageHeader;
