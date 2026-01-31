# Comparison Dashboard - Types & Utility Functions

This file contains all TypeScript types and utility functions you'll need for the comparison feature.

---

## TypeScript Types

### Core Comparison Types

**Add to:** `frontend/lib/types.ts`

```typescript
// ============================================================================
// COMPARISON FEATURE TYPES
// ============================================================================

/**
 * Complete comparison data structure containing all related data for properties
 */
export interface ComparisonData {
  properties: Property[];
  floorPlans: Map<string, PropertyFloorPlan[]>;
  amenities: Map<string, PropertyAmenities | null>;
  reviewsSummaries: Map<string, PropertyReviewsSummary | null>;
  specialOffers: Map<string, PropertySpecialOffer[]>;
}

/**
 * Property with all related data loaded
 */
export interface PropertyWithAllData {
  property: Property;
  floorPlans: PropertyFloorPlan[];
  amenities: PropertyAmenities | null;
  reviewsSummary: PropertyReviewsSummary | null;
  specialOffers: PropertySpecialOffer[];
}

/**
 * Floor plan with calculated metrics
 */
export interface FloorPlanWithMetrics extends PropertyFloorPlan {
  pricePerSqft: number | null;
  effectiveRent: number | null; // After special offers
  isBestPrice: boolean;
  isBestValue: boolean; // Best price/sqft ratio
}

/**
 * Quick metrics for comparison grid
 */
export interface QuickMetrics {
  propertyId: string;
  propertyName: string;
  overallRating: number | null;
  reviewCount: number | null;
  reviewConfidence: number | null; // rating * log(reviewCount)
  studioPrice: number | null;
  oneBrPrice: number | null;
  twoBrPrice: number | null;
  threeBrPrice: number | null;
  startingPrice: number | null; // Lowest available price
  amenityCount: number;
}

/**
 * Amenity for comparison matrix
 */
export interface AmenityComparison {
  name: string;
  category: 'building' | 'apartment';
  availability: Map<string, boolean | null>; // propertyId -> has amenity
}

/**
 * Comparison highlight types
 */
export type HighlightType = 'best' | 'worst' | 'unique' | 'missing' | 'neutral';

/**
 * Cell highlight information
 */
export interface CellHighlight {
  type: HighlightType;
  reason?: string; // e.g., "Lowest price", "Highest rating"
}
```

---

## Utility Functions

### 1. Comparison Helpers

**Create:** `frontend/app/properties/compare/utils/comparisonHelpers.ts`

