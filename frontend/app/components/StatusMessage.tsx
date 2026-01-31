'use client';

import { useEffect, useState } from 'react';

interface StatusMessageProps {
  type: 'success' | 'error';
  message: string;
  onRetry?: () => void;
  autoDismiss?: boolean;
  dismissDelay?: number;
  onDismiss?: () => void;
}

/**
 * Unified status message component for success and error messages.
 * Auto-dismisses success messages after a delay.
 * Shows retry button for errors.
 */
export default function StatusMessage({
  type,
  message,
  onRetry,
  autoDismiss = true,
  dismissDelay = 5000,
  onDismiss,
}: StatusMessageProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (type === 'success' && autoDismiss) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        if (onDismiss) {
          onDismiss();
        }
      }, dismissDelay);

      return () => clearTimeout(timer);
    }
  }, [type, autoDismiss, dismissDelay, onDismiss]);

  if (!isVisible) {
    return null;
  }

  const isSuccess = type === 'success';
  const bgColor = isSuccess ? 'bg-success-light' : 'bg-error-light';
  const borderColor = isSuccess ? 'border-success' : 'border-error';
  const textColor = isSuccess ? 'text-success-dark' : 'text-error-dark';

  return (
    <div className={`mt-4 p-3 ${bgColor} border ${borderColor} rounded-lg`}>
      <div className="flex items-start justify-between gap-3">
        <p className={`text-sm ${textColor} flex-1`}>
          {isSuccess && '✓ '}
          {!isSuccess && '✗ '}
          {message}
        </p>
        {!isSuccess && onRetry && (
          <button
            onClick={onRetry}
            className="px-3 py-1 text-sm font-semibold text-error-dark border border-error-dark rounded hover:bg-error/20 transition-colors focus:outline-none focus:ring-2 focus:ring-error focus:ring-offset-1"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
