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
