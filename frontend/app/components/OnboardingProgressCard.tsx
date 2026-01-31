'use client';

import { 
  Building2, 
  Image, 
  Palette, 
  Star, 
  Layout, 
  Tag, 
  MessageSquare, 
  MapPin,
  Sparkles,
  CheckCircle2,
  XCircle,
  Loader2
} from 'lucide-react';
import { Card, CardContent } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { cn } from '@/lib/utils';

interface OnboardingProgressCardProps {
  stepName: string;
  stepDescription: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  error?: string;
  delay?: number;
  onRetry?: () => void;
}

// Icon mapping for each step (matching OnboardingHero)
const STEP_ICONS = {
  property_info: Building2,
  images: Image,
  brand_identity: Palette,
  amenities: Star,
  floor_plans: Layout,
  special_offers: Tag,
  classify_images: Sparkles,
  reviews: MessageSquare,
  competitors: MapPin,
};

const stepDisplayNames: Record<string, string> = {
  property_info: 'Property Information',
  images: 'Images',
  brand_identity: 'Brand Identity',
  amenities: 'Amenities',
  floor_plans: 'Floor Plans',
  special_offers: 'Special Offers',
  classify_images: 'Classify Images',
  reviews: 'Reviews',
  competitors: 'Competitors',
};

const stepDescriptions: Record<string, string> = {
  property_info: 'Crawling website to find all pages and extract content',
  images: 'Collecting images from the website',
  brand_identity: 'Analyzing brand colors, fonts, and design elements',
  amenities: 'Identifying building and apartment amenities',
  floor_plans: 'Extracting floor plan details and pricing',
  special_offers: 'Finding special offers and promotions',
  classify_images: 'Tagging images with AI to categorize them',
  reviews: 'Gathering reviews and ratings',
  competitors: 'Identifying nearby competitor properties',
};

export default function OnboardingProgressCard({
  stepName,
  stepDescription,
  status,
  error,
  delay = 0,
  onRetry,
}: OnboardingProgressCardProps) {
  const displayName = stepDisplayNames[stepName] || stepName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  
  // Special handling for property_info step when in progress
  let description = stepDescriptions[stepName] || stepDescription;
  if (stepName === 'property_info' && status === 'in_progress') {
    description = 'Crawling website to find all pages and extract content';
  } else if (stepName === 'property_info' && status === 'completed') {
    description = 'Extracted property name, address, and contact information';
  }

  const getStepIcon = () => {
    const IconComponent = STEP_ICONS[stepName as keyof typeof STEP_ICONS];
    if (!IconComponent) return null;
    
    return (
      <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center">
        <IconComponent 
          className={cn(
            'w-5 h-5',
            status === 'completed' && 'text-success',
            status === 'error' && 'text-error',
            status === 'in_progress' && 'text-primary-500',
            status === 'pending' && 'text-muted-foreground'
          )}
          strokeWidth={status === 'in_progress' ? 2.5 : 2}
        />
      </div>
    );
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return (
          <div className="flex-shrink-0 w-5 h-5 rounded-full bg-success flex items-center justify-center shadow-sm">
            <CheckCircle2 className="w-3 h-3 text-white" />
          </div>
        );
      case 'in_progress':
        return (
          <div className="flex-shrink-0 w-5 h-5 rounded-full border-2 border-primary-500 border-t-transparent animate-spin shadow-sm bg-background" />
        );
      case 'error':
        return (
          <div className="flex-shrink-0 w-5 h-5 rounded-full bg-error flex items-center justify-center shadow-sm">
            <XCircle className="w-3 h-3 text-white" />
          </div>
        );
      default:
        return (
          <div className="flex-shrink-0 w-5 h-5 rounded-full border-2 border-border bg-background shadow-sm" />
        );
    }
  };

  const getCardVariant = () => {
    switch (status) {
      case 'completed':
        return 'border-success border-2';
      case 'in_progress':
        return 'border-primary-500 border-2 shadow-lg';
      case 'error':
        return 'border-error border-2';
      default:
        return 'border-border opacity-60';
    }
  };

  return (
    <Card
      className={cn(
        'transition-all duration-500 ease-out p-4',
        status === 'pending' && 'translate-y-2 bg-muted',
        status !== 'pending' && 'opacity-100 translate-y-0',
        getCardVariant()
      )}
      style={{
        animationDelay: `${delay}ms`,
        animation: status !== 'pending' ? 'fadeInUp 0.5s ease-out forwards' : 'none',
      }}
    >
      <CardContent className="p-0">
        <div className="flex items-start gap-3">
          {/* Step Icon with Status Indicator Overlay */}
          <div className="relative flex-shrink-0">
            {getStepIcon()}
            {/* Status Indicator - positioned as overlay */}
            <div className="absolute -bottom-1 -right-1">
              {getStatusIcon()}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className={cn(
                'text-lg font-semibold',
                status === 'completed' && 'text-success dark:text-success-dark',
                status === 'error' && 'text-error dark:text-error-dark',
                status === 'in_progress' && 'text-primary-600 dark:text-primary-400',
                status === 'pending' && 'text-muted-foreground'
              )}>
                {displayName}
              </h3>
              {status === 'completed' && (
                <Badge variant="default" className="bg-success text-white">
                  Complete
                </Badge>
              )}
              {status === 'in_progress' && (
                <Badge variant="default" className="bg-primary-500 text-white">
                  In Progress
                </Badge>
              )}
              {status === 'error' && (
                <Badge variant="destructive">
                  Error
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground mb-2">
              {description}
            </p>
            {error && (
              <div className="mt-2">
                <p className="text-sm text-error dark:text-error-dark mb-2">
                  {error}
                </p>
                {onRetry && (
                  <Button
                    onClick={onRetry}
                    variant="outline"
                    size="sm"
                    className="border-error-dark text-error-dark hover:bg-error/10"
                  >
                    Retry
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

