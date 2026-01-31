'use client';

import { PropertyWithAllData } from '@/lib/types';
import { formatRating, getStarDisplay, formatNumber, getCellHighlight } from '../utils/comparisonHelpers';

interface ReviewsComparisonProps {
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

export default function ReviewsComparison({ properties }: ReviewsComparisonProps) {
  const reviewsSummaries = properties.map(p => p.reviewsSummary);
  const ratings = reviewsSummaries.map(r => r?.overall_rating || null);
  const reviewCounts = reviewsSummaries.map(r => r?.review_count || null);

  // Check if any property has reviews
  const hasReviews = properties.some(p => p.reviewsSummary !== null);

  if (!hasReviews) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="text-xl font-semibold mb-4 text-foreground">Reviews</h2>
        <p className="text-muted-foreground">No reviews data available for comparison</p>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border overflow-x-auto">
      <div className="px-6 py-4 border-b border-border">
        <h2 className="text-xl font-semibold text-foreground">Reviews</h2>
      </div>
      <table className="w-full">
        <thead>
          <tr>
            <th className="text-left px-4 py-3 text-sm font-semibold text-foreground border-b border-border bg-muted">
              Metric
            </th>
            {properties.map((propData) => (
              <th
                key={propData.property.id}
                className="text-center px-4 py-3 text-sm font-semibold text-foreground border-b border-border bg-muted min-w-[200px] max-w-[280px]"
              >
                {getDisplayName(propData.property)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {/* Rating Row */}
          <tr className="border-b border-border">
            <td className="px-4 py-3 text-sm font-medium text-foreground bg-card">
              Overall Rating
            </td>
            {properties.map((propData, index) => {
              const rating = propData.reviewsSummary?.overall_rating || null;
              const highlight = getCellHighlight(rating, ratings, true);
              const isBest = highlight === 'best';

              return (
                <td
                  key={propData.property.id}
                  className={`
                    px-4 py-3 text-sm text-center
                    ${isBest ? 'bg-success-light dark:bg-success/20 text-success-dark dark:text-success font-semibold' : 'bg-card text-foreground'}
                    transition-colors duration-200
                  `}
                >
                  <div className="flex flex-col items-center gap-1">
                    {rating !== null ? (
                      <>
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-bold">{formatRating(rating)}</span>
                          {isBest && (
                            <span className="text-lg" title="Best rating">👑</span>
                          )}
                        </div>
                        <span className="text-yellow-500 text-sm">{getStarDisplay(rating)}</span>
                      </>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </div>
                </td>
              );
            })}
          </tr>

          {/* Review Count Row */}
          <tr className="border-b border-border">
            <td className="px-4 py-3 text-sm font-medium text-foreground bg-card">
              Review Count
            </td>
            {properties.map((propData) => {
              const count = propData.reviewsSummary?.review_count || null;
              const highlight = getCellHighlight(count, reviewCounts, true);
              const isBest = highlight === 'best';

              return (
                <td
                  key={propData.property.id}
                  className={`
                    px-4 py-3 text-sm text-center
                    ${isBest ? 'bg-success-light dark:bg-success/20 text-success-dark dark:text-success font-semibold' : 'bg-card text-foreground'}
                    transition-colors duration-200
                  `}
                >
                  <div className="flex items-center justify-center gap-2">
                    {formatNumber(count)}
                    {isBest && (
                      <span className="text-lg" title="Most reviews">👑</span>
                    )}
                  </div>
                </td>
              );
            })}
          </tr>

          {/* Sentiment Summary Row */}
          <tr>
            <td className="px-4 py-3 text-sm font-medium text-foreground bg-card align-top">
              Sentiment Summary
            </td>
            {properties.map((propData) => {
              const sentiment = propData.reviewsSummary?.sentiment_summary || null;
              const googleMapsUrl = propData.reviewsSummary?.google_maps_url || null;

              return (
                <td
                  key={propData.property.id}
                  className="px-4 py-3 text-sm bg-card align-top"
                >
                  {sentiment ? (
                    <div className="space-y-2">
                      <p className="text-foreground leading-relaxed">{sentiment}</p>
                      {googleMapsUrl && (
                        <a
                          href={googleMapsUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-500 hover:text-primary-600 text-xs underline"
                        >
                          View all reviews →
                        </a>
                      )}
                    </div>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </td>
              );
            })}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
