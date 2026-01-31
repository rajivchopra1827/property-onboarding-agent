'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import type {
  PropertyWithAllData
} from '@/lib/types';

/**
 * Custom hook to fetch all comparison data in parallel
 */
export function useComparisonData(propertyIds: string[]) {
  const [data, setData] = useState<PropertyWithAllData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      if (propertyIds.length === 0) {
        setError('No properties selected');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);

        // Fetch all data in parallel
        const [
          { data: properties, error: propsError },
          { data: floorPlans, error: plansError },
          { data: amenities, error: amenitiesError },
          { data: reviewsSummaries, error: reviewsError },
          { data: specialOffers, error: offersError }
        ] = await Promise.all([
          supabase.from('properties').select('*').in('id', propertyIds),
          supabase.from('property_floor_plans').select('*').in('property_id', propertyIds),
          supabase.from('property_amenities').select('*').in('property_id', propertyIds),
          supabase.from('property_reviews_summary').select('*').in('property_id', propertyIds),
          supabase.from('property_special_offers').select('*').in('property_id', propertyIds)
        ]);

        if (propsError) throw propsError;

        // Group data by property_id
        const propertyDataMap = new Map<string, PropertyWithAllData>();

        (properties || []).forEach(property => {
          propertyDataMap.set(property.id, {
            property,
            floorPlans: [],
            amenities: null,
            reviewsSummary: null,
            specialOffers: []
          });
        });

        // Group floor plans
        (floorPlans || []).forEach(plan => {
          const propData = propertyDataMap.get(plan.property_id);
          if (propData) {
            propData.floorPlans.push(plan);
          }
        });

        // Attach amenities
        (amenities || []).forEach(amenity => {
          const propData = propertyDataMap.get(amenity.property_id);
          if (propData) {
            propData.amenities = amenity;
          }
        });

        // Attach reviews summaries
        (reviewsSummaries || []).forEach(review => {
          const propData = propertyDataMap.get(review.property_id);
          if (propData) {
            propData.reviewsSummary = review;
          }
        });

        // Group special offers
        (specialOffers || []).forEach(offer => {
          const propData = propertyDataMap.get(offer.property_id);
          if (propData) {
            propData.specialOffers.push(offer);
          }
        });

        // Convert map to array, preserving order of propertyIds
        const orderedData = propertyIds
          .map(id => propertyDataMap.get(id))
          .filter(d => d !== undefined) as PropertyWithAllData[];

        setData(orderedData);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching comparison data:', err);
        setError(err.message || 'Failed to load comparison data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [propertyIds.join(',')]); // Only re-fetch if IDs change

  return { data, loading, error };
}
