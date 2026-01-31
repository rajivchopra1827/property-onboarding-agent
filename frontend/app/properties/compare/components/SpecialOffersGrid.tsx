'use client';

import { PropertyWithAllData } from '@/lib/types';

interface SpecialOffersGridProps {
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

function formatDate(dateString: string | null): string {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch {
    return dateString;
  }
}

export default function SpecialOffersGrid({ properties }: SpecialOffersGridProps) {
  // Check if any property has special offers
  const hasOffers = properties.some(p => p.specialOffers.length > 0);

  if (!hasOffers) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="text-xl font-semibold mb-4 text-foreground">Special Offers</h2>
        <p className="text-muted-foreground">No special offers available for comparison</p>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border overflow-x-auto">
      <div className="px-6 py-4 border-b border-border">
        <h2 className="text-xl font-semibold text-foreground">Special Offers</h2>
      </div>
      <table className="w-full">
        <thead>
          <tr>
            <th className="text-left px-4 py-3 text-sm font-semibold text-foreground border-b border-border bg-muted">
              Property
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
          <tr>
            <td className="px-4 py-3 text-sm font-medium text-foreground bg-card align-top">
              Offers
            </td>
            {properties.map((propData) => {
              const offers = propData.specialOffers;

              return (
                <td
                  key={propData.property.id}
                  className="px-4 py-3 text-sm bg-card align-top"
                >
                  {offers.length > 0 ? (
                    <div className="space-y-4">
                      {offers.map((offer) => (
                        <div
                          key={offer.id}
                          className="border border-primary-200 dark:border-primary-800 rounded-lg p-3 bg-primary-50 dark:bg-primary-900/20"
                        >
                          <div className="font-semibold text-foreground mb-1">
                            {offer.offer_description}
                          </div>
                          {offer.descriptive_text && (
                            <div className="text-xs text-foreground mb-2">
                              {offer.descriptive_text}
                            </div>
                          )}
                          {offer.valid_until && (
                            <div className="text-xs text-muted-foreground">
                              Valid until: {formatDate(offer.valid_until)}
                            </div>
                          )}
                        </div>
                      ))}
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
