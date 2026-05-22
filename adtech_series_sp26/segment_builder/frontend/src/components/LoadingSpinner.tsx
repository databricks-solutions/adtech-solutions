/**
 * Shared loading spinner for consistent loading UX across the app.
 */

import React from 'react';

interface LoadingSpinnerProps {
  /** Optional label shown next to the spinner */
  label?: string;
  /** Size: 'sm' | 'md' | 'lg' */
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label,
  size = 'md',
  className = '',
}) => {
  return (
    <div
      className={`flex items-center justify-center gap-2 ${className}`}
      role="status"
      aria-label={label ?? 'Loading'}
    >
      <svg
        className={`animate-spin text-blue-500 ${sizeClasses[size]}`}
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      {label && (
        <span className="text-sm text-gray-500">{label}</span>
      )}
    </div>
  );
};

export default LoadingSpinner;
