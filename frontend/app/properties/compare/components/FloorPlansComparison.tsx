'use client';

import { PropertyWithAllData } from '@/lib/types';
import {
  enhanceFloorPlansWithMetrics,
  formatPrice,
  formatNumber,
  getBedroomLabel,
  getBathroomLabel
} from '../utils/comparisonHelpers';

interface FloorPlansComparisonProps {
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

export default function FloorPlansComparison({ properties }: FloorPlansComparisonProps) {
  // Collect all floor plans for comparison
  const allFloorPlans = properties.flatMap(p => p.floorPlans);

  // Enhance each property's floor plans with metrics
  const enhancedProperties = properties.map(propData => ({
    ...propData,
    enhancedFloorPlans: enhanceFloorPlansWithMetrics(propData.floorPlans, allFloorPlans)
  }));

  // Group by bedroom count
  const bedroomCounts = new Set<number | null>();
  allFloorPlans.forEach(fp => bedroomCounts.add(fp.bedrooms));
  const sortedBedrooms = Array.from(bedroomCounts).sort((a, b) => {
    if (a === null) return 1;
    if (b === null) return -1;
    return a - b;
  });

  // Check if any property has floor plans
  const hasFloorPlans = properties.some(p => p.floorPlans.length > 0);

  if (!hasFloorPlans) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="text-xl font-semibold mb-4 text-foreground">Floor Plans</h2>
        <p className="text-muted-foreground">No floor plans available for comparison</p>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border overflow-x-auto">
      <div className="px-6 py-4 border-b border-border">
        <h2 className="text-xl font-semibold text-foreground">Floor Plans</h2>
      </div>
      <table className="w-full">
        <thead>
          <tr>
            <th className="text-left px-4 py-3 text-sm font-semibold text-foreground border-b border-border bg-muted">
              Floor Plan
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
          {sortedBedrooms.map((bedrooms) => {
            const bedroomLabel = getBedroomLabel(bedrooms);
            const plansForBedroom = enhancedProperties.map(prop => ({
              propertyId: prop.property.id,
              plan: prop.enhancedFloorPlans.find(fp => fp.bedrooms === bedrooms)
            }));

            // Check if any property has a plan for this bedroom count
            const hasAnyPlan = plansForBedroom.some(p => p.plan !== undefined);

            if (!hasAnyPlan) return null;

            return (
              <tr key={bedrooms} className="border-b border-border">
                <td className="px-4 py-3 text-sm font-medium text-foreground bg-card">
                  {bedroomLabel}
                </td>
                {plansForBedroom.map(({ propertyId, plan }) => {
                  if (!plan) {
                    return (
                      <td
                        key={propertyId}
                        className="px-4 py-3 text-sm text-center text-muted-foreground bg-card"
                      >
                        —
                      </td>
                    );
                  }

                  const isBestValue = plan.isBestValue;

                  return (
                    <td
                      key={propertyId}
                      className={`
                        px-4 py-3 text-sm text-center
                        ${isBestValue ? 'bg-success-light dark:bg-success/20 text-success-dark dark:text-success font-semibold' : 'bg-card text-foreground'}
                        transition-colors duration-200
                      `}
                    >
                      <div className="space-y-1">
                        <div className="font-medium">{plan.name}</div>
                        <div className="text-xs">
                          {formatPrice(plan.min_price)}
                          {plan.max_price && plan.max_price !== plan.min_price && (
                            <span> - {formatPrice(plan.max_price)}</span>
                          )}
                        </div>
                        {plan.size_sqft && (
                          <div className="text-xs text-muted-foreground">
                            {formatNumber(plan.size_sqft)} sqft
                          </div>
                        )}
                        {plan.pricePerSqft !== null && (
                          <div className="text-xs font-medium">
                            {formatPrice(plan.pricePerSqft)}/sqft
                            {isBestValue && (
                              <span className="ml-1" title="Best value">👑</span>
                            )}
                          </div>
                        )}
                        {plan.is_available !== null && (
                          <div className="text-xs">
                            {plan.is_available ? (
                              <span className="text-success dark:text-success-dark">Available</span>
                            ) : (
                              <span className="text-muted-foreground">Not Available</span>
                            )}
                          </div>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
