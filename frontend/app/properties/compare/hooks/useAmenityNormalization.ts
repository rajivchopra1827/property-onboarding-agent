'use client';

import { useState, useEffect, useMemo } from 'react';
import { PropertyWithAllData } from '@/lib/types';
import type { NormalizedAmenity, AmenityComparison } from '@/lib/types';

interface NormalizeResponse {
  normalized: Array<{
    raw_name: string;
    normalized_name: string;
    confidence: number | null;
  }>;
  success: boolean;
  error?: string;
}

// Helper to extract amenity name (handles both string and object formats)
function getAmenityName(amenity: string | { name: string; description?: string; category?: string }): string {
  if (typeof amenity === 'string') {
    return amenity;
  }
  return amenity.name || '';
}

/**
 * Hook to normalize amenities for comparison.
 * Fetches raw amenities, calls normalization API, and returns normalized comparison matrix.
 */
export function useAmenityNormalization(properties: PropertyWithAllData[]) {
  const [normalizedMappings, setNormalizedMappings] = useState<Map<string, NormalizedAmenity>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Extract all unique raw amenity names
  const rawAmenities = useMemo(() => {
    const amenities: Array<{ name: string; category: 'building' | 'apartment' }> = [];
    const seen = new Set<string>();

    properties.forEach(prop => {
      if (!prop.amenities?.amenities_data) return;

      // Building amenities
      (prop.amenities.amenities_data.building_amenities || []).forEach(a => {
        const name = getAmenityName(a);
        const key = `building:${name}`;
        if (name && !seen.has(key)) {
          seen.add(key);
          amenities.push({ name, category: 'building' });
        }
      });

      // Apartment amenities
      (prop.amenities.amenities_data.apartment_amenities || []).forEach(a => {
        const name = getAmenityName(a);
        const key = `apartment:${name}`;
        if (name && !seen.has(key)) {
          seen.add(key);
          amenities.push({ name, category: 'apartment' });
        }
      });
    });

    return amenities;
  }, [properties]);

  // Normalize amenities
  useEffect(() => {
    async function normalize() {
      if (rawAmenities.length === 0) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        console.log(`[AmenityNormalization] Normalizing ${rawAmenities.length} amenities...`);

        // Add timeout (30 seconds should be enough even for many amenities)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);

        const response = await fetch('/api/amenities/normalize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ amenities: rawAmenities }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
          throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        const data: NormalizeResponse = await response.json();
        console.log(`[AmenityNormalization] Received ${data.normalized?.length || 0} normalized amenities`);

        if (!response.ok || !data.success) {
          throw new Error(data.error || 'Failed to normalize amenities');
        }

        // Create mapping: "category:raw_name" -> NormalizedAmenity
        const mappings = new Map<string, NormalizedAmenity>();
        data.normalized.forEach(n => {
          // Find the category for this raw name
          const amenity = rawAmenities.find(a => a.name === n.raw_name);
          if (amenity) {
            const mapKey = `${amenity.category}:${n.raw_name}`;
            mappings.set(mapKey, {
              rawName: n.raw_name,
              normalizedName: n.normalized_name,
              confidence: n.confidence
            });
          }
        });

        setNormalizedMappings(mappings);
        console.log(`[AmenityNormalization] Successfully normalized amenities`);
      } catch (err: any) {
        console.error('[AmenityNormalization] Error:', err);
        if (err.name === 'AbortError') {
          setError('Normalization timed out. Please try again or refresh the page.');
        } else {
          setError(err.message || 'Failed to normalize amenities');
        }
        // On error, continue with empty mappings (will use raw names)
        setNormalizedMappings(new Map());
      } finally {
        setLoading(false);
      }
    }

    normalize();
  }, [rawAmenities.join(',')]); // Re-normalize if raw amenities change

  // Get normalized name for a raw amenity
  const getNormalizedName = (rawName: string, category: 'building' | 'apartment'): string => {
    const key = `${category}:${rawName}`;
    const mapping = normalizedMappings.get(key);
    return mapping?.normalizedName || rawName; // Fallback to raw name if not normalized
  };

  return {
    normalizedMappings,
    loading,
    error,
    getNormalizedName
  };
}
