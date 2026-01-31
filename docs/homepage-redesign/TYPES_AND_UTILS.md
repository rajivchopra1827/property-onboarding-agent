# Homepage Redesign - Types & Utility Functions

This file contains all TypeScript types and utility functions you'll need for the dual-view homepage with intelligence layer.

---

## TypeScript Types

### Enhanced Property Types

**Add to:** `frontend/lib/types.ts`

```typescript
// ============================================================================
// HOMEPAGE INTELLIGENCE TYPES
// ============================================================================

/**
 * Property with calculated health and intelligence data
 */
export interface PropertyWithHealth extends Property {
  // Health status
  healthStatus: HealthStatus;
  daysSinceUpdate: number;
  dataCompleteness: number; // 0-100%

  // Insights and missing data
  insights: Insight[];
  missingData: MissingDataType[];

  // Quick stats (calculated from related data)
  hasFloorPlans: boolean;
  hasReviews: boolean;
  hasAmenities: boolean;
  hasSpecialOffers: boolean;
  hasImages: boolean;
  hasCompetitors: boolean;
  hasBranding: boolean;

  // Display helpers
  imageUrl?: string;
  startingPrice?: number;
  availableUnits?: number;
  rating?: number;
  reviewCount?: number;
}

/**
 * Health status levels
 */
export type HealthStatus = 'stale' | 'partial' | 'complete' | 'new';

/**
 * Types of data that can be missing
 */
export type MissingDataType =
  | 'floor_plans'
  | 'reviews'
  | 'amenities'
  | 'special_offers'
  | 'images'
  | 'competitors'
  | 'branding';

/**
 * Insight/alert shown on property
 */
export interface Insight {
  type: InsightType;
  message: string;
  priority: number; // 1-5, higher = more urgent
  action?: InsightAction;
}

export type InsightType = 'warning' | 'info' | 'error';

export interface InsightAction {
  label: string;
  route: string; // e.g., '/properties/123/extract/floor-plans'
}

/**
 * Filter state
 */
export interface PropertyFilters {
  search: string;
  cities: string[];
  ratingMin: number | null;
  dataHealth: DataHealthFilter;
  hasUnits: boolean | null;
  hasOffers: boolean | null;
}

export type DataHealthFilter = 'all' | 'complete' | 'partial' | 'stale';

/**
 * Sort options
 */
export type PropertySortOption =
  | 'needs-attention'
  | 'recent'
  | 'alphabetical'
  | 'rating'
  | 'price'
  | 'last-updated';

/**
 * Categorized properties
 */
export interface CategorizedProperties {
  needsAttention: PropertyWithHealth[];
  partial: PropertyWithHealth[];
  upToDate: PropertyWithHealth[];
  recentlyAdded: PropertyWithHealth[];
}
```

---

## Utility Functions

### 1. Health Calculation

**Create:** `frontend/app/utils/propertyHealth.ts`

