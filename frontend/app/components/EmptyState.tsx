import React from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';

interface EmptyStateProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  actionIcon?: React.ReactNode;
  isLoading?: boolean;
  disabled?: boolean;
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  actionIcon,
  isLoading = false,
  disabled = false,
}: EmptyStateProps) {
  return (
    <Card className="shadow-sm bg-muted">
      <CardContent className="p-8 text-center">
        <div className="max-w-md mx-auto">
          <Icon className="w-12 h-12 text-muted-foreground mx-auto mb-4" strokeWidth={1.5} />
          <p className="text-foreground mb-2 font-medium">
            {title}
          </p>
          <p className="text-sm text-muted-foreground mb-6">
            {description}
          </p>
          {actionLabel && onAction && (
            <Button
              onClick={onAction}
              disabled={disabled || isLoading}
              size="sm"
              className="w-[240px]"
            >
              {actionIcon}
              {actionLabel}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
