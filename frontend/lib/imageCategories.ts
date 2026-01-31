/**
 * Image category definitions and configuration for property images.
 * 
 * Defines the available categories, their display names, sort order,
 * and optional metadata for UI presentation.
 */

export interface CategoryMetadata {
  id: string;
  displayName: string;
  sortOrder: number;
  description?: string;
  icon?: string;
  color?: string;
}

/**
 * Default category order for sorting images.
 * Lower numbers appear first.
 */
export const CATEGORY_ORDER: Record<string, number> = {
  floor_plans: 1,
  apartment_interior: 2,
  building_amenities: 3,
  apartment_amenities: 4,
  common_areas: 5,
  lifestyle: 6,
  exterior: 7,
  outdoor_spaces: 8,
  // uncategorized is used for display/grouping only, not a selectable tag
  uncategorized: 999,
};

/**
 * Category metadata with display information.
 * Note: 'uncategorized' is not included here as it's not a selectable tag.
 * It's only used for display/grouping purposes when images have no tags.
 */
export const CATEGORY_METADATA: Record<string, CategoryMetadata> = {
  floor_plans: {
    id: 'floor_plans',
    displayName: 'Floor Plans',
    sortOrder: CATEGORY_ORDER.floor_plans,
    description: 'Layout diagrams, unit plans',
  },
  apartment_interior: {
    id: 'apartment_interior',
    displayName: 'Apartment Interior',
    sortOrder: CATEGORY_ORDER.apartment_interior,
    description: 'Living rooms, bedrooms, kitchens, bathrooms',
  },
  building_amenities: {
    id: 'building_amenities',
    displayName: 'Building Amenities',
    sortOrder: CATEGORY_ORDER.building_amenities,
    description: 'Pool, gym, clubhouse, business center, shared facilities',
  },
  apartment_amenities: {
    id: 'apartment_amenities',
    displayName: 'Apartment Amenities',
    sortOrder: CATEGORY_ORDER.apartment_amenities,
    description: 'Appliances, countertops, in-unit features',
  },
  common_areas: {
    id: 'common_areas',
    displayName: 'Common Areas',
    sortOrder: CATEGORY_ORDER.common_areas,
    description: 'Lobbies, hallways, mailrooms',
  },
  lifestyle: {
    id: 'lifestyle',
    displayName: 'Lifestyle',
    sortOrder: CATEGORY_ORDER.lifestyle,
    description: 'People, activities, community events',
  },
  exterior: {
    id: 'exterior',
    displayName: 'Exterior',
    sortOrder: CATEGORY_ORDER.exterior,
    description: 'Building facade, street view, aerial shots',
  },
  outdoor_spaces: {
    id: 'outdoor_spaces',
    displayName: 'Outdoor Spaces',
    sortOrder: CATEGORY_ORDER.outdoor_spaces,
    description: 'Patios, balconies, courtyards, rooftop decks',
  },
};

/**
 * Get the sort order for a category.
 * Returns a high number for unknown categories to sort them last.
 * 'uncategorized' is handled specially for display purposes.
 */
export function getCategorySortOrder(category: string): number {
  if (category === 'uncategorized') {
    return CATEGORY_ORDER.uncategorized;
  }
  return CATEGORY_ORDER[category] ?? 999;
}

/**
 * Get display name for a category.
 * Handles 'uncategorized' as a special case for display purposes.
 */
export function getCategoryDisplayName(category: string): string {
  if (category === 'uncategorized') {
    return 'Uncategorized';
  }
  return CATEGORY_METADATA[category]?.displayName ?? category;
}

/**
 * Get primary tag from an image's tags array.
 * Returns the first tag, or 'uncategorized' if no tags exist.
 * Note: 'uncategorized' is used for display/grouping only, not as an actual tag.
 */
export function getPrimaryTag(imageTags?: string[]): string {
  if (!imageTags || imageTags.length === 0) {
    return 'uncategorized';
  }
  // Filter out invalid/removed categories and return first valid tag
  const validTags = imageTags.filter(tag => isValidCategory(tag));
  if (validTags.length === 0) {
    return 'uncategorized';
  }
  return validTags[0];
}

/**
 * Sort categories by their sort order.
 */
export function sortCategoriesByOrder(categories: string[]): string[] {
  return [...categories].sort((a, b) => {
    const orderA = getCategorySortOrder(a);
    const orderB = getCategorySortOrder(b);
    return orderA - orderB;
  });
}

/**
 * Validate if a tag exists in the available categories.
 */
export function isValidCategory(tag: string): boolean {
  return tag in CATEGORY_METADATA;
}

/**
 * Get list of all available category IDs.
 */
export function getAllCategoryIds(): string[] {
  return Object.keys(CATEGORY_METADATA);
}

/**
 * Reorder tags array to set a specific tag as primary (move to index 0).
 * Keeps all other tags in their relative order.
 * 
 * @param tags - Current tags array
 * @param tagToSetAsPrimary - Tag to move to the front
 * @returns New tags array with the specified tag as primary
 */
export function setTagAsPrimary(tags: string[], tagToSetAsPrimary: string): string[] {
  if (!tags.includes(tagToSetAsPrimary)) {
    return tags;
  }
  
  const filteredTags = tags.filter(tag => tag !== tagToSetAsPrimary);
  return [tagToSetAsPrimary, ...filteredTags];
}

