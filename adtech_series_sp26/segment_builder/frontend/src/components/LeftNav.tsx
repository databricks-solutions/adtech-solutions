/**
 * Collapsible left nav. Narrow strip by default; expands on hover or when open.
 */

import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faChevronLeft,
  faChevronRight,
  faUsersViewfinder,
  faBarsStaggered,
  faPersonWalkingDashedLineArrowRight,
  faGear,
} from '@fortawesome/free-solid-svg-icons';

const ACTIVATION_URL = 'https://ad-tech-audience-activation-2556758628403379.aws.databricksapps.com/';

export type NavPage = 'segmentation' | 'all-segments' | 'settings';

export interface LeftNavProps {
  currentPage: NavPage;
  onNavigate: (page: NavPage) => void;
  expanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
}

const NAV_ITEMS: { id: NavPage; label: string }[] = [
  { id: 'segmentation', label: 'Segmentation' },
  { id: 'all-segments', label: 'All Segments' },
];

export const LeftNav: React.FC<LeftNavProps> = ({
  currentPage,
  onNavigate,
  expanded,
  onExpandedChange,
}) => {
  return (
    <nav
      className={`
        flex flex-col bg-white border-r border-gray-200 transition-[width] duration-200 ease-out shrink-0
        ${expanded ? 'w-48' : 'w-14'}
      `}
      onMouseEnter={() => onExpandedChange(true)}
      onMouseLeave={() => onExpandedChange(false)}
    >
      {/* Toggle / branding strip */}
      <div
        className={`h-12 flex items-center border-b border-gray-200 cursor-pointer text-gray-600 ${expanded ? 'px-3' : 'justify-center'}`}
        onClick={() => onExpandedChange(!expanded)}
        role="button"
        aria-label={expanded ? 'Collapse sidebar' : 'Expand sidebar'}
      >
        <span className="text-lg leading-none select-none w-5 flex items-center justify-center shrink-0">
          <FontAwesomeIcon icon={expanded ? faChevronLeft : faChevronRight} />
        </span>
        {expanded && (
          <span className="ml-2 text-sm font-medium text-gray-700 truncate">
            Menu
          </span>
        )}
      </div>

      <ul className="py-2 flex flex-col gap-0.5 flex-1 min-h-0">
        {NAV_ITEMS.map(({ id, label }) => (
          <li key={id}>
            <button
              type="button"
              onClick={() => onNavigate(id)}
              className={`
                w-full flex items-center gap-3 px-3 py-2.5 text-left text-sm transition-colors
                ${expanded ? 'min-w-0' : 'justify-center'}
                ${currentPage === id
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
              `}
            >
              <span
                className={`shrink-0 w-5 flex items-center justify-center ${currentPage === id ? 'text-gray-700' : 'text-gray-500'}`}
                aria-hidden
              >
                <FontAwesomeIcon
                  icon={id === 'segmentation' ? faUsersViewfinder : faBarsStaggered}
                />
              </span>
              {expanded && <span className="truncate">{label}</span>}
            </button>
          </li>
        ))}
        <li>
          <a
            href={ACTIVATION_URL}
            target="_blank"
            rel="noopener noreferrer"
            className={`
              w-full flex items-center gap-3 px-3 py-2.5 text-left text-sm transition-colors text-gray-600 hover:bg-gray-50 hover:text-gray-900 no-underline
              ${expanded ? 'min-w-0' : 'justify-center'}
            `}
          >
            <span className="shrink-0 w-5 flex items-center justify-center text-gray-500" aria-hidden>
              <FontAwesomeIcon icon={faPersonWalkingDashedLineArrowRight} />
            </span>
            {expanded && <span className="truncate">Activation</span>}
          </a>
        </li>
      </ul>

      {/* Settings at bottom of nav */}
      <div className="border-t border-gray-200 py-2">
        <button
          type="button"
          onClick={() => onNavigate('settings')}
          className={`
            w-full flex items-center gap-3 px-3 py-2.5 text-left text-sm transition-colors
            ${expanded ? 'min-w-0' : 'justify-center'}
            ${currentPage === 'settings'
              ? 'bg-gray-100 text-gray-900'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
          `}
        >
          <span
            className={`shrink-0 w-5 flex items-center justify-center ${currentPage === 'settings' ? 'text-gray-700' : 'text-gray-500'}`}
            aria-hidden
          >
            <FontAwesomeIcon icon={faGear} />
          </span>
          {expanded && <span className="truncate">Settings</span>}
        </button>
      </div>
    </nav>
  );
};

export default LeftNav;