```typescript
import type {
  Property,
  PropertyWithHealth,
  HealthStatus,
  Insight,
  MissingDataType
} from '@/lib/types';

/**
 * Calculate days since last update
 */
export function calculateDaysSinceUpdate(updatedAt: string): number {
  const now = new Date();
  const updated = new Date(updatedAt);
  const diffTime = Math.abs(now.getTime() - updated.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
}

/**
 * Determine health status based on data age and completeness
 */
export function calculateHealthStatus(
  property: Property,
  daysSinceUpdate: number,
  dataCompleteness: number
): HealthStatus {
  // Check if recently added (within 7 days)
  const createdAt = new Date(property.created_at);
  const daysSinceCreation = calculateDaysSinceUpdate(property.created_at);

  if (daysSinceCreation <= 7) {
    return 'new';
  }

  // Check if stale (>30 days old)
  if (daysSinceUpdate > 30) {
    return 'stale';
  }

  // Check completeness
  if (dataCompleteness < 70) {
    return 'partial';
  }

  return 'complete';
}

/**
 * Calculate data completeness percentage
 */
export function calculateDataCompleteness(
  hasFloorPlans: boolean,
  hasReviews: boolean,
  hasAmenities: boolean,
  hasSpecialOffers: boolean,
  hasImages: boolean,
  hasCompetitors: boolean,
  hasBranding: boolean
): number {
  const fields = [
    hasFloorPlans,
    hasReviews,
    hasAmenities,
    hasSpecialOffers,
    hasImages,
    hasCompetitors,
    hasBranding
  ];

  const completedFields = fields.filter(Boolean).length;
  return Math.round((completedFields / fields.length) * 100);
}

/**
 * Generate insights based on property health
 */
export function generateInsights(
  property: Property,
  daysSinceUpdate: number,
  missingData: MissingDataType[]
): Insight[] {
  const insights: Insight[] = [];

  // Stale data warning
  if (daysSinceUpdate > 30) {
    insights.push({
      type: 'warning',
      message: `Data not updated in ${daysSinceUpdate} days`,
      priority: 5,
      action: {
        label: 'Refresh Data',
        route: `/properties/${property.id}/refresh`
      }
    });
  }

  // Missing data alerts (prioritized)
  const missingDataPriority: Record<MissingDataType, number> = {
    floor_plans: 4,
    reviews: 4,
    amenities: 3,
    images: 3,
    special_offers: 2,
    competitors: 2,
    branding: 1
  };

  missingData.forEach(dataType => {
    const labels: Record<MissingDataType, string> = {
      floor_plans: 'floor plan data',
      reviews: 'reviews data',
      amenities: 'amenities data',
      images: 'property images',
      special_offers: 'special offers',
      competitors: 'competitor data',
      branding: 'brand identity data'
    };

    insights.push({
      type: 'info',
      message: `Missing ${labels[dataType]}`,
      priority: missingDataPriority[dataType],
      action: {
        label: `Extract ${labels[dataType]}`,
        route: `/properties/${property.id}/extract/${dataType}`
      }
    });
  });

  // Sort by priority (highest first)
  return insights.sort((a, b) => b.priority - a.priority);
}

/**
 * Enhance property with health and intelligence data
 */
export function enhancePropertyWithHealth(
  property: Property,
  relatedData: {
    floorPlansCount: number;
    reviewsCount: number;
    amenitiesCount: number;
    specialOffersCount: number;
    imagesCount: number;
    competitorsCount: number;
    hasBranding: boolean;
    reviewsSummary?: { overall_rating?: number; review_count?: number };
    imageUrl?: string;
    startingPrice?: number;
    availableUnits?: number;
  }
): PropertyWithHealth {
  const daysSinceUpdate = calculateDaysSinceUpdate(property.updated_at);

  // Check what data exists
  const hasFloorPlans = relatedData.floorPlansCount > 0;
  const hasReviews = relatedData.reviewsCount > 0;
  const hasAmenities = relatedData.amenitiesCount > 0;
  const hasSpecialOffers = relatedData.specialOffersCount > 0;
  const hasImages = relatedData.imagesCount > 0;
  const hasCompetitors = relatedData.competitorsCount > 0;
  const hasBranding = relatedData.hasBranding;

  // Calculate completeness
  const dataCompleteness = calculateDataCompleteness(
    hasFloorPlans,
    hasReviews,
    hasAmenities,
    hasSpecialOffers,
    hasImages,
    hasCompetitors,
    hasBranding
  );

  // Determine health status
  const healthStatus = calculateHealthStatus(
    property,
    daysSinceUpdate,
    dataCompleteness
  );

  // Identify missing data
  const missingData: MissingDataType[] = [];
  if (!hasFloorPlans) missingData.push('floor_plans');
  if (!hasReviews) missingData.push('reviews');
  if (!hasAmenities) missingData.push('amenities');
  if (!hasSpecialOffers) missingData.push('special_offers');
  if (!hasImages) missingData.push('images');
  if (!hasCompetitors) missingData.push('competitors');
  if (!hasBranding) missingData.push('branding');

  // Generate insights
  const insights = generateInsights(property, daysSinceUpdate, missingData);

  return {
    ...property,
    healthStatus,
    daysSinceUpdate,
    dataCompleteness,
    insights,
    missingData,
    hasFloorPlans,
    hasReviews,
    hasAmenities,
    hasSpecialOffers,
    hasImages,
    hasCompetitors,
    hasBranding,
    imageUrl: relatedData.imageUrl,
    startingPrice: relatedData.startingPrice,
    availableUnits: relatedData.availableUnits,
    rating: relatedData.reviewsSummary?.overall_rating,
    reviewCount: relatedData.reviewsSummary?.review_count
  };
}
```

---

### 2. Categorization Logic

**Create:** `frontend/app/utils/propertyCategorization.ts`

