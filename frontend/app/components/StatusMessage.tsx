'use client';

import { useEffect, useState } from 'react';
import { Alert, AlertDescription } from '@/app/components/ui/alert';
import { Button } from '@/app/components/ui/button';
import { CheckCircle2, XCircle } from 'lucide-react';

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
  const Icon = isSuccess ? CheckCircle2 : XCircle;

  return (
    <Alert 
      variant={isSuccess ? 'default' : 'destructive'}
      className={`mt-4 ${isSuccess ? 'bg-success-light text-success-dark' : ''}`}
    >
      <Icon className="size-4" />
      <AlertDescription className="flex items-center justify-between gap-3">
        <span className="flex-1">{message}</span>
        {!isSuccess && onRetry && (
          <Button
            onClick={onRetry}
            variant="outline"
            size="sm"
            className="text-error-dark hover:bg-error/20 shadow-sm"
          >
            Retry
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}
