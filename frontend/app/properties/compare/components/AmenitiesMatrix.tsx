'use client';

import { useEffect } from 'react';
import { PropertyWithAllData } from '@/lib/types';
import { createAmenityMatrix, findUniqueAmenities } from '../utils/amenityHelpers';
import { useAmenityNormalization } from '../hooks/useAmenityNormalization';

interface AmenitiesMatrixProps {
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

export default function AmenitiesMatrix({ properties }: AmenitiesMatrixProps) {
  // Normalize amenities
  const { normalizedMappings, loading: normalizing, error: normalizationError } = useAmenityNormalization(properties);

  // Log normalization state for debugging
  useEffect(() => {
    if (normalizing) {
      console.log('[AmenitiesMatrix] Normalizing amenities...');
    } else if (normalizationError) {
      console.warn('[AmenitiesMatrix] Normalization error:', normalizationError);
    } else {
      console.log('[AmenitiesMatrix] Normalization complete, mappings:', normalizedMappings.size);
    }
  }, [normalizing, normalizationError, normalizedMappings.size]);

  // Create amenity comparison matrix with normalized names
  const propertyData = properties.map(p => ({
    propertyId: p.property.id,
    amenities: p.amenities
  }));

  const amenityMatrix = createAmenityMatrix(propertyData, normalizedMappings);

  // Separate building and apartment amenities
  const buildingAmenities = amenityMatrix.filter(a => a.category === 'building');
  const apartmentAmenities = amenityMatrix.filter(a => a.category === 'apartment');

  // Find unique amenities for each property
  const uniqueAmenitiesByProperty = new Map<string, Set<string>>();
  properties.forEach(prop => {
    const unique = findUniqueAmenities(prop.property.id, amenityMatrix);
    uniqueAmenitiesByProperty.set(prop.property.id, new Set(unique));
  });

  const renderAmenityRow = (amenity: typeof amenityMatrix[0], index: number) => {
    const isUniqueForProperty = (propertyId: string) => {
      return uniqueAmenitiesByProperty.get(propertyId)?.has(amenity.name) || false;
    };

    // Use category + name + index for unique key to handle duplicate names across categories
    const uniqueKey = `${amenity.category}-${amenity.name}-${index}`;

    return (
      <tr key={uniqueKey} className="border-b border-neutral-200">
        <td className="px-4 py-3 text-sm text-neutral-700 bg-white">
          {amenity.name}
        </td>
        {properties.map((propData) => {
          const hasAmenity = amenity.availability.get(propData.property.id);
          const isUnique = isUniqueForProperty(propData.property.id);

          let cellContent: React.ReactNode;
          let cellClass = 'px-4 py-3 text-sm text-center bg-white';

          if (hasAmenity === true) {
            cellContent = (
              <span className="text-success-dark font-semibold text-lg">✓</span>
            );
            if (isUnique) {
              cellClass += ' bg-primary-100';
            }
          } else if (hasAmenity === false) {
            cellContent = (
              <span className="text-error-dark text-lg">✗</span>
            );
          } else {
            cellContent = (
              <span className="text-neutral-400">–</span>
            );
            cellClass += ' bg-neutral-50';
          }

          return (
            <td key={propData.property.id} className={cellClass}>
              {cellContent}
            </td>
          );
        })}
      </tr>
    );
  };

  // Show loading state while normalizing
  if (normalizing) {
    return (
      <div className="bg-white rounded-lg border border-neutral-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Amenities</h2>
        <p className="text-neutral-600">Normalizing amenities...</p>
        <p className="text-sm text-neutral-500 mt-2">This may take a few seconds for new amenities</p>
      </div>
    );
  }

  // Show error state if normalization failed (but continue with raw names)
  if (normalizationError) {
    console.warn('[AmenitiesMatrix] Normalization error:', normalizationError);
    // Continue with raw names if normalization fails - don't block the UI
  }

  if (amenityMatrix.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-neutral-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Amenities</h2>
        <p className="text-neutral-600">No amenities data available for comparison</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-neutral-200 overflow-x-auto">
      <div className="px-6 py-4 border-b border-neutral-200">
        <h2 className="text-xl font-semibold text-neutral-900">Amenities</h2>
        <p className="text-sm text-neutral-600 mt-1">
          ✓ = Has amenity, ✗ = Doesn't have, – = Unknown
        </p>
      </div>

      {buildingAmenities.length > 0 && (
        <div className="mb-6">
          <div className="px-6 py-3 bg-neutral-50 border-b border-neutral-200">
            <h3 className="text-lg font-semibold text-neutral-900">Building Amenities</h3>
          </div>
          <table className="w-full">
            <thead>
              <tr>
                <th className="text-left px-4 py-3 text-sm font-semibold text-neutral-700 border-b border-neutral-200 bg-neutral-50">
                  Amenity
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
              {buildingAmenities.map((amenity, index) => renderAmenityRow(amenity, index))}
            </tbody>
          </table>
        </div>
      )}

      {apartmentAmenities.length > 0 && (
        <div>
          <div className="px-6 py-3 bg-neutral-50 border-b border-neutral-200">
            <h3 className="text-lg font-semibold text-neutral-900">Apartment Amenities</h3>
          </div>
          <table className="w-full">
            <thead>
              <tr>
                <th className="text-left px-4 py-3 text-sm font-semibold text-neutral-700 border-b border-neutral-200 bg-neutral-50">
                  Amenity
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
              {apartmentAmenities.map((amenity, index) => renderAmenityRow(amenity, index))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