```typescript
import { PropertyFloorPlan, PropertyReviewsSummary } from '@/lib/types';
import type { QuickMetrics, FloorPlanWithMetrics, HighlightType } from '@/lib/types';

/**
 * Calculate price per square foot
 */
export function calculatePricePerSqft(
  price: number | null,
  sqft: number | null
): number | null {
  if (!price || !sqft || sqft === 0) return null;
  return Math.round((price / sqft) * 100) / 100; // Round to 2 decimals
}

/**
 * Calculate review confidence score
 * Higher rating + more reviews = higher confidence
 */
export function calculateReviewConfidence(
  rating: number | null,
  reviewCount: number | null
): number | null {
  if (!rating || !reviewCount || reviewCount === 0) return null;
  return Math.round(rating * Math.log10(reviewCount) * 100) / 100;
}

/**
 * Calculate effective rent after special offers
 */
export function calculateEffectiveRent(
  baseRent: number | null,
  monthsFreeConcession: number = 0,
  leaseTerm: number = 12
): number | null {
  if (!baseRent) return null;
  if (monthsFreeConcession === 0) return baseRent;

  const totalRent = baseRent * leaseTerm;
  const discount = baseRent * monthsFreeConcession;
  const effectiveMonthly = (totalRent - discount) / leaseTerm;

  return Math.round(effectiveMonthly * 100) / 100;
}

/**
 * Enhance floor plans with calculated metrics
 */
export function enhanceFloorPlansWithMetrics(
  floorPlans: PropertyFloorPlan[],
  allFloorPlans: PropertyFloorPlan[] // All floor plans across all properties for comparison
): FloorPlanWithMetrics[] {
  return floorPlans.map(fp => {
    const pricePerSqft = calculatePricePerSqft(fp.min_price, fp.size_sqft);

    // Find if this is the best price in its category (by bedroom count)
    const sameBedroom = allFloorPlans.filter(f => f.bedrooms === fp.bedrooms);
    const isBestPrice = fp.min_price !== null &&
      fp.min_price === Math.min(...sameBedroom.map(f => f.min_price || Infinity));

    // Find if this is the best value (price/sqft) in its category
    const validPricePerSqft = sameBedroom
      .map(f => calculatePricePerSqft(f.min_price, f.size_sqft))
      .filter(p => p !== null) as number[];

    const isBestValue = pricePerSqft !== null &&
      validPricePerSqft.length > 0 &&
      pricePerSqft === Math.min(...validPricePerSqft);

    return {
      ...fp,
      pricePerSqft,
      effectiveRent: fp.min_price, // TODO: Factor in special offers
      isBestPrice,
      isBestValue
    };
  });
}

/**
 * Extract quick metrics from property data
 */
export function extractQuickMetrics(
  propertyId: string,
  propertyName: string,
  reviewsSummary: PropertyReviewsSummary | null,
  floorPlans: PropertyFloorPlan[],
  amenityCount: number
): QuickMetrics {
  // Find prices by bedroom count
  const studioPrice = floorPlans.find(fp => fp.bedrooms === 0)?.min_price || null;
  const oneBrPrice = floorPlans.find(fp => fp.bedrooms === 1)?.min_price || null;
  const twoBrPrice = floorPlans.find(fp => fp.bedrooms === 2)?.min_price || null;
  const threeBrPrice = floorPlans.find(fp => fp.bedrooms === 3)?.min_price || null;

  // Find starting price (lowest available)
  const validPrices = floorPlans
    .map(fp => fp.min_price)
    .filter(p => p !== null) as number[];
  const startingPrice = validPrices.length > 0 ? Math.min(...validPrices) : null;

  return {
    propertyId,
    propertyName,
    overallRating: reviewsSummary?.overall_rating || null,
    reviewCount: reviewsSummary?.review_count || null,
    reviewConfidence: calculateReviewConfidence(
      reviewsSummary?.overall_rating || null,
      reviewsSummary?.review_count || null
    ),
    studioPrice,
    oneBrPrice,
    twoBrPrice,
    threeBrPrice,
    startingPrice,
    amenityCount
  };
}

/**
 * Determine if a value is the best in its row
 */
export function findBestInRow(values: (number | null)[]): number | null {
  const validValues = values.filter(v => v !== null) as number[];
  if (validValues.length === 0) return null;
  return Math.min(...validValues);
}

/**
 * Determine if a value is the worst in its row
 */
export function findWorstInRow(values: (number | null)[]): number | null {
  const validValues = values.filter(v => v !== null) as number[];
  if (validValues.length === 0) return null;
  return Math.max(...validValues);
}

/**
 * Determine if a value should be highlighted (for ratings, higher is better)
 */
export function findBestRating(ratings: (number | null)[]): number | null {
  const validRatings = ratings.filter(r => r !== null) as number[];
  if (validRatings.length === 0) return null;
  return Math.max(...validRatings);
}

/**
 * Get highlight type for a cell value
 */
export function getCellHighlight(
  value: number | null,
  allValues: (number | null)[],
  higherIsBetter: boolean = false
): HighlightType {
  if (value === null) return 'neutral';

  const best = higherIsBetter ? findBestRating(allValues) : findBestInRow(allValues);
  const worst = higherIsBetter ? findBestInRow(allValues) : findWorstInRow(allValues);

  if (best !== null && value === best) return 'best';
  if (worst !== null && value === worst && allValues.length > 2) return 'worst';

  return 'neutral';
}

/**
 * Format price for display
 */
export function formatPrice(price: number | null): string {
  if (price === null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(price);
}

/**
 * Format number with commas
 */
export function formatNumber(num: number | null): string {
  if (num === null) return '—';
  return new Intl.NumberFormat('en-US').format(num);
}

/**
 * Format rating for display
 */
export function formatRating(rating: number | null): string {
  if (rating === null) return '—';
  return rating.toFixed(1);
}

/**
 * Get star display for rating
 */
export function getStarDisplay(rating: number | null): string {
  if (rating === null) return '—';
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;

  let stars = '★'.repeat(fullStars);
  if (hasHalfStar) stars += '½';
  const emptyStars = 5 - Math.ceil(rating);
  stars += '☆'.repeat(Math.max(0, emptyStars));

  return stars;
}

/**
 * Get bedroom label
 */
export function getBedroomLabel(bedrooms: number | null): string {
  if (bedrooms === null) return 'Unknown';
  if (bedrooms === 0) return 'Studio';
  return `${bedrooms}BR`;
}

/**
 * Get bathroom label
 */
export function getBathroomLabel(bathrooms: number | null): string {
  if (bathrooms === null) return '—';
  if (bathrooms % 1 === 0) {
    return `${bathrooms}BA`;
  }
  return `${bathrooms}BA`;
}
```

