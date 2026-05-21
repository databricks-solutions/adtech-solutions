/**
 * Shared page header with MegaCorp logo (left), title, optional description, and optional right-side content.
 * Logo size is fixed (h-10); whitespace around it is consistent across all pages.
 */

import React from 'react';

const LOGO_SRC = '/MegaCorp_Logo_-_Transparent.png';

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
    <header className="bg-white border-b border-gray-200 px-4 py-3 shrink-0 flex items-center justify-between gap-4">
      <div className="flex items-center gap-4 min-w-0">
        <div className="py-2 pl-1 flex-shrink-0">
          <img
            src={LOGO_SRC}
            alt="MegaCorp"
            className="h-10 w-auto object-contain"
          />
        </div>
        <div className="min-w-0">
          <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
          {description && (
            <p className="text-sm text-gray-500 mt-0.5">{description}</p>
          )}
        </div>
      </div>
      {children != null && <div className="flex-shrink-0">{children}</div>}
    </header>
  );
};

export default PageHeader;
