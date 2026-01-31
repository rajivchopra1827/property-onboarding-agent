'use client';

import { PropertyWithAllData } from '@/lib/types';

interface ComparisonHeaderProps {
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

export default function ComparisonHeader({ properties }: ComparisonHeaderProps) {
  if (properties.length === 0) return null;

  return (
    <div className="sticky top-0 z-20 bg-white shadow-md border-b border-neutral-200">
      <div className="container mx-auto px-6 py-4">
        <div 
          className="grid gap-4"
          style={{
            gridTemplateColumns: `repeat(${properties.length}, minmax(200px, 280px))`,
          }}
        >
          {properties.map((propData) => {
            const rating = propData.reviewsSummary?.overall_rating || null;
            const displayName = getDisplayName(propData.property);

            return (
              <div
                key={propData.property.id}
                className="flex flex-col items-center text-center"
                role="columnheader"
                aria-label={`Property: ${displayName}`}
              >
                {/* Property Logo/Image placeholder - can be enhanced later */}
                <div className="w-16 h-16 bg-neutral-100 rounded-lg mb-3 flex items-center justify-center">
                  <span className="text-2xl font-bold text-primary-500">
                    {displayName.charAt(0).toUpperCase()}
                  </span>
                </div>

                {/* Property Name */}
                <h3 className="text-lg font-semibold text-neutral-900 mb-2 line-clamp-2">
                  {displayName}
                </h3>

                {/* Rating */}
                <div className="flex items-center gap-2">
                  {rating !== null ? (
                    <>
                      <span className="text-xl font-bold text-neutral-900">
                        {rating.toFixed(1)}
                      </span>
                      <span className="text-lg text-yellow-500">
                        {getStarDisplay(rating)}
                      </span>
                    </>
                  ) : (
                    <span className="text-sm text-neutral-500">No rating</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