```typescript
import type {
  PropertyWithHealth,
  CategorizedProperties,
  PropertyFilters,
  PropertySortOption
} from '@/lib/types';

/**
 * Categorize properties by health status
 */
export function categorizeProperties(
  properties: PropertyWithHealth[]
): CategorizedProperties {
  return {
    needsAttention: properties.filter(p => p.healthStatus === 'stale'),
    partial: properties.filter(p => p.healthStatus === 'partial'),
    upToDate: properties.filter(p => p.healthStatus === 'complete'),
    recentlyAdded: properties.filter(p => p.healthStatus === 'new')
  };
}

/**
 * Filter properties based on criteria
 */
export function filterProperties(
  properties: PropertyWithHealth[],
  filters: PropertyFilters
): PropertyWithHealth[] {
  let filtered = [...properties];

  // Search filter
  if (filters.search) {
    const searchLower = filters.search.toLowerCase();
    filtered = filtered.filter(p =>
      p.property_name?.toLowerCase().includes(searchLower) ||
      p.website_url?.toLowerCase().includes(searchLower)
    );
  }

  // City filter
  if (filters.cities.length > 0) {
    filtered = filtered.filter(p =>
      p.city && filters.cities.includes(p.city)
    );
  }

  // Rating filter
  if (filters.ratingMin !== null) {
    filtered = filtered.filter(p =>
      p.rating !== undefined && p.rating >= filters.ratingMin!
    );
  }

  // Data health filter
  if (filters.dataHealth !== 'all') {
    filtered = filtered.filter(p => p.healthStatus === filters.dataHealth);
  }

  // Has units filter
  if (filters.hasUnits !== null) {
    filtered = filtered.filter(p => {
      if (filters.hasUnits) {
        return p.availableUnits !== undefined && p.availableUnits > 0;
      } else {
        return p.availableUnits === undefined || p.availableUnits === 0;
      }
    });
  }

  // Has offers filter
  if (filters.hasOffers !== null) {
    if (filters.hasOffers) {
      filtered = filtered.filter(p => p.hasSpecialOffers);
    } else {
      filtered = filtered.filter(p => !p.hasSpecialOffers);
    }
  }

  return filtered;
}

/**
 * Sort properties
 */
export function sortProperties(
  properties: PropertyWithHealth[],
  sortBy: PropertySortOption
): PropertyWithHealth[] {
  const sorted = [...properties];

  switch (sortBy) {
    case 'needs-attention':
      // Stale first, then partial, then new, then complete
      return sorted.sort((a, b) => {
        const statusOrder = { stale: 0, partial: 1, new: 2, complete: 3 };
        const orderA = statusOrder[a.healthStatus];
        const orderB = statusOrder[b.healthStatus];
        if (orderA !== orderB) return orderA - orderB;
        // Within same status, sort by days since update (oldest first)
        return b.daysSinceUpdate - a.daysSinceUpdate;
      });

    case 'recent':
      return sorted.sort((a, b) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        return dateB - dateA; // Newest first
      });

    case 'alphabetical':
      return sorted.sort((a, b) => {
        const nameA = a.property_name || a.website_url || '';
        const nameB = b.property_name || b.website_url || '';
        return nameA.localeCompare(nameB);
      });

    case 'rating':
      return sorted.sort((a, b) => {
        const ratingA = a.rating || 0;
        const ratingB = b.rating || 0;
        return ratingB - ratingA; // Highest first
      });

    case 'price':
      return sorted.sort((a, b) => {
        const priceA = a.startingPrice || Infinity;
        const priceB = b.startingPrice || Infinity;
        return priceA - priceB; // Lowest first
      });

    case 'last-updated':
      return sorted.sort((a, b) => {
        const dateA = new Date(a.updated_at).getTime();
        const dateB = new Date(b.updated_at).getTime();
        return dateA - dateB; // Oldest first
      });

    default:
      return sorted;
  }
}
```

---

### 3. Badge & Status Helpers

**Create:** `frontend/app/utils/statusHelpers.ts`

```typescript
import type { HealthStatus } from '@/lib/types';

/**
 * Get badge configuration for health status
 */
export function getHealthBadge(status: HealthStatus) {
  const badges = {
    stale: {
      emoji: '🔴',
      label: 'Stale',
      color: 'text-red-800',
      bg: 'bg-red-100',
      border: 'border-red-500'
    },
    partial: {
      emoji: '🟡',
      label: 'Partial',
      color: 'text-yellow-800',
      bg: 'bg-yellow-100',
      border: 'border-yellow-500'
    },
    complete: {
      emoji: '🟢',
      label: 'Complete',
      color: 'text-green-800',
      bg: 'bg-green-100',
      border: 'border-green-500'
    },
    new: {
      emoji: '🆕',
      label: 'NEW',
      color: 'text-indigo-800',
      bg: 'bg-indigo-100',
      border: 'border-indigo-500'
    }
  };

  return badges[status];
}

/**
 * Get section configuration for category
 */
export function getSectionConfig(category: string) {
  const configs = {
    needsAttention: {
      emoji: '🚨',
      label: 'Needs Attention',
      defaultExpanded: true
    },
    partial: {
      emoji: '🟡',
      label: 'Partial Data',
      defaultExpanded: false
    },
    upToDate: {
      emoji: '🟢',
      label: 'Up to Date',
      defaultExpanded: false
    },
    recentlyAdded: {
      emoji: '🆕',
      label: 'Recently Added',
      defaultExpanded: true
    }
  };

  return configs[category as keyof typeof configs] || {
    emoji: '📋',
    label: 'Properties',
    defaultExpanded: false
  };
}

/**
 * Format days ago text
 */
export function formatDaysAgo(days: number): string {
  if (days === 0) return 'Today';
  if (days === 1) return '1 day ago';
  if (days < 7) return `${days}d ago`;
  if (days < 30) {
    const weeks = Math.floor(days / 7);
    return `${weeks}w ago`;
  }
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

/**
 * Format price for display
 */
export function formatPrice(price: number | null | undefined): string {
  if (!price) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(price);
}

/**
 * Format rating display
 */
export function formatRating(rating: number | null | undefined): string {
  if (!rating) return '—';
  return `⭐ ${rating.toFixed(1)}`;
}
```

