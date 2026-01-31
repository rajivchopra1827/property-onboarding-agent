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
  Sparkles
} from 'lucide-react';

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
          className={`w-5 h-5 ${
            status === 'completed' ? 'text-success' :
            status === 'error' ? 'text-error' :
            status === 'in_progress' ? 'text-primary-500' :
            'text-neutral-400'
          }`}
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
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case 'in_progress':
        return (
          <div className="flex-shrink-0 w-5 h-5 rounded-full border-2 border-primary-500 border-t-transparent animate-spin shadow-sm bg-white" />
        );
      case 'error':
        return (
          <div className="flex-shrink-0 w-5 h-5 rounded-full bg-error flex items-center justify-center shadow-sm">
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="flex-shrink-0 w-5 h-5 rounded-full border-2 border-neutral-300 bg-white shadow-sm" />
        );
    }
  };

  const getCardStyles = () => {
    const baseStyles = 'transition-all duration-500 ease-out';
    
    switch (status) {
      case 'completed':
        return `${baseStyles} opacity-100 translate-y-0 bg-white border-success border-2`;
      case 'in_progress':
        return `${baseStyles} opacity-100 translate-y-0 bg-white border-primary-500 border-2 shadow-lg`;
      case 'error':
        return `${baseStyles} opacity-100 translate-y-0 bg-white border-error border-2`;
      default:
        return `${baseStyles} opacity-60 translate-y-2 bg-neutral-50 border-neutral-200`;
    }
  };

  return (
    <div
      className={`rounded-lg border p-4 ${getCardStyles()}`}
      style={{
        animationDelay: `${delay}ms`,
        animation: status !== 'pending' ? 'fadeInUp 0.5s ease-out forwards' : 'none',
      }}
    >
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
          <h3 className={`text-lg font-semibold mb-1 ${
            status === 'completed' ? 'text-success-dark' :
            status === 'error' ? 'text-error-dark' :
            status === 'in_progress' ? 'text-primary-600' :
            'text-neutral-600'
          }`}>
            {displayName}
          </h3>
          <p className="text-sm text-neutral-600 mb-2">
            {description}
          </p>
          {error && (
            <div className="mt-2">
              <p className="text-sm text-error-dark mb-2">
                {error}
              </p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="px-3 py-1.5 text-sm font-semibold text-error-dark border border-error-dark rounded hover:bg-error/10 transition-colors focus:outline-none focus:ring-2 focus:ring-error focus:ring-offset-1"
                >
                  Retry
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

