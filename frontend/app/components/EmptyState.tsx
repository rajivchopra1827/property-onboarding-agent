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
    <Card className="shadow-sm bg-gradient-to-br from-primary-50/30 via-background to-secondary-50/30 border-dashed border-2 border-neutral-200">
      <CardContent className="p-8 text-center">
        <div className="max-w-md mx-auto">
          {/* Icon with gradient circle border and float animation */}
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full p-[2px] bg-[image:var(--gradient-primary)]">
              <div className="w-full h-full rounded-full bg-background flex items-center justify-center">
                <Icon className="w-8 h-8 text-primary-500 animate-float" strokeWidth={1.5} />
              </div>
            </div>
            {/* Sparkle particles */}
            <div className="absolute -top-1 -right-1 w-2 h-2 bg-primary-300 rounded-full animate-sparkle" style={{ animationDelay: '0s' }} />
            <div className="absolute -bottom-1 -left-1 w-1.5 h-1.5 bg-secondary-300 rounded-full animate-sparkle" style={{ animationDelay: '0.7s' }} />
            <div className="absolute top-0 -left-2 w-1 h-1 bg-primary-400 rounded-full animate-sparkle" style={{ animationDelay: '1.4s' }} />
          </div>
          <p className="text-foreground mb-2 font-medium font-display">
            {title}
          </p>
          <p className="text-sm text-muted-foreground mb-6">
            {description}
          </p>
          {actionLabel && onAction && (
            <Button
              onClick={onAction}
              disabled={disabled || isLoading}
              variant="gradient"
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