---

## Usage Examples

### Example 1: Enhancing Properties with Health Data

```typescript
'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { enhancePropertyWithHealth } from '@/app/utils/propertyHealth';
import type { Property, PropertyWithHealth } from '@/lib/types';

export default function PropertiesPage() {
  const [properties, setProperties] = useState<PropertyWithHealth[]>([]);

  useEffect(() => {
    async function fetchAndEnhanceProperties() {
      // Fetch properties
      const { data: props } = await supabase
        .from('properties')
        .select('*');

      if (!props) return;

      // Enhance each property
      const enhanced = await Promise.all(
        props.map(async (prop) => {
          // Fetch related data counts
          const [floorPlans, reviews, amenities, offers, images, competitors, branding] =
            await Promise.all([
              supabase.from('property_floor_plans').select('*', { count: 'exact', head: true }).eq('property_id', prop.id),
              supabase.from('property_reviews').select('*', { count: 'exact', head: true }).eq('property_id', prop.id),
              supabase.from('property_amenities').select('*').eq('property_id', prop.id).single(),
              supabase.from('property_special_offers').select('*', { count: 'exact', head: true }).eq('property_id', prop.id),
              supabase.from('property_images').select('*', { count: 'exact', head: true }).eq('property_id', prop.id),
              supabase.from('competitors').select('*', { count: 'exact', head: true }).eq('property_id', prop.id),
              supabase.from('property_branding').select('*').eq('property_id', prop.id).single()
            ]);

          return enhancePropertyWithHealth(prop, {
            floorPlansCount: floorPlans.count || 0,
            reviewsCount: reviews.count || 0,
            amenitiesCount: amenities.data ? 1 : 0,
            specialOffersCount: offers.count || 0,
            imagesCount: images.count || 0,
            competitorsCount: competitors.count || 0,
            hasBranding: !!branding.data
          });
        })
      );

      setProperties(enhanced);
    }

    fetchAndEnhanceProperties();
  }, []);

  return <div>{/* Render properties */}</div>;
}
```

### Example 2: Categorizing and Filtering

```typescript
import { categorizeProperties, filterProperties, sortProperties } from '@/app/utils/propertyCategorization';

// In your component
const filtered = filterProperties(properties, filters);
const sorted = sortProperties(filtered, sortBy);
const categorized = categorizeProperties(sorted);

// Render sections
return (
  <div>
    {categorized.needsAttention.length > 0 && (
      <Section title="Needs Attention" properties={categorized.needsAttention} />
    )}
    {categorized.recentlyAdded.length > 0 && (
      <Section title="Recently Added" properties={categorized.recentlyAdded} />
    )}
    {/* etc */}
  </div>
);
```

### Example 3: Displaying Status Badges

```typescript
import { getHealthBadge } from '@/app/utils/statusHelpers';

function PropertyCard({ property }: { property: PropertyWithHealth }) {
  const badge = getHealthBadge(property.healthStatus);

  return (
    <div className="relative">
      <div className={`
        absolute top-4 right-4 px-2 py-1 rounded text-xs font-semibold
        ${badge.bg} ${badge.color} ${badge.border} border
      `}>
        {badge.emoji} {badge.label}
      </div>
      {/* Rest of card */}
    </div>
  );
}
```

---

## Complete!

You now have:
1. ✅ Enhanced property types with health data
2. ✅ Health calculation utilities
3. ✅ Categorization and filtering logic
4. ✅ Badge and status helpers
5. ✅ Formatting functions

Copy these into your project and reference them as you build the homepage redesign!
