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
      <div className="bg-white rounded-lg border border-neutral-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Special Offers</h2>
        <p className="text-neutral-600">No special offers available for comparison</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-neutral-200 overflow-x-auto">
      <div className="px-6 py-4 border-b border-neutral-200">
        <h2 className="text-xl font-semibold text-neutral-900">Special Offers</h2>
      </div>
      <table className="w-full">
        <thead>
          <tr>
            <th className="text-left px-4 py-3 text-sm font-semibold text-neutral-700 border-b border-neutral-200 bg-neutral-50">
              Property
            </th>
            {properties.map((propData) => (
              <th
                key={propData.property.id}
                className="text-center px-4 py-3 text-sm font-semibold text-neutral-700 border-b border-neutral-200 bg-neutral-50 min-w-[200px] max-w-[280px]"
              >
                {getDisplayName(propData.property)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="px-4 py-3 text-sm font-medium text-neutral-700 bg-white align-top">
              Offers
            </td>
            {properties.map((propData) => {
              const offers = propData.specialOffers;

              return (
                <td
                  key={propData.property.id}
                  className="px-4 py-3 text-sm bg-white align-top"
                >
                  {offers.length > 0 ? (
                    <div className="space-y-4">
                      {offers.map((offer) => (
                        <div
                          key={offer.id}
                          className="border border-primary-200 rounded-lg p-3 bg-primary-50"
                        >
                          <div className="font-semibold text-neutral-900 mb-1">
                            {offer.offer_description}
                          </div>
                          {offer.descriptive_text && (
                            <div className="text-xs text-neutral-700 mb-2">
                              {offer.descriptive_text}
                            </div>
                          )}
                          {offer.valid_until && (
                            <div className="text-xs text-neutral-600">
                              Valid until: {formatDate(offer.valid_until)}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-neutral-500">—</span>
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
