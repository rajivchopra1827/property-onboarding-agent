'use client';

import { useState } from 'react';
import { PropertyWithAllData } from '@/lib/types';
import CollapsibleSection from './CollapsibleSection';
import FloorPlansComparison from './FloorPlansComparison';
import AmenitiesMatrix from './AmenitiesMatrix';
import ReviewsComparison from './ReviewsComparison';
import SpecialOffersGrid from './SpecialOffersGrid';
import {
  formatPrice,
  formatNumber,
  formatRating,
  getStarDisplay
} from '../utils/comparisonHelpers';
import { countAmenities } from '../utils/amenityHelpers';

interface MobileCompareViewProps {
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

export default function MobileCompareView({ properties }: MobileCompareViewProps) {
  return (
    <div className="space-y-6 pb-8">
      {properties.map((propData) => {
        const property = propData.property;
        const reviewsSummary = propData.reviewsSummary;
        const floorPlans = propData.floorPlans;
        const amenities = propData.amenities;
        const specialOffers = propData.specialOffers;

        // Calculate starting price
        const validPrices = floorPlans
          .map(fp => fp.min_price)
          .filter(p => p !== null) as number[];
        const startingPrice = validPrices.length > 0 ? Math.min(...validPrices) : null;

        const amenityCount = countAmenities(amenities);

        return (
          <div
            key={property.id}
            className="bg-white rounded-lg border border-neutral-200 shadow-md overflow-hidden"
          >
            {/* Property Header */}
            <div className="px-6 py-4 bg-gradient-to-r from-primary-500 to-secondary-700 text-white">
              <h2 className="text-2xl font-bold mb-2">{getDisplayName(property)}</h2>
              {reviewsSummary?.overall_rating && (
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold">
                    {formatRating(reviewsSummary.overall_rating)}
                  </span>
                  <span className="text-yellow-300">{getStarDisplay(reviewsSummary.overall_rating)}</span>
                  {reviewsSummary.review_count && (
                    <span className="text-sm opacity-90">
                      ({formatNumber(reviewsSummary.review_count)} reviews)
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Quick Metrics */}
            <div className="px-6 py-4 border-b border-neutral-200">
              <div className="grid grid-cols-2 gap-4">
                {startingPrice !== null && (
                  <div>
                    <div className="text-xs text-neutral-600 mb-1">Starting Price</div>
                    <div className="text-lg font-semibold text-neutral-900">
                      {formatPrice(startingPrice)}
                    </div>
                  </div>
                )}
                {amenityCount > 0 && (
                  <div>
                    <div className="text-xs text-neutral-600 mb-1">Amenities</div>
                    <div className="text-lg font-semibold text-neutral-900">
                      {formatNumber(amenityCount)}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Collapsible Sections */}
            <div className="divide-y divide-neutral-200">
              {floorPlans.length > 0 && (
                <CollapsibleSection title="Floor Plans" defaultExpanded={false}>
                  <FloorPlansComparison properties={[propData]} />
                </CollapsibleSection>
              )}

              {amenities && (
                <CollapsibleSection title="Amenities" defaultExpanded={false}>
                  <AmenitiesMatrix properties={[propData]} />
                </CollapsibleSection>
              )}

              {reviewsSummary && (
                <CollapsibleSection title="Reviews" defaultExpanded={false}>
                  <ReviewsComparison properties={[propData]} />
                </CollapsibleSection>
              )}

              {specialOffers.length > 0 && (
                <CollapsibleSection title="Special Offers" defaultExpanded={false}>
                  <SpecialOffersGrid properties={[propData]} />
                </CollapsibleSection>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
