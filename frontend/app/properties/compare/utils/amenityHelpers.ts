import type { PropertyAmenities, AmenityComparison, NormalizedAmenity } from '@/lib/types';

// Helper to extract amenity name (handles both string and object formats)
export function getAmenityName(amenity: string | { name: string; description?: string; category?: string }): string {
  if (typeof amenity === 'string') {
    return amenity;
  }
  return amenity.name || '';
}

/**
 * Get normalized name for a raw amenity name
 */
function getNormalizedName(
  rawName: string,
  category: 'building' | 'apartment',
  normalizedMappings: Map<string, NormalizedAmenity>
): string {
  const key = `${category}:${rawName}`;
  const mapping = normalizedMappings.get(key);
  return mapping?.normalizedName || rawName; // Fallback to raw name if not normalized
}

/**
 * Create normalized amenity comparison matrix from multiple properties.
 * Groups variations together (e.g., "gym", "fitness center", "24-Hour Fitness Center" → "Fitness Center").
 * Users see ONLY normalized names; raw names are preserved but hidden.
 */
export function createAmenityMatrix(
  propertyData: Array<{ propertyId: string; amenities: PropertyAmenities | null }>,
  normalizedMappings: Map<string, NormalizedAmenity> = new Map()
): AmenityComparison[] {
  // Map: normalized_name -> Set of raw names that map to it
  const normalizedBuildingMap = new Map<string, Set<string>>();
  const normalizedApartmentMap = new Map<string, Set<string>>();

  // Map: normalized_name -> category
  const normalizedCategoryMap = new Map<string, 'building' | 'apartment'>();

  // Collect all amenities and normalize them
  propertyData.forEach(({ amenities }) => {
    if (!amenities?.amenities_data) return;

    // Building amenities
    (amenities.amenities_data.building_amenities || []).forEach(a => {
      const rawName = getAmenityName(a);
      if (!rawName) return;

      const normalizedName = getNormalizedName(rawName, 'building', normalizedMappings);
      normalizedCategoryMap.set(normalizedName, 'building');

      if (!normalizedBuildingMap.has(normalizedName)) {
        normalizedBuildingMap.set(normalizedName, new Set());
      }
      normalizedBuildingMap.get(normalizedName)!.add(rawName);
    });

    // Apartment amenities
    (amenities.amenities_data.apartment_amenities || []).forEach(a => {
      const rawName = getAmenityName(a);
      if (!rawName) return;

      const normalizedName = getNormalizedName(rawName, 'apartment', normalizedMappings);
      normalizedCategoryMap.set(normalizedName, 'apartment');

      if (!normalizedApartmentMap.has(normalizedName)) {
        normalizedApartmentMap.set(normalizedName, new Set());
      }
      normalizedApartmentMap.get(normalizedName)!.add(rawName);
    });
  });

  // Create comparison objects for building amenities (using normalized names)
  const buildingComparisons: AmenityComparison[] = Array.from(normalizedBuildingMap.keys())
    .sort()
    .map(normalizedName => {
      const availability = new Map<string, boolean | null>();
      const rawNames = Array.from(normalizedBuildingMap.get(normalizedName)!);

      propertyData.forEach(({ propertyId, amenities }) => {
        if (!amenities?.amenities_data) {
          availability.set(propertyId, null);
          return;
        }

        // Check if property has any of the raw names that map to this normalized name
        const buildingAmenities = (amenities.amenities_data.building_amenities || [])
          .map(a => getAmenityName(a));
        
        // Property has this normalized amenity if it has ANY of the raw variations
        const hasAmenity = rawNames.some(rawName => buildingAmenities.includes(rawName));
        availability.set(propertyId, hasAmenity);
      });

      return {
        name: normalizedName, // Normalized name (ONLY this is shown to users)
        rawNames, // All raw names that map to this (stored but hidden from UI)
        category: 'building',
        availability
      };
    });

  // Create comparison objects for apartment amenities (using normalized names)
  const apartmentComparisons: AmenityComparison[] = Array.from(normalizedApartmentMap.keys())
    .sort()
    .map(normalizedName => {
      const availability = new Map<string, boolean | null>();
      const rawNames = Array.from(normalizedApartmentMap.get(normalizedName)!);

      propertyData.forEach(({ propertyId, amenities }) => {
        if (!amenities?.amenities_data) {
          availability.set(propertyId, null);
          return;
        }

        // Check if property has any of the raw names that map to this normalized name
        const apartmentAmenities = (amenities.amenities_data.apartment_amenities || [])
          .map(a => getAmenityName(a));
        
        // Property has this normalized amenity if it has ANY of the raw variations
        const hasAmenity = rawNames.some(rawName => apartmentAmenities.includes(rawName));
        availability.set(propertyId, hasAmenity);
      });

      return {
        name: normalizedName, // Normalized name (ONLY this is shown to users)
        rawNames, // All raw names that map to this (stored but hidden from UI)
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

  const buildingCount = (amenities.amenities_data.building_amenities || []).length;
  const apartmentCount = (amenities.amenities_data.apartment_amenities || []).length;

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
