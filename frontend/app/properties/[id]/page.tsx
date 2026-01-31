'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { Building2, Image as ImageIcon, Palette, Star, Layout, Tag, MessageSquare, MapPin, Gift } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import type { RealtimeChannel } from '@supabase/supabase-js';
import { Property, PropertyImage, PropertyBranding, PropertyAmenities, PropertyFloorPlan, PropertySpecialOffer } from '@/lib/types';
import ReviewsSection from '@/app/components/ReviewsSection';
import CompetitorsSection from '@/app/components/CompetitorsSection';
import SocialPostsSection from '@/app/components/SocialPostsSection';
import ImageGallery from '@/app/components/ImageGallery';
import ExtractionLoadingState from '@/app/components/ExtractionLoadingState';
import StatusMessage from '@/app/components/StatusMessage';
import { useExtractionState } from '@/app/hooks/useExtractionState';
import { getPrimaryTag, getCategoryDisplayName, getCategorySortOrder, sortCategoriesByOrder } from '@/lib/imageCategories';

export default function PropertyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const propertyId = params.id as string;

  const [property, setProperty] = useState<Property | null>(null);
  const [images, setImages] = useState<PropertyImage[]>([]);
  const [branding, setBranding] = useState<PropertyBranding | null>(null);
  const [amenities, setAmenities] = useState<PropertyAmenities | null>(null);
  const [floorPlans, setFloorPlans] = useState<PropertyFloorPlan[]>([]);
  const [specialOffers, setSpecialOffers] = useState<PropertySpecialOffer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showHiddenImages, setShowHiddenImages] = useState(false);
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryIndex, setGalleryIndex] = useState(0);
  const [unavailableImageIds, setUnavailableImageIds] = useState<Set<string>>(new Set());

  // Unified extraction state hooks
  const imagesExtraction = useExtractionState({
    extractionType: 'images',
    propertyId,
    apiEndpoint: `/api/properties/${propertyId}/extract/images`,
    onSuccess: () => {
      // Loading will be set to false automatically when images appear via Realtime
    },
  });

  const amenitiesExtraction = useExtractionState({
    extractionType: 'amenities',
    propertyId,
    apiEndpoint: `/api/properties/${propertyId}/extract/amenities`,
    onSuccess: () => {
      // Loading will be set to false automatically when amenities appear via Realtime
    },
  });

  const floorPlansExtraction = useExtractionState({
    extractionType: 'floor plans',
    propertyId,
    apiEndpoint: `/api/properties/${propertyId}/extract/floor-plans`,
    onSuccess: () => {
      // Loading will be set to false automatically when floor plans appear via Realtime
    },
  });

  const brandIdentityExtraction = useExtractionState({
    extractionType: 'brand identity',
    propertyId,
    apiEndpoint: `/api/properties/${propertyId}/extract/brand-identity`,
    onSuccess: () => {
      // Loading will be set to false automatically when brand identity appears via Realtime
    },
  });

  const specialOffersExtraction = useExtractionState({
    extractionType: 'special offers',
    propertyId,
    apiEndpoint: `/api/properties/${propertyId}/extract/special-offers`,
    onSuccess: () => {
      // Loading will be set to false automatically when special offers appear via Realtime
    },
  });

  const reviewsExtraction = useExtractionState({
    extractionType: 'reviews',
    propertyId,
    apiEndpoint: `/api/properties/${propertyId}/extract/reviews`,
    onSuccess: () => {
      // Loading will be set to false automatically when reviews appear via Realtime
    },
  });

  const competitorsExtraction = useExtractionState({
    extractionType: 'competitors',
    propertyId,
    apiEndpoint: `/api/properties/${propertyId}/extract/competitors`,
    onSuccess: () => {
      setTimeout(() => {
        fetchPropertyData();
        setTimeout(() => competitorsExtraction.clearMessages(), 3000);
      }, 2000);
    },
  });

  // Image classification uses a different endpoint
  const [isClassifyingImages, setIsClassifyingImages] = useState(false);
  const [classifyImagesSuccessMessage, setClassifyImagesSuccessMessage] = useState<string | null>(null);
  const [classifyImagesErrorMessage, setClassifyImagesErrorMessage] = useState<string | null>(null);

  // Realtime subscription channel refs
  const imagesChannelRef = useRef<RealtimeChannel | null>(null);
  const amenitiesChannelRef = useRef<RealtimeChannel | null>(null);
  const floorPlansChannelRef = useRef<RealtimeChannel | null>(null);
  const brandIdentityChannelRef = useRef<RealtimeChannel | null>(null);
  const specialOffersChannelRef = useRef<RealtimeChannel | null>(null);
  const reviewsChannelRef = useRef<RealtimeChannel | null>(null);


  // Define fetchPropertyData outside useEffect so it can be called from extraction handlers
  const fetchPropertyData = useCallback(async () => {
    if (!propertyId) return;
    
    try {
      setLoading(true);

      // Fetch property
      const { data: propertyData, error: propertyError } = await supabase
        .from('properties')
        .select('*')
        .eq('id', propertyId)
        .single();

      if (propertyError) {
        throw propertyError;
      }

      if (!propertyData) {
        setError('Property not found');
        setLoading(false);
        return;
      }

      setProperty(propertyData);

      // Fetch images
      const { data: imagesData, error: imagesError } = await supabase
        .from('property_images')
        .select('*')
        .eq('property_id', propertyId)
        .order('created_at', { ascending: false });

      if (imagesError) {
        console.error('Error fetching images:', imagesError);
        console.error('Supabase URL:', process.env.NEXT_PUBLIC_SUPABASE_URL || 'not set (check .env.local)');
        // Don't throw - property might not have images
      } else {
        // Ensure is_hidden defaults to false for images that don't have it set
        const imagesWithDefaults = (imagesData || []).map((img: PropertyImage) => ({
          ...img,
          is_hidden: img.is_hidden ?? false,
        }));
        console.log(`[DEBUG] Fetched ${imagesWithDefaults.length} images for property ${propertyId}`);
        console.log('[DEBUG] Sample images:', imagesWithDefaults.slice(0, 3).map(img => ({
          id: img.id,
          url: img.image_url.substring(0, 60),
          is_hidden: img.is_hidden,
          tags: img.image_tags
        })));
        setImages(imagesWithDefaults);
      }

      // Fetch branding data
      const { data: brandingData, error: brandingError } = await supabase
        .from('property_branding')
        .select('*')
        .eq('property_id', propertyId)
        .single();

      if (brandingError) {
        // Only log if it's not a "not found" error (PGRST116)
        // Missing branding data is expected for properties that haven't been fully onboarded
        if (brandingError.code !== 'PGRST116' && brandingError.message !== 'JSON object requested, multiple (or no) rows returned') {
          console.error('Error fetching branding:', brandingError);
        }
        setBranding(null);
      } else {
        setBranding(brandingData);
      }

      // Fetch amenities data
      const { data: amenitiesData, error: amenitiesError } = await supabase
        .from('property_amenities')
        .select('*')
        .eq('property_id', propertyId)
        .single();

      if (amenitiesError) {
        // Only log if it's not a "not found" error (PGRST116)
        // Missing amenities data is expected for properties that haven't been fully onboarded
        if (amenitiesError.code !== 'PGRST116' && amenitiesError.message !== 'JSON object requested, multiple (or no) rows returned') {
          console.error('Error fetching amenities:', amenitiesError);
        }
        setAmenities(null);
      } else {
        setAmenities(amenitiesData);
      }

      // Fetch floor plans data
      const { data: floorPlansData, error: floorPlansError } = await supabase
        .from('property_floor_plans')
        .select('*')
        .eq('property_id', propertyId)
        .order('bedrooms', { ascending: true, nullsFirst: false })
        .order('min_price', { ascending: true, nullsFirst: false });

      if (floorPlansError) {
        // Don't throw - property might not have floor plans data
        console.error('Error fetching floor plans:', floorPlansError);
        setFloorPlans([]);
      } else {
        setFloorPlans(floorPlansData || []);
      }

      // Fetch special offers data
      const { data: specialOffersData, error: specialOffersError } = await supabase
        .from('property_special_offers')
        .select('*')
        .eq('property_id', propertyId)
        .order('created_at', { ascending: false });

      if (specialOffersError) {
        // Don't throw - property might not have special offers data
        console.error('Error fetching special offers:', specialOffersError);
        setSpecialOffers([]);
      } else {
        setSpecialOffers(specialOffersData || []);
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load property');
      console.error('Error fetching property:', err);
    } finally {
      setLoading(false);
    }
  }, [propertyId]);

  useEffect(() => {
    if (propertyId) {
      fetchPropertyData();
    }
  }, [propertyId, fetchPropertyData]);

  // Set up Realtime subscriptions for Images
  useEffect(() => {
    if (!propertyId || !imagesExtraction.isLoading) {
      if (imagesChannelRef.current) {
        supabase.removeChannel(imagesChannelRef.current);
        imagesChannelRef.current = null;
      }
      return;
    }

    const channel = supabase
      .channel(`images:${propertyId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'property_images',
          filter: `property_id=eq.${propertyId}`,
        },
        (payload) => {
          console.log('New image detected via Realtime:', payload);
          fetchPropertyData();
        }
      )
      .subscribe((status) => {
        console.log('Images Realtime subscription status:', status);
      });

    imagesChannelRef.current = channel;

    return () => {
      if (imagesChannelRef.current) {
        supabase.removeChannel(imagesChannelRef.current);
        imagesChannelRef.current = null;
      }
    };
  }, [propertyId, imagesExtraction.isLoading, fetchPropertyData]);

  // Set up Realtime subscriptions for Amenities (single row - INSERT or UPDATE)
  useEffect(() => {
    if (!propertyId || !amenitiesExtraction.isLoading) {
      if (amenitiesChannelRef.current) {
        supabase.removeChannel(amenitiesChannelRef.current);
        amenitiesChannelRef.current = null;
      }
      return;
    }

    const channel = supabase
      .channel(`amenities:${propertyId}`)
      .on(
        'postgres_changes',
        {
          event: '*', // Listen for both INSERT and UPDATE
          schema: 'public',
          table: 'property_amenities',
          filter: `property_id=eq.${propertyId}`,
        },
        (payload) => {
          console.log('Amenities data detected via Realtime:', payload);
          fetchPropertyData();
        }
      )
      .subscribe((status) => {
        console.log('Amenities Realtime subscription status:', status);
      });

    amenitiesChannelRef.current = channel;

    return () => {
      if (amenitiesChannelRef.current) {
        supabase.removeChannel(amenitiesChannelRef.current);
        amenitiesChannelRef.current = null;
      }
    };
  }, [propertyId, amenitiesExtraction.isLoading, fetchPropertyData]);

  // Set up Realtime subscriptions for Floor Plans
  useEffect(() => {
    if (!propertyId || !floorPlansExtraction.isLoading) {
      if (floorPlansChannelRef.current) {
        supabase.removeChannel(floorPlansChannelRef.current);
        floorPlansChannelRef.current = null;
      }
      return;
    }

    const channel = supabase
      .channel(`floor-plans:${propertyId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'property_floor_plans',
          filter: `property_id=eq.${propertyId}`,
        },
        (payload) => {
          console.log('New floor plan detected via Realtime:', payload);
          fetchPropertyData();
        }
      )
      .subscribe((status) => {
        console.log('Floor Plans Realtime subscription status:', status);
      });

    floorPlansChannelRef.current = channel;

    return () => {
      if (floorPlansChannelRef.current) {
        supabase.removeChannel(floorPlansChannelRef.current);
        floorPlansChannelRef.current = null;
      }
    };
  }, [propertyId, floorPlansExtraction.isLoading, fetchPropertyData]);

  // Set up Realtime subscriptions for Brand Identity (single row - INSERT or UPDATE)
  useEffect(() => {
    if (!propertyId || !brandIdentityExtraction.isLoading) {
      if (brandIdentityChannelRef.current) {
        supabase.removeChannel(brandIdentityChannelRef.current);
        brandIdentityChannelRef.current = null;
      }
      return;
    }

    const channel = supabase
      .channel(`brand-identity:${propertyId}`)
      .on(
        'postgres_changes',
        {
          event: '*', // Listen for both INSERT and UPDATE
          schema: 'public',
          table: 'property_branding',
          filter: `property_id=eq.${propertyId}`,
        },
        (payload) => {
          console.log('Brand identity data detected via Realtime:', payload);
          fetchPropertyData();
        }
      )
      .subscribe((status) => {
        console.log('Brand Identity Realtime subscription status:', status);
      });

    brandIdentityChannelRef.current = channel;

    return () => {
      if (brandIdentityChannelRef.current) {
        supabase.removeChannel(brandIdentityChannelRef.current);
        brandIdentityChannelRef.current = null;
      }
    };
  }, [propertyId, brandIdentityExtraction.isLoading, fetchPropertyData]);

  // Set up Realtime subscriptions for Special Offers
  useEffect(() => {
    if (!propertyId || !specialOffersExtraction.isLoading) {
      if (specialOffersChannelRef.current) {
        supabase.removeChannel(specialOffersChannelRef.current);
        specialOffersChannelRef.current = null;
      }
      return;
    }

    const channel = supabase
      .channel(`special-offers:${propertyId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'property_special_offers',
          filter: `property_id=eq.${propertyId}`,
        },
        (payload) => {
          console.log('New special offer detected via Realtime:', payload);
          fetchPropertyData();
        }
      )
      .subscribe((status) => {
        console.log('Special Offers Realtime subscription status:', status);
      });

    specialOffersChannelRef.current = channel;

    return () => {
      if (specialOffersChannelRef.current) {
        supabase.removeChannel(specialOffersChannelRef.current);
        specialOffersChannelRef.current = null;
      }
    };
  }, [propertyId, specialOffersExtraction.isLoading, fetchPropertyData]);

  // Set up Realtime subscriptions for Reviews
  useEffect(() => {
    if (!propertyId || !reviewsExtraction.isLoading) {
      if (reviewsChannelRef.current) {
        supabase.removeChannel(reviewsChannelRef.current);
        reviewsChannelRef.current = null;
      }
      return;
    }

    const channel = supabase
      .channel(`reviews:${propertyId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'property_reviews',
          filter: `property_id=eq.${propertyId}`,
        },
        (payload) => {
          console.log('New review detected via Realtime:', payload);
          fetchPropertyData();
        }
      )
      .subscribe((status) => {
        console.log('Reviews Realtime subscription status:', status);
      });

    reviewsChannelRef.current = channel;

    return () => {
      if (reviewsChannelRef.current) {
        supabase.removeChannel(reviewsChannelRef.current);
        reviewsChannelRef.current = null;
      }
    };
  }, [propertyId, reviewsExtraction.isLoading, fetchPropertyData]);

  // Check if images have appeared and stop extraction state
  useEffect(() => {
    if (imagesExtraction.isLoading && images.length > 0) {
      imagesExtraction.stopLoading();
      imagesExtraction.clearMessages();
      if (imagesChannelRef.current) {
        supabase.removeChannel(imagesChannelRef.current);
        imagesChannelRef.current = null;
      }
    }
  }, [imagesExtraction.isLoading, images.length, imagesExtraction.stopLoading, imagesExtraction.clearMessages]);

  // Check if amenities have appeared and stop extraction state
  useEffect(() => {
    if (amenitiesExtraction.isLoading && amenities) {
      amenitiesExtraction.stopLoading();
      amenitiesExtraction.clearMessages();
      if (amenitiesChannelRef.current) {
        supabase.removeChannel(amenitiesChannelRef.current);
        amenitiesChannelRef.current = null;
      }
    }
  }, [amenitiesExtraction.isLoading, amenities, amenitiesExtraction.stopLoading, amenitiesExtraction.clearMessages]);

  // Check if floor plans have appeared and stop extraction state
  useEffect(() => {
    if (floorPlansExtraction.isLoading && floorPlans.length > 0) {
      floorPlansExtraction.stopLoading();
      floorPlansExtraction.clearMessages();
      if (floorPlansChannelRef.current) {
        supabase.removeChannel(floorPlansChannelRef.current);
        floorPlansChannelRef.current = null;
      }
    }
  }, [floorPlansExtraction.isLoading, floorPlans.length, floorPlansExtraction.stopLoading, floorPlansExtraction.clearMessages]);

  // Check if brand identity has appeared and stop extraction state
  useEffect(() => {
    if (brandIdentityExtraction.isLoading && branding) {
      brandIdentityExtraction.stopLoading();
      brandIdentityExtraction.clearMessages();
      if (brandIdentityChannelRef.current) {
        supabase.removeChannel(brandIdentityChannelRef.current);
        brandIdentityChannelRef.current = null;
      }
    }
  }, [brandIdentityExtraction.isLoading, branding, brandIdentityExtraction.stopLoading, brandIdentityExtraction.clearMessages]);

  // Check if special offers have appeared and stop extraction state
  useEffect(() => {
    if (specialOffersExtraction.isLoading && specialOffers.length > 0) {
      specialOffersExtraction.stopLoading();
      specialOffersExtraction.clearMessages();
      if (specialOffersChannelRef.current) {
        supabase.removeChannel(specialOffersChannelRef.current);
        specialOffersChannelRef.current = null;
      }
    }
  }, [specialOffersExtraction.isLoading, specialOffers.length, specialOffersExtraction.stopLoading, specialOffersExtraction.clearMessages]);

  // Check if reviews have appeared and stop extraction state
  // Note: We need to check if reviews exist - this might require checking a reviews summary or count
  // For now, we'll check if the ReviewsSection component would show data
  // This is a bit tricky since reviews might be in a separate component
  // Let's check if we can detect reviews through the property data or a separate state
  // For now, we'll rely on the Realtime subscription to trigger fetchPropertyData
  // and the ReviewsSection component handles its own state


  // Function to mark an image as unavailable
  const markImageAsUnavailable = useCallback((imageId: string) => {
    setUnavailableImageIds((prev) => new Set(prev).add(imageId));
  }, []);

  // Extraction handlers - now use unified hook
  const handleExtractImages = () => imagesExtraction.startExtraction();
  const handleExtractAmenities = () => amenitiesExtraction.startExtraction();
  const handleExtractFloorPlans = () => floorPlansExtraction.startExtraction();
  const handleExtractBrandIdentity = () => brandIdentityExtraction.startExtraction();
  const handleExtractSpecialOffers = () => specialOffersExtraction.startExtraction();
  const handleExtractReviews = () => reviewsExtraction.startExtraction();
  const handleExtractCompetitors = () => competitorsExtraction.startExtraction();

  const handleClassifyImages = async () => {
    if (!propertyId || isClassifyingImages) return;
    
    try {
      setIsClassifyingImages(true);
      setClassifyImagesErrorMessage(null);
      setClassifyImagesSuccessMessage(null);

      const response = await fetch(`/api/properties/${propertyId}/classify-images`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ force_reclassify: false }),
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Failed to classify images');
      }

      // Show success message with actual results
      const classified = result.classified || 0;
      const failed = result.failed || 0;
      const total = result.total_images || 0;
      
      if (classified > 0) {
        setClassifyImagesSuccessMessage(
          `Successfully classified ${classified} image${classified !== 1 ? 's' : ''}${failed > 0 ? ` (${failed} failed)` : ''}!`
        );
      } else if (result.images_to_classify === 0) {
        setClassifyImagesSuccessMessage('All images are already classified!');
      } else {
        setClassifyImagesSuccessMessage('Classification completed, but no images were classified.');
      }
      
      // Clear loading state immediately since classification is complete
      setIsClassifyingImages(false);
      
      // Refresh to show updated tags
      fetchPropertyData();
      
      // Clear success message after 5 seconds
      setTimeout(() => setClassifyImagesSuccessMessage(null), 5000);
      
    } catch (error: any) {
      console.error('Error classifying images:', error);
      setClassifyImagesErrorMessage(error.message || 'Failed to classify images. Please try again.');
      setIsClassifyingImages(false);
    }
  };


  const getAddress = (property: Property) => {
    const parts = [
      property.street_address,
      property.city,
      property.state,
      property.zip_code,
    ].filter(Boolean);
    return parts.length > 0 ? parts.join(', ') : null;
  };

  const formatOfficeHours = (officeHours: Record<string, any> | null) => {
    if (!officeHours) return null;

    if (typeof officeHours === 'string') {
      return officeHours;
    }

    if (Array.isArray(officeHours)) {
      return officeHours.join(', ');
    }

    // If it's an object, format it nicely with plain English labels
    const dayLabels: Record<string, string> = {
      monday_friday: 'Monday - Friday',
      saturday: 'Saturday',
      sunday: 'Sunday',
    };

    // Define the order: Monday-Friday first, then Saturday, then Sunday
    const dayOrder = ['monday_friday', 'saturday', 'sunday'];

    const formattedHours: string[] = [];

    // Process days in the specified order
    dayOrder.forEach((dayKey) => {
      if (officeHours[dayKey]) {
        const hours = officeHours[dayKey];
        const dayLabel = dayLabels[dayKey] || dayKey;
        const hoursStr = typeof hours === 'string' ? hours : JSON.stringify(hours);
        formattedHours.push(`${dayLabel}: ${hoursStr}`);
      }
    });

    // Handle any other days that might exist (fallback)
    Object.entries(officeHours).forEach(([day, hours]) => {
      if (!dayOrder.includes(day)) {
        const hoursStr = typeof hours === 'string' ? hours : JSON.stringify(hours);
        // Capitalize first letter of day name
        const dayLabel = day.charAt(0).toUpperCase() + day.slice(1).replace(/_/g, ' ');
        formattedHours.push(`${dayLabel}: ${hoursStr}`);
      }
    });

    return formattedHours.length > 0 ? formattedHours.join('\n') : null;
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="text-lg text-neutral-800">Loading property...</div>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="min-h-screen bg-neutral-50">
        <div className="container mx-auto px-6 py-8 max-w-7xl">
          <Link
            href="/properties"
            className="text-primary-500 hover:text-primary-600 hover:underline mb-4 inline-block transition-colors focus:outline-none focus:ring-4 focus:ring-primary-300 rounded-lg px-2 py-1"
          >
            ← Back to Properties
          </Link>
          <div className="text-center py-16">
            <p className="text-lg text-error">
              {error || 'Property not found'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const address = getAddress(property);
  const officeHours = formatOfficeHours(property.office_hours);

  // Filter out unavailable images, then filter into visible and hidden
  const availableImages = images.filter((img) => !unavailableImageIds.has(img.id));
  const visibleImages = availableImages.filter((img) => !img.is_hidden);
  const hiddenImages = availableImages.filter((img) => img.is_hidden);
  
  // Debug logging
  if (images.length > 0) {
    console.log(`[DEBUG] Image counts - Total: ${images.length}, Available: ${availableImages.length}, Visible: ${visibleImages.length}, Hidden: ${hiddenImages.length}, Unavailable: ${unavailableImageIds.size}`);
  }

  // Group visible images by primary tag and sort
  const groupImagesByCategory = (imageList: PropertyImage[]) => {
    const grouped: Record<string, PropertyImage[]> = {};
    
    imageList.forEach((img) => {
      const primaryTag = getPrimaryTag(img.image_tags);
      if (!grouped[primaryTag]) {
        grouped[primaryTag] = [];
      }
      grouped[primaryTag].push(img);
    });
    
    // Sort images within each group by quality_score (descending), then by created_at
    Object.keys(grouped).forEach((tag) => {
      grouped[tag].sort((a, b) => {
        // Sort by quality_score first (higher is better)
        const qualityA = a.quality_score ?? 0;
        const qualityB = b.quality_score ?? 0;
        if (qualityB !== qualityA) {
          return qualityB - qualityA;
        }
        // Then by created_at (newer first)
        const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return dateB - dateA;
      });
    });
    
    return grouped;
  };

  const visibleImagesGrouped = groupImagesByCategory(visibleImages);
  const hiddenImagesGrouped = groupImagesByCategory(hiddenImages);

  // Get sorted category keys
  const sortedVisibleCategories = sortCategoriesByOrder(Object.keys(visibleImagesGrouped));
  const sortedHiddenCategories = sortCategoriesByOrder(Object.keys(hiddenImagesGrouped));
  
  // Debug logging for categories
  if (visibleImages.length > 0) {
    console.log('[DEBUG] Visible images grouped by category:', Object.keys(visibleImagesGrouped).map(cat => ({
      category: cat,
      count: visibleImagesGrouped[cat].length
    })));
  }

  // Flatten images for gallery (maintaining order)
  const allVisibleImagesForGallery: PropertyImage[] = [];
  sortedVisibleCategories.forEach((category) => {
    allVisibleImagesForGallery.push(...visibleImagesGrouped[category]);
  });
  
  const allHiddenImagesForGallery: PropertyImage[] = [];
  sortedHiddenCategories.forEach((category) => {
    allHiddenImagesForGallery.push(...hiddenImagesGrouped[category]);
  });

  const toggleImageVisibility = async (imageId: string, currentIsHidden: boolean) => {
    const newIsHidden = !currentIsHidden;
    
    try {
      console.log('Toggling image visibility:', { imageId, currentIsHidden, newIsHidden });
      
      const { error: updateError, data } = await supabase
        .from('property_images')
        .update({ is_hidden: newIsHidden })
        .eq('id', imageId)
        .select();

      console.log('Update response:', { error: updateError, data });

      if (updateError) {
        console.error('Error updating image visibility:', updateError);
        console.error('Error keys:', Object.keys(updateError));
        console.error('Error stringified:', JSON.stringify(updateError, null, 2));
        
        // Extract error message from Supabase error object
        const errorMessage = 
          updateError.message || 
          updateError.details || 
          updateError.hint || 
          (typeof updateError === 'object' ? JSON.stringify(updateError) : String(updateError)) ||
          'Unknown error';
        
        // Check if the error is about missing column (migration not run)
        if (errorMessage.includes('column') && (errorMessage.includes('is_hidden') || errorMessage.includes('does not exist'))) {
          alert(
            'Database migration not run. Please run the migration to add the is_hidden column:\n\n' +
            'supabase/migrations/20251221160140_add_is_hidden_to_property_images.sql\n\n' +
            `Error details: ${errorMessage}`
          );
        } else if (errorMessage.includes('permission') || errorMessage.includes('policy') || errorMessage.includes('RLS')) {
          alert(
            'Permission denied. This might be a Row Level Security (RLS) policy issue.\n\n' +
            'Please check your Supabase RLS policies for the property_images table.\n\n' +
            `Error details: ${errorMessage}`
          );
        } else {
          alert(`Failed to update image visibility.\n\nError: ${errorMessage}\n\nCode: ${updateError.code || 'N/A'}\n\nPlease check the browser console for more details.`);
        }
        return;
      }

      if (!data || data.length === 0) {
        console.warn('Update succeeded but no data returned');
        // Still update local state as the update might have succeeded
      }

      // Update local state immediately for better UX
      setImages((prevImages) =>
        prevImages.map((img) =>
          img.id === imageId ? { ...img, is_hidden: newIsHidden } : img
        )
      );

      // If hiding an image, expand the hidden section
      if (newIsHidden && !showHiddenImages) {
        setShowHiddenImages(true);
      }
    } catch (err) {
      console.error('Error toggling image visibility:', err);
      const errorMessage = err instanceof Error ? err.message : String(err);
      alert(`Failed to update image visibility: ${errorMessage}`);
    }
  };

  // Eye icon SVG component
  const EyeIcon = ({ className }: { className?: string }) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className={className || 'w-5 h-5'}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
      />
    </svg>
  );

  // Eye slash icon SVG component
  const EyeSlashIcon = ({ className }: { className?: string }) => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className={className || 'w-5 h-5'}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 01-4.243-4.243m4.242 4.242L9.88 9.88"
      />
    </svg>
  );

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="container mx-auto px-6 py-8 max-w-7xl">
        <Link
          href="/properties"
          className="text-primary-500 hover:text-primary-600 hover:underline mb-6 inline-block transition-colors focus:outline-none focus:ring-4 focus:ring-primary-300 rounded-lg px-2 py-1"
        >
          ← Back to Properties
        </Link>

        <div className="flex items-center gap-4 mb-6">
          {branding && branding.branding_data && branding.branding_data.logo && (
            <img
              src={branding.branding_data.logo}
              alt="Property logo"
              className="h-16 w-auto object-contain"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
              }}
            />
          )}
          <h1 className="text-4xl font-bold text-secondary-700 font-display">
            {property.property_name || 'Unnamed Property'}
          </h1>
        </div>

        <div className="space-y-6">
          {/* Basic Information Card */}
          <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md transition-all duration-300 hover:shadow-lg">
            <h2 className="text-2xl font-bold text-secondary-700 mb-4 font-display flex items-center gap-2">
              <Building2 className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
              Basic Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Address */}
              <div>
                <p className="text-sm font-semibold text-neutral-700 mb-1 flex items-center gap-2 uppercase tracking-wide">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-5 h-5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"
                    />
                  </svg>
                  Address
                </p>
                <p className="text-base text-neutral-900 leading-relaxed">
                  {address || <span className="text-neutral-400 italic">Not collected</span>}
                </p>
              </div>

              {/* Phone */}
              <div>
                <p className="text-sm font-semibold text-neutral-700 mb-1 flex items-center gap-2 uppercase tracking-wide">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-5 h-5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z"
                    />
                  </svg>
                  Phone
                </p>
                <p className="text-base text-neutral-900 leading-relaxed">
                  {property.phone ? (
                    <a
                      href={`tel:${property.phone}`}
                      className="text-primary-500 hover:text-primary-600 hover:underline transition-colors"
                    >
                      {property.phone}
                    </a>
                  ) : (
                    <span className="text-neutral-400 italic">Not collected</span>
                  )}
                </p>
              </div>

              {/* Email */}
              <div>
                <p className="text-sm font-semibold text-neutral-700 mb-1 flex items-center gap-2 uppercase tracking-wide">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-5 h-5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
                    />
                  </svg>
                  Email
                </p>
                <p className="text-base text-neutral-900 leading-relaxed">
                  {property.email ? (
                    <a
                      href={`mailto:${property.email}`}
                      className="text-primary-500 hover:text-primary-600 hover:underline transition-colors"
                    >
                      {property.email}
                    </a>
                  ) : (
                    <span className="text-neutral-400 italic">Not collected</span>
                  )}
                </p>
              </div>

              {/* Website */}
              <div>
                <p className="text-sm font-semibold text-neutral-700 mb-1 flex items-center gap-2 uppercase tracking-wide">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-5 h-5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418"
                    />
                  </svg>
                  Website
                </p>
                <p className="text-base text-neutral-900 leading-relaxed">
                  {property.website_url ? (
                    <a
                      href={property.website_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-500 hover:text-primary-600 hover:underline transition-colors"
                    >
                      {property.website_url}
                    </a>
                  ) : (
                    <span className="text-neutral-400 italic">Not collected</span>
                  )}
                </p>
              </div>

              {/* Office Hours */}
              <div>
                <p className="text-sm font-semibold text-neutral-700 mb-1 flex items-center gap-2 uppercase tracking-wide">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                    className="w-5 h-5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  Office Hours
                </p>
                <div className="text-base text-neutral-900 leading-relaxed whitespace-pre-wrap">
                  {officeHours || <span className="text-neutral-400 italic">Not collected</span>}
                </div>
              </div>
            </div>
          </div>

          {/* Floor Plans Card */}
          <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md transition-all duration-300 hover:shadow-lg">
            <h2 className="text-2xl font-bold text-secondary-700 mb-4 font-display flex items-center gap-2">
              <Layout className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
              Floor Plans
            </h2>
            {floorPlans.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-200">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                        Name
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                        Size
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                        Bed/Bath
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                        Price
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                        Availability
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {floorPlans.map((floorPlan) => {
                      // Format bathrooms (handle half baths)
                      const formatBathrooms = (baths: number | null) => {
                        if (baths === null) return null;
                        if (baths % 1 === 0) return `${baths}BA`;
                        return `${baths}BA`;
                      };

                      // Format bedrooms
                      const formatBedrooms = (beds: number | null) => {
                        if (beds === null) return null;
                        return `${beds}BR`;
                      };

                      const bedStr = formatBedrooms(floorPlan.bedrooms);
                      const bathStr = formatBathrooms(floorPlan.bathrooms);
                      const bedBathStr = [bedStr, bathStr].filter(Boolean).join(' / ');

                      // Format availability
                      let availabilityDisplay = null;
                      if (floorPlan.available_units !== null) {
                        availabilityDisplay = (
                          <span className="text-sm text-success-dark font-medium">
                            {floorPlan.available_units} {floorPlan.available_units === 1 ? 'unit' : 'units'}
                          </span>
                        );
                      } else if (floorPlan.is_available !== null) {
                        availabilityDisplay = (
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${
                              floorPlan.is_available
                                ? 'bg-success-light text-success-dark'
                                : 'bg-error-light text-error-dark'
                            }`}
                          >
                            {floorPlan.is_available ? 'Available' : 'Not Available'}
                          </span>
                        );
                      }

                      return (
                        <tr
                          key={floorPlan.id}
                          className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors"
                        >
                          <td className="py-4 px-4">
                            <span className="text-lg font-semibold text-neutral-900">
                              {floorPlan.name}
                            </span>
                          </td>
                          <td className="py-4 px-4">
                            {floorPlan.size_sqft ? (
                              <span className="text-sm text-neutral-700">
                                {floorPlan.size_sqft.toLocaleString()} sqft
                              </span>
                            ) : (
                              <span className="text-sm text-neutral-400">—</span>
                            )}
                          </td>
                          <td className="py-4 px-4">
                            {bedBathStr ? (
                              <span className="text-sm text-neutral-700">
                                {bedBathStr}
                              </span>
                            ) : (
                              <span className="text-sm text-neutral-400">—</span>
                            )}
                          </td>
                          <td className="py-4 px-4">
                            {floorPlan.price_string ? (
                              <span className="text-base font-semibold text-neutral-900">
                                {floorPlan.price_string}
                              </span>
                            ) : (
                              <span className="text-sm text-neutral-400">—</span>
                            )}
                          </td>
                          <td className="py-4 px-4">
                            {availabilityDisplay || (
                              <span className="text-sm text-neutral-400">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <>
                {floorPlansExtraction.isLoading ? (
                  <ExtractionLoadingState
                    toolName="floor plans"
                    isGenerating={floorPlansExtraction.isLoading}
                  />
                ) : (
                  <div className="rounded-lg border border-neutral-200 shadow-sm bg-neutral-50 p-8 text-center">
                    <div className="max-w-md mx-auto">
                      <Layout className="w-12 h-12 text-neutral-400 mx-auto mb-4" strokeWidth={1.5} />
                      <p className="text-neutral-600 mb-2 font-medium">
                        No floor plans collected yet
                      </p>
                      <p className="text-sm text-neutral-500 mb-6">
                        Floor plan information will appear here once collected from the property website.
                      </p>
                      <button
                        onClick={handleExtractFloorPlans}
                        disabled={floorPlansExtraction.isLoading}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-primary-500 text-white font-semibold rounded-lg hover:bg-primary-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-primary-300"
                      >
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
                          />
                        </svg>
                        Extract Floor Plans
                      </button>
                      {floorPlansExtraction.success && (
                        <StatusMessage
                          type="success"
                          message={floorPlansExtraction.success}
                          onDismiss={() => floorPlansExtraction.clearMessages()}
                        />
                      )}
                      {floorPlansExtraction.error && (
                        <StatusMessage
                          type="error"
                          message={floorPlansExtraction.error}
                          onRetry={floorPlansExtraction.retry}
                        />
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Special Offers Card */}
          <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md transition-all duration-300 hover:shadow-lg">
            <h2 className="text-2xl font-bold text-secondary-700 mb-4 font-display flex items-center gap-2">
              <Gift className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
              Special Offers
            </h2>
            {specialOffers.length > 0 ? (
              <div className="space-y-4">
                {specialOffers.map((offer) => {
                  // Format expiration date if available
                  const formatDate = (dateString: string | null) => {
                    if (!dateString) return null;
                    try {
                      const date = new Date(dateString);
                      return date.toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      });
                    } catch {
                      return dateString;
                    }
                  };

                  const expirationDate = formatDate(offer.valid_until);

                  return (
                    <div
                      key={offer.id}
                      className="border border-primary-200 rounded-lg p-6 bg-primary-50/50 hover:bg-primary-50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-secondary-700 mb-2">
                            {offer.offer_description}
                          </h3>
                          {offer.descriptive_text && (
                            <p className="text-base text-neutral-700 mb-2 leading-relaxed">
                              {offer.descriptive_text}
                            </p>
                          )}
                          <div className="flex flex-wrap gap-4 text-sm text-neutral-600">
                            {expirationDate && (
                              <span className="flex items-center gap-1">
                                <svg
                                  xmlns="http://www.w3.org/2000/svg"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  strokeWidth={1.5}
                                  stroke="currentColor"
                                  className="w-4 h-4"
                                >
                                  <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5"
                                  />
                                </svg>
                                Valid until: {expirationDate}
                              </span>
                            )}
                            {offer.floor_plan_id && (
                              <span className="flex items-center gap-1">
                                <Layout className="w-4 h-4" />
                                Applies to specific floor plan
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <>
                {specialOffersExtraction.isLoading ? (
                  <ExtractionLoadingState
                    toolName="special offers"
                    isGenerating={specialOffersExtraction.isLoading}
                  />
                ) : (
                  <div className="rounded-lg border border-neutral-200 shadow-sm bg-neutral-50 p-8 text-center">
                    <div className="max-w-md mx-auto">
                      <Gift className="w-12 h-12 text-neutral-400 mx-auto mb-4" strokeWidth={1.5} />
                      <p className="text-neutral-600 mb-2 font-medium">
                        No special offers collected yet
                      </p>
                      <p className="text-sm text-neutral-500 mb-6">
                        Special offers and promotions will appear here once collected from the property website.
                      </p>
                      <button
                        onClick={handleExtractSpecialOffers}
                        disabled={specialOffersExtraction.isLoading}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-primary-500 text-white font-semibold rounded-lg hover:bg-primary-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-primary-300"
                      >
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
                          />
                        </svg>
                        Extract Special Offers
                      </button>
                      {specialOffersExtraction.success && (
                        <StatusMessage
                          type="success"
                          message={specialOffersExtraction.success}
                          onDismiss={() => specialOffersExtraction.clearMessages()}
                        />
                      )}
                      {specialOffersExtraction.error && (
                        <StatusMessage
                          type="error"
                          message={specialOffersExtraction.error}
                          onRetry={specialOffersExtraction.retry}
                        />
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Brand Identity Card */}
          <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md transition-all duration-300 hover:shadow-lg">
            <h2 className="text-2xl font-bold text-secondary-700 mb-4 font-display flex items-center gap-2">
              <Palette className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
              Brand Identity
            </h2>
            {branding && branding.branding_data ? (
              <div className="space-y-6">
                {/* Tagline */}
                {branding.branding_data.tagline && (
                  <div>
                    <p className="text-sm font-semibold text-neutral-700 mb-1 uppercase tracking-wide">
                      Tagline
                    </p>
                    <p className="text-base text-neutral-900 italic leading-relaxed">
                      {branding.branding_data.tagline}
                    </p>
                  </div>
                )}

                {/* Tone */}
                {branding.branding_data.tone && branding.branding_data.tone.description && (
                  <div>
                    <p className="text-sm font-semibold text-neutral-700 mb-1 uppercase tracking-wide">
                      Tone
                    </p>
                    <p className="text-base text-neutral-900 leading-relaxed">
                      {branding.branding_data.tone.description}
                    </p>
                  </div>
                )}

                {/* Keywords */}
                {branding.branding_data.tone && branding.branding_data.tone.tone_tags && Array.isArray(branding.branding_data.tone.tone_tags) && branding.branding_data.tone.tone_tags.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-neutral-700 mb-2 uppercase tracking-wide">
                      Keywords
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {branding.branding_data.tone.tone_tags.map((tag, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold uppercase tracking-wide"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Brand Colors */}
                {branding.branding_data.colors && Object.keys(branding.branding_data.colors).length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-neutral-700 mb-2 uppercase tracking-wide">
                      Brand Colors
                    </p>
                    <div className="flex flex-wrap gap-3">
                      {Object.entries(branding.branding_data.colors).map(([colorName, colorValue]) => {
                        if (!colorValue || typeof colorValue !== 'string') return null;
                        
                        return (
                          <div
                            key={colorName}
                            className="w-12 h-12 rounded-lg border border-neutral-200 flex-shrink-0 shadow-sm"
                            style={{ backgroundColor: colorValue }}
                            title={colorValue}
                          />
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <>
                {brandIdentityExtraction.isLoading ? (
                  <ExtractionLoadingState
                    toolName="brand identity"
                    isGenerating={brandIdentityExtraction.isLoading}
                  />
                ) : (
                  <div className="rounded-lg border border-neutral-200 shadow-sm bg-neutral-50 p-8 text-center">
                    <div className="max-w-md mx-auto">
                      <Palette className="w-12 h-12 text-neutral-400 mx-auto mb-4" strokeWidth={1.5} />
                      <p className="text-neutral-600 mb-2 font-medium">
                        No brand identity collected yet
                      </p>
                      <p className="text-sm text-neutral-500 mb-6">
                        Brand identity information including colors, fonts, tone, and tagline will appear here once collected from the property website.
                      </p>
                      <button
                        onClick={handleExtractBrandIdentity}
                        disabled={brandIdentityExtraction.isLoading}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-primary-500 text-white font-semibold rounded-lg hover:bg-primary-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-primary-300"
                      >
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
                          />
                        </svg>
                        Extract Brand Identity
                      </button>
                      {brandIdentityExtraction.success && (
                        <StatusMessage
                          type="success"
                          message={brandIdentityExtraction.success}
                          onDismiss={() => brandIdentityExtraction.clearMessages()}
                        />
                      )}
                      {brandIdentityExtraction.error && (
                        <StatusMessage
                          type="error"
                          message={brandIdentityExtraction.error}
                          onRetry={brandIdentityExtraction.retry}
                        />
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Images Card */}
          <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md transition-all duration-300 hover:shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-secondary-700 font-display flex items-center gap-2">
                <ImageIcon className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
                Images ({visibleImages.length})
              </h2>
              {availableImages.length > 0 && (
                <button
                    onClick={handleClassifyImages}
                    disabled={isClassifyingImages}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-primary-500 text-white font-semibold rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-primary-300"
                  >
                    <span>✨</span>
                    Tag Images with AI
                  </button>
              )}
            </div>
            {isClassifyingImages && (
              <div className="mb-6">
                <ExtractionLoadingState
                  toolName="image tags"
                  isGenerating={isClassifyingImages}
                />
              </div>
            )}
            {classifyImagesSuccessMessage && (
              <StatusMessage
                type="success"
                message={classifyImagesSuccessMessage}
                onDismiss={() => setClassifyImagesSuccessMessage(null)}
              />
            )}
            {classifyImagesErrorMessage && (
              <StatusMessage
                type="error"
                message={classifyImagesErrorMessage}
                onRetry={handleClassifyImages}
              />
            )}
              {availableImages.length === 0 ? (
                <>
                  {imagesExtraction.isLoading ? (
                    <ExtractionLoadingState
                      toolName="images"
                      isGenerating={imagesExtraction.isLoading}
                    />
                  ) : (
                    <div className="rounded-lg border border-neutral-200 shadow-sm bg-neutral-50 p-8 text-center">
                      <div className="max-w-md mx-auto">
                        <ImageIcon className="w-12 h-12 text-neutral-400 mx-auto mb-4" strokeWidth={1.5} />
                        <p className="text-neutral-600 mb-2 font-medium">
                          No images collected yet
                        </p>
                        <p className="text-sm text-neutral-500 mb-6">
                          Property images will appear here once collected from the property website.
                        </p>
                        <button
                          onClick={handleExtractImages}
                          disabled={imagesExtraction.isLoading}
                          className="inline-flex items-center gap-2 px-6 py-3 bg-primary-500 text-white font-semibold rounded-lg hover:bg-primary-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-primary-300"
                        >
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
                            />
                          </svg>
                          Extract Images
                        </button>
                        {imagesExtraction.success && (
                          <StatusMessage
                            type="success"
                            message={imagesExtraction.success}
                            onDismiss={() => imagesExtraction.clearMessages()}
                          />
                        )}
                        {imagesExtraction.error && (
                          <StatusMessage
                            type="error"
                            message={imagesExtraction.error}
                            onRetry={imagesExtraction.retry}
                          />
                        )}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <>
                  {/* Visible Images - Grouped by Category */}
                  {visibleImages.length > 0 && (
                    <div className="space-y-8 mb-6">
                      {sortedVisibleCategories.map((category) => {
                        const categoryImages = visibleImagesGrouped[category];
                        if (categoryImages.length === 0) return null;
                        
                        // Calculate starting index for gallery
                        let galleryStartIndex = 0;
                        const categoryIndex = sortedVisibleCategories.indexOf(category);
                        for (let i = 0; i < categoryIndex; i++) {
                          galleryStartIndex += visibleImagesGrouped[sortedVisibleCategories[i]].length;
                        }
                        
                        return (
                          <div key={category} className="space-y-4">
                            <h3 className="text-xl font-semibold text-secondary-600 font-display flex items-center gap-2">
                              {getCategoryDisplayName(category)}
                              <span className="text-sm font-normal text-neutral-500">
                                ({categoryImages.length})
                              </span>
                            </h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                              {categoryImages.map((image, index) => (
                                <div
                                  key={image.id}
                                  className="relative aspect-video bg-neutral-100 rounded-lg overflow-hidden group cursor-pointer"
                                  onClick={() => {
                                    setGalleryIndex(galleryStartIndex + index);
                                    setGalleryOpen(true);
                                  }}
                                >
                                  <img
                                    src={image.image_url}
                                    alt={image.alt_text || 'Property image'}
                                    className="w-full h-full object-cover hover:opacity-90 transition-opacity"
                                    onError={(e) => {
                                      // Mark image as unavailable and hide it
                                      markImageAsUnavailable(image.id);
                                      const target = e.target as HTMLImageElement;
                                      target.style.display = 'none';
                                      const parent = target.parentElement;
                                      if (parent) {
                                        parent.style.display = 'none';
                                      }
                                    }}
                                  />
                                  <div className="absolute top-2 left-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                      onClick={(e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        toggleImageVisibility(image.id, image.is_hidden);
                                      }}
                                      className="bg-black/70 hover:bg-black/90 text-white p-2 rounded-full transition-all focus:outline-none focus:ring-4 focus:ring-primary-300"
                                      title="Hide image"
                                      aria-label="Hide image"
                                    >
                                      <EyeIcon className="w-4 h-4" />
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Hidden Images Section */}
                  {hiddenImages.length > 0 && (
                    <div className="mt-6">
                      <button
                        onClick={() => setShowHiddenImages(!showHiddenImages)}
                        className="flex items-center gap-2 text-lg font-semibold text-neutral-900 mb-4 hover:text-primary-500 transition-colors focus:outline-none focus:ring-4 focus:ring-primary-300 rounded-lg px-2 py-1"
                      >
                        <span>Hidden Images ({hiddenImages.length})</span>
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          strokeWidth={2}
                          stroke="currentColor"
                          className={`w-5 h-5 transition-transform ${showHiddenImages ? 'rotate-180' : ''}`}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                          />
                        </svg>
                      </button>
                      {showHiddenImages && (
                        <div className="space-y-8">
                          {sortedHiddenCategories.map((category) => {
                            const categoryImages = hiddenImagesGrouped[category];
                            if (categoryImages.length === 0) return null;
                            
                            // Calculate starting index for gallery (after all visible images)
                            let galleryStartIndex = allVisibleImagesForGallery.length;
                            const categoryIndex = sortedHiddenCategories.indexOf(category);
                            for (let i = 0; i < categoryIndex; i++) {
                              galleryStartIndex += hiddenImagesGrouped[sortedHiddenCategories[i]].length;
                            }
                            
                            return (
                              <div key={category} className="space-y-4">
                                <h3 className="text-xl font-semibold text-secondary-600 font-display flex items-center gap-2 opacity-60">
                                  {getCategoryDisplayName(category)}
                                  <span className="text-sm font-normal text-neutral-500">
                                    ({categoryImages.length})
                                  </span>
                                </h3>
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                                  {categoryImages.map((image, index) => (
                                    <div
                                      key={image.id}
                                      className="relative aspect-video bg-neutral-100 rounded-lg overflow-hidden group opacity-60 cursor-pointer"
                                      onClick={() => {
                                        setGalleryIndex(galleryStartIndex + index);
                                        setGalleryOpen(true);
                                      }}
                                    >
                                      <img
                                        src={image.image_url}
                                        alt={image.alt_text || 'Property image'}
                                        className="w-full h-full object-cover hover:opacity-90 transition-opacity"
                                        onError={(e) => {
                                          // Mark image as unavailable and hide it
                                          markImageAsUnavailable(image.id);
                                          const target = e.target as HTMLImageElement;
                                          target.style.display = 'none';
                                          const parent = target.parentElement;
                                          if (parent) {
                                            parent.style.display = 'none';
                                          }
                                        }}
                                      />
                                      <div className="absolute top-2 left-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                          onClick={(e) => {
                                            e.preventDefault();
                                            e.stopPropagation();
                                            toggleImageVisibility(image.id, image.is_hidden);
                                          }}
                                          className="bg-black/70 hover:bg-black/90 text-white p-2 rounded-full transition-all focus:outline-none focus:ring-4 focus:ring-primary-300"
                                          title="Show image"
                                          aria-label="Show image"
                                        >
                                          <EyeSlashIcon className="w-4 h-4" />
                                        </button>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
          </div>

          {/* Amenities Card */}
          <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md transition-all duration-300 hover:shadow-lg">
            <h2 className="text-2xl font-bold text-secondary-700 mb-4 font-display flex items-center gap-2">
              <Star className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
              Amenities
            </h2>
            {amenities && amenities.amenities_data ? (
              <div className="grid grid-cols-2 gap-6">
                {/* Building Amenities */}
                <div>
                  <h3 className="text-lg font-semibold text-neutral-900 mb-3">
                    Building
                  </h3>
                  {amenities.amenities_data.building_amenities && amenities.amenities_data.building_amenities.length > 0 ? (
                    <ul className="space-y-1">
                      {amenities.amenities_data.building_amenities.map((amenity, index) => (
                        <li
                          key={index}
                          className="text-base text-neutral-900 leading-relaxed"
                        >
                          • {amenity.name}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-neutral-800">
                      No building amenities listed.
                    </p>
                  )}
                </div>

                {/* Apartment Amenities */}
                <div>
                  <h3 className="text-lg font-semibold text-neutral-900 mb-3">
                    Apartment
                  </h3>
                  {amenities.amenities_data.apartment_amenities && amenities.amenities_data.apartment_amenities.length > 0 ? (
                    <ul className="space-y-1">
                      {amenities.amenities_data.apartment_amenities.map((amenity, index) => (
                        <li
                          key={index}
                          className="text-base text-neutral-900 leading-relaxed"
                        >
                          • {amenity.name}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-neutral-800">
                      No apartment amenities listed.
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <>
                {amenitiesExtraction.isLoading ? (
                  <ExtractionLoadingState
                    toolName="amenities"
                    isGenerating={amenitiesExtraction.isLoading}
                  />
                ) : (
                  <div className="rounded-lg border border-neutral-200 shadow-sm bg-neutral-50 p-8 text-center">
                    <div className="max-w-md mx-auto">
                      <Star className="w-12 h-12 text-neutral-400 mx-auto mb-4" strokeWidth={1.5} />
                      <p className="text-neutral-600 mb-2 font-medium">
                        No amenities collected yet
                      </p>
                      <p className="text-sm text-neutral-500 mb-6">
                        Building and apartment amenities will appear here once collected from the property website.
                      </p>
                      <button
                        onClick={handleExtractAmenities}
                        disabled={amenitiesExtraction.isLoading}
                        className="inline-flex items-center gap-2 px-6 py-3 bg-primary-500 text-white font-semibold rounded-lg hover:bg-primary-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-primary-300"
                      >
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
                          />
                        </svg>
                        Extract Amenities
                      </button>
                      {amenitiesExtraction.success && (
                        <StatusMessage
                          type="success"
                          message={amenitiesExtraction.success}
                          onDismiss={() => amenitiesExtraction.clearMessages()}
                        />
                      )}
                      {amenitiesExtraction.error && (
                        <StatusMessage
                          type="error"
                          message={amenitiesExtraction.error}
                          onRetry={amenitiesExtraction.retry}
                        />
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Social Media Posts Section */}
          <SocialPostsSection propertyId={propertyId} />

          {/* Reviews Section */}
          <ReviewsSection propertyId={propertyId} />

          {/* Competitors Section */}
          <CompetitorsSection propertyId={propertyId} />
        </div>
      </div>

      {/* Image Gallery Modal */}
      {galleryOpen && (
        <ImageGallery
          images={[...allVisibleImagesForGallery, ...allHiddenImagesForGallery]}
          initialIndex={galleryIndex}
          onClose={() => setGalleryOpen(false)}
          onImageUpdate={(updatedImage) => {
            setImages((prevImages) =>
              prevImages.map((img) =>
                img.id === updatedImage.id ? updatedImage : img
              )
            );
          }}
        />
      )}

    </div>
  );
}

