'use client';

import { PropertyWithAllData, QuickMetrics, HighlightType } from '@/lib/types';

interface QuickMetricsTableProps {
  properties: PropertyWithAllData[];
}

function getDisplayName(property: PropertyWithAllData['property']) {
  if (property.property_name) {
    return property.property_name;
  }
  if (property.website_url) {
    try {
      const url = new URL(property.website_url);
      return url.hostname.replace('www.', '');
    } catch {
      return property.website_url;
    }
  }
  return 'Unnamed Property';
}

function calculateReviewConfidence(
  rating: number | null,
  reviewCount: number | null
): number | null {
  if (!rating || !reviewCount || reviewCount === 0) return null;
  return Math.round(rating * Math.log10(reviewCount) * 100) / 100;
}

function extractQuickMetrics(
  propertyData: PropertyWithAllData
): QuickMetrics {
  const property = propertyData.property;
  const reviewsSummary = propertyData.reviewsSummary;
  const floorPlans = propertyData.floorPlans;
  const amenities = propertyData.amenities;

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

  // Count amenities
  const amenityCount = amenities?.amenities_data
    ? (amenities.amenities_data.building_amenities?.length || 0) +
      (amenities.amenities_data.apartment_amenities?.length || 0)
    : 0;

  return {
    propertyId: property.id,
    propertyName: getDisplayName(property),
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

function findBestInRow(values: (number | null)[]): number | null {
  const validValues = values.filter(v => v !== null) as number[];
  if (validValues.length === 0) return null;
  return Math.min(...validValues);
}

function findBestRating(ratings: (number | null)[]): number | null {
  const validRatings = ratings.filter(r => r !== null) as number[];
  if (validRatings.length === 0) return null;
  return Math.max(...validRatings);
}

function getCellHighlight(
  value: number | null,
  allValues: (number | null)[],
  higherIsBetter: boolean = false
): HighlightType {
  if (value === null) return 'neutral';

  const best = higherIsBetter ? findBestRating(allValues) : findBestInRow(allValues);

  if (best !== null && value === best) return 'best';

  return 'neutral';
}

function formatPrice(price: number | null): string {
  if (price === null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(price);
}

function formatNumber(num: number | null): string {
  if (num === null) return '—';
  return new Intl.NumberFormat('en-US').format(num);
}

function formatRating(rating: number | null): string {
  if (rating === null) return '—';
  return rating.toFixed(1);
}

function getStarDisplay(rating: number | null): string {
  if (rating === null) return '—';
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;

  let stars = '★'.repeat(fullStars);
  if (hasHalfStar) stars += '½';
  const emptyStars = 5 - Math.ceil(rating);
  stars += '☆'.repeat(Math.max(0, emptyStars));

  return stars;
}

export default function QuickMetricsTable({ properties }: QuickMetricsTableProps) {
  if (properties.length === 0) return null;

  const metrics = properties.map(extractQuickMetrics);

  // Prepare data for highlighting
  const ratings = metrics.map(m => m.overallRating);
  const reviewCounts = metrics.map(m => m.reviewCount);
  const startingPrices = metrics.map(m => m.startingPrice);
  const oneBrPrices = metrics.map(m => m.oneBrPrice);
  const twoBrPrices = metrics.map(m => m.twoBrPrice);
  const amenityCounts = metrics.map(m => m.amenityCount);

  const rows = [
    {
      label: 'Overall Rating',
      values: ratings,
      formatter: (val: number | null) => (
        <div className="flex items-center gap-2">
          <span>{formatRating(val)}</span>
          {val !== null && (
            <span className="text-yellow-500 text-sm">{getStarDisplay(val)}</span>
          )}
        </div>
      ),
      higherIsBetter: true
    },
    {
      label: 'Review Count',
      values: reviewCounts,
      formatter: (val: number | null) => formatNumber(val),
      higherIsBetter: true
    },
    {
      label: 'Starting Price',
      values: startingPrices,
      formatter: (val: number | null) => formatPrice(val),
      higherIsBetter: false
    },
    {
      label: '1BR Price',
      values: oneBrPrices,
      formatter: (val: number | null) => formatPrice(val),
      higherIsBetter: false
    },
    {
      label: '2BR Price',
      values: twoBrPrices,
      formatter: (val: number | null) => formatPrice(val),
      higherIsBetter: false
    },
    {
      label: 'Amenities',
      values: amenityCounts,
      formatter: (val: number | null) => formatNumber(val),
      higherIsBetter: true
    }
  ];

  return (
    <div className="bg-neutral-100 rounded-lg border border-neutral-200 overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr>
            <th className="text-left px-4 py-3 text-sm font-semibold text-neutral-700 border-b border-neutral-200" scope="col">
              Metric
            </th>
            {metrics.map((metric) => (
              <th
                key={metric.propertyId}
                className="text-center px-4 py-3 text-sm font-semibold text-neutral-700 border-b border-neutral-200 min-w-[200px] max-w-[280px]"
                scope="col"
              >
                {metric.propertyName}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b border-neutral-200 last:border-b-0">
              <th className="px-4 py-3 text-sm font-medium text-neutral-700 bg-white text-left" scope="row">
                {row.label}
              </th>
              {row.values.map((value, colIndex) => {
                const highlight = getCellHighlight(value, row.values, row.higherIsBetter);
                const isBest = highlight === 'best';

                return (
                  <td
                    key={colIndex}
                    className={`
                      px-4 py-3 text-sm text-center
                      ${isBest ? 'bg-success-light text-success-dark font-semibold' : 'bg-white text-neutral-900'}
                      transition-colors duration-200
                    `}
                  >
                    <div className="flex items-center justify-center gap-2">
                      {row.formatter(value)}
                      {isBest && (
                        <span className="text-lg" title="Best value">👑</span>
                      )}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