---

### 2. Data Fetching Hook

**Create:** `frontend/app/properties/compare/hooks/useComparisonData.ts`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import type {
  Property,
  PropertyFloorPlan,
  PropertyAmenities,
  PropertyReviewsSummary,
  PropertySpecialOffer,
  ComparisonData,
  PropertyWithAllData
} from '@/lib/types';

/**
 * Custom hook to fetch all comparison data in parallel
 */
export function useComparisonData(propertyIds: string[]) {
  const [data, setData] = useState<PropertyWithAllData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      if (propertyIds.length === 0) {
        setError('No properties selected');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);

        // Fetch all data in parallel
        const [
          { data: properties, error: propsError },
          { data: floorPlans, error: plansError },
          { data: amenities, error: amenitiesError },
          { data: reviewsSummaries, error: reviewsError },
          { data: specialOffers, error: offersError }
        ] = await Promise.all([
          supabase.from('properties').select('*').in('id', propertyIds),
          supabase.from('property_floor_plans').select('*').in('property_id', propertyIds),
          supabase.from('property_amenities').select('*').in('property_id', propertyIds),
          supabase.from('property_reviews_summary').select('*').in('property_id', propertyIds),
          supabase.from('property_special_offers').select('*').in('property_id', propertyIds)
        ]);

        if (propsError) throw propsError;

        // Group data by property_id
        const propertyDataMap = new Map<string, PropertyWithAllData>();

        (properties || []).forEach(property => {
          propertyDataMap.set(property.id, {
            property,
            floorPlans: [],
            amenities: null,
            reviewsSummary: null,
            specialOffers: []
          });
        });

        // Group floor plans
        (floorPlans || []).forEach(plan => {
          const propData = propertyDataMap.get(plan.property_id);
          if (propData) {
            propData.floorPlans.push(plan);
          }
        });

        // Attach amenities
        (amenities || []).forEach(amenity => {
          const propData = propertyDataMap.get(amenity.property_id);
          if (propData) {
            propData.amenities = amenity;
          }
        });

        // Attach reviews summaries
        (reviewsSummaries || []).forEach(review => {
          const propData = propertyDataMap.get(review.property_id);
          if (propData) {
            propData.reviewsSummary = review;
          }
        });

        // Group special offers
        (specialOffers || []).forEach(offer => {
          const propData = propertyDataMap.get(offer.property_id);
          if (propData) {
            propData.specialOffers.push(offer);
          }
        });

        // Convert map to array, preserving order of propertyIds
        const orderedData = propertyIds
          .map(id => propertyDataMap.get(id))
          .filter(d => d !== undefined) as PropertyWithAllData[];

        setData(orderedData);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching comparison data:', err);
        setError(err.message || 'Failed to load comparison data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [propertyIds.join(',')]); // Only re-fetch if IDs change

  return { data, loading, error };
}
```

---

### 3. Amenity Comparison Helpers

**Create:** `frontend/app/properties/compare/utils/amenityHelpers.ts`

```typescript
import type { PropertyAmenities, AmenityComparison } from '@/lib/types';

/**
 * Create amenity comparison matrix from multiple properties
 */
export function createAmenityMatrix(
  propertyData: Array<{ propertyId: string; amenities: PropertyAmenities | null }>
): AmenityComparison[] {
  const allBuildingAmenities = new Set<string>();
  const allApartmentAmenities = new Set<string>();

  // Collect all unique amenities
  propertyData.forEach(({ amenities }) => {
    if (!amenities?.amenities_data) return;

    (amenities.amenities_data.building_amenities || []).forEach(a =>
      allBuildingAmenities.add(a)
    );
    (amenities.amenities_data.apartment_amenities || []).forEach(a =>
      allApartmentAmenities.add(a)
    );
  });

  // Create comparison objects for building amenities
  const buildingComparisons: AmenityComparison[] = Array.from(allBuildingAmenities)
    .sort()
    .map(name => {
      const availability = new Map<string, boolean | null>();

      propertyData.forEach(({ propertyId, amenities }) => {
        if (!amenities?.amenities_data) {
          availability.set(propertyId, null);
          return;
        }

        const hasAmenity = (amenities.amenities_data.building_amenities || [])
          .includes(name);
        availability.set(propertyId, hasAmenity);
      });

      return {
        name,
        category: 'building',
        availability
      };
    });

  // Create comparison objects for apartment amenities
  const apartmentComparisons: AmenityComparison[] = Array.from(allApartmentAmenities)
    .sort()
    .map(name => {
      const availability = new Map<string, boolean | null>();

      propertyData.forEach(({ propertyId, amenities }) => {
        if (!amenities?.amenities_data) {
          availability.set(propertyId, null);
          return;
        }

        const hasAmenity = (amenities.amenities_data.apartment_amenities || [])
          .includes(name);
        availability.set(propertyId, hasAmenity);
      });

      return {
        name,
        category: 'apartment',
        availability
      };
    });

  return [...buildingComparisons, ...apartmentComparisons];
}

/**
 * Count total amenities for a property
 */
export function countAmenities(amenities: PropertyAmenities | null): number {
  if (!amenities?.amenities_data) return 0;

  const buildingCount = amenities.amenities_data.building_amenities?.length || 0;
  const apartmentCount = amenities.amenities_data.apartment_amenities?.length || 0;

  return buildingCount + apartmentCount;
}

/**
 * Find unique amenities (only one property has it)
 */
export function findUniqueAmenities(
  propertyId: string,
  allComparisons: AmenityComparison[]
): string[] {
  return allComparisons
    .filter(comp => {
      const hasIt = comp.availability.get(propertyId) === true;
      if (!hasIt) return false;

      // Check if any other property has it
      const othersHaveIt = Array.from(comp.availability.entries())
        .some(([id, has]) => id !== propertyId && has === true);

      return !othersHaveIt;
    })
    .map(comp => comp.name);
}
```

---

## CSS Classes for Highlights

Add these to your global CSS or Tailwind config:

```css
/* Comparison highlight classes */
.highlight-best {
  @apply bg-success-light text-success-dark;
}

.highlight-worst {
  @apply bg-error-light text-error-dark;
}

.highlight-unique {
  @apply bg-primary-100 text-primary-600;
}

.highlight-missing {
  @apply bg-neutral-200 text-neutral-500;
}

.highlight-neutral {
  @apply bg-white text-neutral-900;
}

/* Cell border for better grid visibility */
.comparison-cell {
  @apply border-r border-neutral-200 px-4 py-3 text-center;
}

.comparison-cell:last-child {
  @apply border-r-0;
}

/* Sticky header */
.comparison-header-sticky {
  @apply sticky top-0 z-20 bg-white shadow-md;
}
```

---

## Usage Examples

### Example 1: Using the comparison hook

```typescript
'use client';

import { useSearchParams } from 'next/navigation';
import { useComparisonData } from './hooks/useComparisonData';

export default function ComparisonPage() {
  const searchParams = useSearchParams();
  const ids = searchParams.get('ids')?.split(',') || [];

  const { data, loading, error } = useComparisonData(ids);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {data.map(propData => (
        <div key={propData.property.id}>
          <h2>{propData.property.property_name}</h2>
          <p>Floor plans: {propData.floorPlans.length}</p>
        </div>
      ))}
    </div>
  );
}
```

### Example 2: Highlighting best values

```typescript
import { getCellHighlight, formatPrice } from './utils/comparisonHelpers';

// In your component
const prices = properties.map(p => p.startingPrice);
const myPrice = property.startingPrice;
const highlight = getCellHighlight(myPrice, prices, false); // Lower is better

return (
  <td className={highlight === 'best' ? 'highlight-best' : 'highlight-neutral'}>
    {formatPrice(myPrice)}
    {highlight === 'best' && <span className="ml-2">👑</span>}
  </td>
);
```

---

## Complete!

You now have:
1. ✅ All TypeScript types needed
2. ✅ Comparison calculation utilities
3. ✅ Data fetching hook
4. ✅ Amenity comparison helpers
5. ✅ Formatting functions
6. ✅ Highlight detection logic

Copy these into your project and reference them as you build the comparison components!
