'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { MapPin } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { Competitor } from '@/lib/types';
import type { RealtimeChannel } from '@supabase/supabase-js';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/app/components/ui/table';

// #region agent log
const DEBUG_LOG_PATH = '/Users/rajivchopra/Property Onboarding Agent/.cursor/debug-layout.log';
const logDebug = (data: any) => {
  try {
    fetch('http://127.0.0.1:7242/ingest/11ae704d-3f84-45d9-821d-70932713d32a', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...data, timestamp: Date.now(), sessionId: 'layout-debug' })
    }).catch(() => {});
  } catch (e) {}
};
// #endregion

interface CompetitorsSectionProps {
  propertyId: string;
  minReviewCount?: number;
}

export default function CompetitorsSection({ propertyId, minReviewCount = 10 }: CompetitorsSectionProps) {
  const [topCompetitors, setTopCompetitors] = useState<Competitor[]>([]);
  const [allTopCompetitors, setAllTopCompetitors] = useState<Competitor[]>([]);
  const [closestCompetitors, setClosestCompetitors] = useState<Competitor[]>([]);
  const [allClosestCompetitors, setAllClosestCompetitors] = useState<Competitor[]>([]);
  const [watchedCompetitors, setWatchedCompetitors] = useState<Competitor[]>([]);
  const [watchedCompetitorIds, setWatchedCompetitorIds] = useState<Set<string>>(new Set());
  const [topCompetitorsExpanded, setTopCompetitorsExpanded] = useState(false);
  const [closestCompetitorsExpanded, setClosestCompetitorsExpanded] = useState(false);
  const [watchlistExpanded, setWatchlistExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [watchlistLoading, setWatchlistLoading] = useState<Set<string>>(new Set());
  const [isGeneratingCompetitors, setIsGeneratingCompetitors] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [generationSuccess, setGenerationSuccess] = useState<string | null>(null);
  
  // Realtime subscription channel ref
  const realtimeChannelRef = useRef<RealtimeChannel | null>(null);
  
  // Refs for measuring layout shifts
  const topCompetitorsHeaderRef = useRef<HTMLDivElement>(null);
  const topCompetitorsTableRef = useRef<HTMLDivElement>(null);
  const topCompetitorsTitleRef = useRef<HTMLHeadingElement>(null);
  const topCompetitorsSubtitleRef = useRef<HTMLParagraphElement>(null);
  const topCompetitorsButtonRef = useRef<HTMLButtonElement>(null);

  // Fetch watched competitor IDs
  useEffect(() => {
    async function fetchWatchedCompetitorIds() {
      try {
        const { data, error } = await supabase
          .from('competitor_watchlist')
          .select('competitor_id')
          .eq('property_id', propertyId);

        if (error) {
          console.error('Error fetching watched competitor IDs:', error);
          return;
        }

        const ids = new Set(data?.map(item => item.competitor_id) || []);
        setWatchedCompetitorIds(ids);
      } catch (err) {
        console.error('Error fetching watched competitor IDs:', err);
      }
    }

    if (propertyId) {
      fetchWatchedCompetitorIds();
    }
  }, [propertyId]);

  // Fetch watched competitors
  useEffect(() => {
    async function fetchWatchedCompetitors() {
      if (watchedCompetitorIds.size === 0) {
        setWatchedCompetitors([]);
        return;
      }

      try {
        const { data, error } = await supabase
          .from('property_competitors')
          .select('*')
          .eq('property_id', propertyId)
          .in('id', Array.from(watchedCompetitorIds));

        if (error) {
          console.error('Error fetching watched competitors:', error);
          setWatchedCompetitors([]);
        } else {
          // Sort by rating descending, then review count descending
          const sorted = (data || []).sort((a, b) => {
            if (a.rating !== b.rating) {
              return (b.rating || 0) - (a.rating || 0);
            }
            return (b.review_count || 0) - (a.review_count || 0);
          });
          setWatchedCompetitors(sorted);
        }
      } catch (err) {
        console.error('Error fetching watched competitors:', err);
        setWatchedCompetitors([]);
      }
    }

    if (propertyId && watchedCompetitorIds.size > 0) {
      fetchWatchedCompetitors();
    } else {
      setWatchedCompetitors([]);
    }
  }, [propertyId, watchedCompetitorIds]);

  // Fetch competitors based on selected radius
  const fetchCompetitors = useCallback(async () => {
    if (!propertyId) return;
    
    try {
      setLoading(true);

      // Fetch top-rated competitors within 5 miles (all, no limit)
      const { data: allTopData, error: allTopError } = await supabase
        .from('property_competitors')
        .select('*')
        .eq('property_id', propertyId)
        .not('rating', 'is', null)
        .not('review_count', 'is', null)
        .not('distance_miles', 'is', null)
        .lte('distance_miles', 5)
        .gte('review_count', minReviewCount)
        .order('rating', { ascending: false })
        .order('review_count', { ascending: false });

      if (allTopError) {
        console.error('Error fetching all top competitors:', allTopError);
        setAllTopCompetitors([]);
      } else {
        setAllTopCompetitors(allTopData || []);
      }

      // Fetch closest competitors within 1.5 miles (all, no limit)
      const { data: allClosestData, error: allClosestError } = await supabase
        .from('property_competitors')
        .select('*')
        .eq('property_id', propertyId)
        .not('distance_miles', 'is', null)
        .lte('distance_miles', 1.5)
        .order('distance_miles', { ascending: true });

      if (allClosestError) {
        console.error('Error fetching all closest competitors:', allClosestError);
        setAllClosestCompetitors([]);
      } else {
        setAllClosestCompetitors(allClosestData || []);
      }
    } catch (err) {
      console.error('Error fetching competitors:', err);
      setAllTopCompetitors([]);
      setAllClosestCompetitors([]);
    } finally {
      setLoading(false);
    }
  }, [propertyId, minReviewCount]);

  useEffect(() => {
    if (propertyId) {
      fetchCompetitors();
    }
  }, [propertyId, fetchCompetitors]);

  // Set up Realtime subscription when generating competitors
  useEffect(() => {
    if (!propertyId || !isGeneratingCompetitors) {
      // Clean up subscription if not generating
      if (realtimeChannelRef.current) {
        supabase.removeChannel(realtimeChannelRef.current);
        realtimeChannelRef.current = null;
      }
      return;
    }

    // Create subscription channel
    const channel = supabase
      .channel(`competitors:${propertyId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'property_competitors',
          filter: `property_id=eq.${propertyId}`,
        },
        (payload) => {
          console.log('New competitor detected via Realtime:', payload);
          // Refresh competitors when new ones are inserted
          fetchCompetitors();
        }
      )
      .subscribe((status) => {
        console.log('Realtime subscription status:', status);
      });

    realtimeChannelRef.current = channel;

    // Cleanup function
    return () => {
      if (realtimeChannelRef.current) {
        supabase.removeChannel(realtimeChannelRef.current);
        realtimeChannelRef.current = null;
      }
    };
  }, [propertyId, isGeneratingCompetitors, fetchCompetitors]);

  // Check if competitors have appeared and stop generation state
  useEffect(() => {
    if (
      isGeneratingCompetitors &&
      (allTopCompetitors.length > 0 || allClosestCompetitors.length > 0)
    ) {
      // Competitors have appeared, stop showing generation state
      setIsGeneratingCompetitors(false);
      setGenerationSuccess(null);
      
      // Clean up subscription
      if (realtimeChannelRef.current) {
        supabase.removeChannel(realtimeChannelRef.current);
        realtimeChannelRef.current = null;
      }
    }
  }, [isGeneratingCompetitors, allTopCompetitors.length, allClosestCompetitors.length]);

  // Update displayed competitors based on expanded state
  useEffect(() => {
    // #region agent log
    const beforeState = {
      expanded: topCompetitorsExpanded,
      allCount: allTopCompetitors.length,
      displayedCount: topCompetitors.length,
    };
    if (topCompetitorsHeaderRef.current) {
      const rect = topCompetitorsHeaderRef.current.getBoundingClientRect();
      logDebug({
        location: 'CompetitorsSection.tsx:149',
        message: 'Before topCompetitors state update',
        data: { ...beforeState, headerRect: { width: rect.width, height: rect.height, top: rect.top, left: rect.left } },
        hypothesisId: 'A'
      });
    }
    // #endregion
    
    setTopCompetitors(topCompetitorsExpanded ? allTopCompetitors : allTopCompetitors.slice(0, 5));
    
    // #region agent log
    setTimeout(() => {
      if (topCompetitorsHeaderRef.current) {
        const rect = topCompetitorsHeaderRef.current.getBoundingClientRect();
        logDebug({
          location: 'CompetitorsSection.tsx:162',
          message: 'After topCompetitors state update',
          data: { 
            expanded: topCompetitorsExpanded,
            displayedCount: topCompetitorsExpanded ? allTopCompetitors.length : 5,
            headerRect: { width: rect.width, height: rect.height, top: rect.top, left: rect.left },
            headerOffsetTop: topCompetitorsHeaderRef.current.offsetTop,
            headerOffsetLeft: topCompetitorsHeaderRef.current.offsetLeft
          },
          hypothesisId: 'A'
        });
      }
      if (topCompetitorsTableRef.current) {
        const rect = topCompetitorsTableRef.current.getBoundingClientRect();
        logDebug({
          location: 'CompetitorsSection.tsx:175',
          message: 'Table container dimensions after update',
          data: {
            tableRect: { width: rect.width, height: rect.height, top: rect.top, left: rect.left },
            tableOffsetTop: topCompetitorsTableRef.current.offsetTop
          },
          hypothesisId: 'B'
        });
      }
    }, 0);
    // #endregion
  }, [topCompetitorsExpanded, allTopCompetitors]);

  useEffect(() => {
    setClosestCompetitors(closestCompetitorsExpanded ? allClosestCompetitors : allClosestCompetitors.slice(0, 5));
  }, [closestCompetitorsExpanded, allClosestCompetitors]);

  const toggleWatchlist = async (competitor: Competitor, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent row click
    const competitorId = competitor.id;
    const isWatched = watchedCompetitorIds.has(competitorId);

    setWatchlistLoading(prev => new Set(prev).add(competitorId));

    try {
      if (isWatched) {
        // Remove from watchlist
        const { error } = await supabase
          .from('competitor_watchlist')
          .delete()
          .eq('property_id', propertyId)
          .eq('competitor_id', competitorId);

        if (error) {
          console.error('Error removing from watchlist:', error);
          return;
        }

        setWatchedCompetitorIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(competitorId);
          return newSet;
        });
      } else {
        // Add to watchlist
        const { error } = await supabase
          .from('competitor_watchlist')
          .insert({
            property_id: propertyId,
            competitor_id: competitorId,
          });

        if (error) {
          console.error('Error adding to watchlist:', error);
          return;
        }

        setWatchedCompetitorIds(prev => new Set(prev).add(competitorId));
      }
    } catch (err) {
      console.error('Error toggling watchlist:', err);
    } finally {
      setWatchlistLoading(prev => {
        const newSet = new Set(prev);
        newSet.delete(competitorId);
        return newSet;
      });
    }
  };

  const renderStars = (rating: number | null) => {
    if (!rating) return null;
    const roundedRating = Math.round(rating);
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={`w-5 h-5 ${
              star <= roundedRating
                ? 'text-yellow-400 fill-current'
                : 'text-neutral-300'
            }`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
    );
  };

  const renderWatchlistStar = (competitor: Competitor) => {
    const isWatched = watchedCompetitorIds.has(competitor.id);
    const isLoading = watchlistLoading.has(competitor.id);

    return (
      <button
        onClick={(e) => toggleWatchlist(competitor, e)}
        disabled={isLoading}
        className="p-2 hover:bg-neutral-100 rounded transition-colors disabled:opacity-50 -m-2"
        title={isWatched ? 'Remove from watchlist' : 'Add to watchlist'}
      >
        {isWatched ? (
          <svg
            className="w-5 h-5 text-yellow-400 fill-current"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ) : (
          <svg
            className="w-5 h-5 text-neutral-400 hover:text-yellow-400 transition-colors"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
            />
          </svg>
        )}
      </button>
    );
  };

  const formatDistance = (distanceMiles: number | null) => {
    if (distanceMiles === null) return '—';
    return `${distanceMiles.toFixed(1)} mi`;
  };

  const formatAddress = (competitor: Competitor) => {
    const parts = [
      competitor.street_address,
      competitor.city,
      competitor.state,
      competitor.zip_code,
    ].filter(Boolean);
    
    if (parts.length > 0) {
      return parts.join(', ');
    }
    
    if (competitor.address) {
      return competitor.address;
    }
    
    return '—';
  };

  const getGoogleMapsUrl = (competitor: Competitor): string | null => {
    if (competitor.google_maps_url) {
      return competitor.google_maps_url;
    }
    
    if (competitor.place_id) {
      return `https://www.google.com/maps/place/?q=place_id:${competitor.place_id}`;
    }
    
    const address = formatAddress(competitor);
    if (address && address !== '—') {
      return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`;
    }
    
    return null;
  };

  const handleGoogleMapsClick = (competitor: Competitor, e: React.MouseEvent) => {
    e.stopPropagation();
    const url = getGoogleMapsUrl(competitor);
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleWebsiteClick = (competitor: Competitor, e: React.MouseEvent) => {
    e.stopPropagation();
    if (competitor.website) {
      window.open(competitor.website, '_blank', 'noopener,noreferrer');
    }
  };

  const handleGenerateCompetitors = async () => {
    if (!propertyId || isGeneratingCompetitors) return;
    
    try {
      setIsGeneratingCompetitors(true);
      setGenerationError(null);
      setGenerationSuccess(null);

      const response = await fetch(`/api/properties/${propertyId}/extract/competitors`, {
        method: 'POST',
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Failed to generate competitors');
      }

      setGenerationSuccess('Competitor data generation started! This may take a few minutes.');
      
      // Note: isGeneratingCompetitors will be set to false automatically when competitors appear
      // via the Realtime subscription and the useEffect that checks for competitor data
    } catch (error: any) {
      console.error('Error generating competitors:', error);
      setGenerationError(error.message || 'Failed to generate competitors. Please try again.');
      setIsGeneratingCompetitors(false);
      setTimeout(() => setGenerationError(null), 5000);
    }
  };

  const renderCompetitorTable = (
    competitors: Competitor[],
    title: string,
    subtitle: string,
    allCompetitors: Competitor[],
    expanded: boolean,
    onToggleExpand: () => void,
    showWatchlistStar: boolean = true,
    showEmptyState: boolean = false
  ) => {
    if (competitors.length === 0 && !showEmptyState) {
      return null;
    }

    if (competitors.length === 0 && showEmptyState) {
      return (
        <div className="mb-8 last:mb-0">
          <h3 className="text-xl font-bold text-secondary-700 mb-2 font-display">
            {title}
          </h3>
          <p className="text-sm text-neutral-600 mb-4">
            {subtitle}
          </p>
          <Card className="shadow-sm bg-neutral-50">
            <CardContent className="p-8 text-center">
            <div className="max-w-md mx-auto">
              <svg
                className="w-12 h-12 text-neutral-400 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <p className="text-neutral-600 mb-2 font-medium">
                No competitors found within 1.5 miles
              </p>
              <p className="text-sm text-neutral-500">
                Try checking the Top Competitors section for highly-rated properties within 5 miles.
              </p>
            </div>
          </CardContent>
        </Card>
        </div>
      );
    }

    const hasMore = allCompetitors.length > 5;

    // Create wrapped toggle function with logging
    const wrappedToggle = () => {
      // #region agent log
      const isTopCompetitors = title === 'Top Competitors';
      if (isTopCompetitors && topCompetitorsHeaderRef.current) {
        const headerRect = topCompetitorsHeaderRef.current.getBoundingClientRect();
        const headerStyle = window.getComputedStyle(topCompetitorsHeaderRef.current);
        const parentEl = topCompetitorsHeaderRef.current.parentElement;
        const parentRect = parentEl?.getBoundingClientRect();
        const parentStyle = parentEl ? window.getComputedStyle(parentEl) : null;
        const prevSibling = parentEl?.previousElementSibling;
        const prevSiblingRect = prevSibling?.getBoundingClientRect();
        
        // Measure individual header elements
        const titleRect = topCompetitorsTitleRef.current?.getBoundingClientRect();
        const subtitleRect = topCompetitorsSubtitleRef.current?.getBoundingClientRect();
        const buttonRect = topCompetitorsButtonRef.current?.getBoundingClientRect();
        const buttonContainerRect = topCompetitorsButtonRef.current?.parentElement?.getBoundingClientRect();
        
        logDebug({
          location: 'CompetitorsSection.tsx:398',
          message: 'Toggle button clicked - BEFORE',
          data: {
            title,
            expanded,
            competitorsCount: competitors.length,
            allCount: allCompetitors.length,
            headerRect: { width: headerRect.width, height: headerRect.height, top: headerRect.top, left: headerRect.left },
            headerStyle: { marginBottom: headerStyle.marginBottom, padding: headerStyle.padding },
            titleRect: titleRect ? { width: titleRect.width, height: titleRect.height, top: titleRect.top, left: titleRect.left } : null,
            subtitleRect: subtitleRect ? { width: subtitleRect.width, height: subtitleRect.height, top: subtitleRect.top, left: subtitleRect.left } : null,
            buttonRect: buttonRect ? { width: buttonRect.width, height: buttonRect.height, top: buttonRect.top, left: buttonRect.left } : null,
            buttonContainerRect: buttonContainerRect ? { width: buttonContainerRect.width, height: buttonContainerRect.height, top: buttonContainerRect.top, left: buttonContainerRect.left } : null,
            parentRect: parentRect ? { width: parentRect.width, height: parentRect.height, top: parentRect.top, left: parentRect.left } : null,
            parentStyle: parentStyle ? { marginBottom: parentStyle.marginBottom, padding: parentStyle.padding } : null,
            prevSiblingRect: prevSiblingRect ? { top: prevSiblingRect.top, height: prevSiblingRect.height } : null,
            scrollY: window.scrollY,
            pageYOffset: window.pageYOffset
          },
          hypothesisId: 'C'
        });
      }
      // #endregion
      
      onToggleExpand();
      
      // #region agent log
      setTimeout(() => {
        if (isTopCompetitors && topCompetitorsHeaderRef.current) {
          const headerRect = topCompetitorsHeaderRef.current.getBoundingClientRect();
          const parentEl = topCompetitorsHeaderRef.current.parentElement;
          const parentRect = parentEl?.getBoundingClientRect();
          const prevSibling = parentEl?.previousElementSibling;
          const prevSiblingRect = prevSibling?.getBoundingClientRect();
          
          // Measure individual header elements
          const titleRect = topCompetitorsTitleRef.current?.getBoundingClientRect();
          const subtitleRect = topCompetitorsSubtitleRef.current?.getBoundingClientRect();
          const buttonRect = topCompetitorsButtonRef.current?.getBoundingClientRect();
          const buttonContainerRect = topCompetitorsButtonRef.current?.parentElement?.getBoundingClientRect();
          
          logDebug({
            location: 'CompetitorsSection.tsx:420',
            message: 'Toggle button clicked - AFTER',
            data: {
              title,
              newExpanded: !expanded,
              headerRect: { width: headerRect.width, height: headerRect.height, top: headerRect.top, left: headerRect.left },
              headerOffsetTop: topCompetitorsHeaderRef.current.offsetTop,
              titleRect: titleRect ? { width: titleRect.width, height: titleRect.height, top: titleRect.top, left: titleRect.left } : null,
              subtitleRect: subtitleRect ? { width: subtitleRect.width, height: subtitleRect.height, top: subtitleRect.top, left: subtitleRect.left } : null,
              buttonRect: buttonRect ? { width: buttonRect.width, height: buttonRect.height, top: buttonRect.top, left: buttonRect.left } : null,
              buttonContainerRect: buttonContainerRect ? { width: buttonContainerRect.width, height: buttonContainerRect.height, top: buttonContainerRect.top, left: buttonContainerRect.left } : null,
              parentRect: parentRect ? { width: parentRect.width, height: parentRect.height, top: parentRect.top, left: parentRect.left } : null,
              prevSiblingRect: prevSiblingRect ? { top: prevSiblingRect.top, height: prevSiblingRect.height } : null,
              scrollY: window.scrollY,
              pageYOffset: window.pageYOffset
            },
            hypothesisId: 'C'
          });
        }
      }, 100);
      // #endregion
    };

    return (
      <div className="mb-8 last:mb-0">
        <div 
          ref={title === 'Top Competitors' ? topCompetitorsHeaderRef : null}
          className="flex items-center justify-between mb-2"
        >
          <div className="flex-1 min-w-0">
            <h3 
              ref={title === 'Top Competitors' ? topCompetitorsTitleRef : null}
              className="text-xl font-bold text-secondary-700 font-display"
            >
              {title}
            </h3>
            <p 
              ref={title === 'Top Competitors' ? topCompetitorsSubtitleRef : null}
              className="text-sm text-neutral-600 mt-1"
            >
              {subtitle}
            </p>
          </div>
          {hasMore && (
            <div className="flex-shrink-0 ml-4 text-right" style={{ width: '140px' }}>
              <button
                ref={title === 'Top Competitors' ? topCompetitorsButtonRef : null}
                onClick={wrappedToggle}
                className="text-sm text-secondary-600 hover:text-secondary-700 font-medium transition-colors whitespace-nowrap w-full"
              >
                {expanded ? 'Show less' : `Show all (${allCompetitors.length})`}
              </button>
            </div>
          )}
        </div>

        <div 
          ref={title === 'Top Competitors' ? topCompetitorsTableRef : null}
          className="overflow-x-auto rounded-lg shadow-sm"
        >
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50">
                {showWatchlistStar && (
                  <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide w-12">
                  </th>
                )}
                <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                  Name
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                  Rating
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                  Reviews
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                  Distance
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                  Address
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide w-24">
                  Links
                </th>
              </tr>
            </thead>
            <tbody>
              {competitors.map((competitor) => {
                const googleMapsUrl = getGoogleMapsUrl(competitor);
                const hasWebsite = !!competitor.website;

                return (
                  <tr
                    key={competitor.id}
                    className="border-b border-neutral-100 transition-all"
                  >
                    {showWatchlistStar && (
                      <td className="py-4 px-4">
                        {renderWatchlistStar(competitor)}
                      </td>
                    )}
                    {/* Name Column */}
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-neutral-900">
                          {competitor.competitor_name}
                        </span>
                      </div>
                    </td>

                    {/* Rating Column */}
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        {renderStars(competitor.rating)}
                        {competitor.rating && (
                          <span className="text-sm font-medium text-neutral-700">
                            {competitor.rating.toFixed(1)}/5
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Reviews Column */}
                    <td className="py-4 px-4">
                      {competitor.review_count !== null ? (
                        <span className="text-sm text-neutral-700">
                          {competitor.review_count.toLocaleString()}
                        </span>
                      ) : (
                        <span className="text-sm text-neutral-400">—</span>
                      )}
                    </td>

                    {/* Distance Column */}
                    <td className="py-4 px-4">
                      <span className="text-sm text-neutral-700">
                        {formatDistance(competitor.distance_miles)}
                      </span>
                    </td>

                    {/* Address Column */}
                    <td className="py-4 px-4">
                      <span className="text-sm text-neutral-700">
                        {formatAddress(competitor)}
                      </span>
                    </td>

                    {/* Links Column */}
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        {googleMapsUrl && (
                          <button
                            onClick={(e) => handleGoogleMapsClick(competitor, e)}
                            className="p-1.5 hover:bg-neutral-100 rounded transition-colors text-neutral-600 hover:text-neutral-900 cursor-pointer"
                            title="Google Maps"
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
                                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                              />
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                              />
                            </svg>
                          </button>
                        )}
                        {hasWebsite && (
                          <button
                            onClick={(e) => handleWebsiteClick(competitor, e)}
                            className="p-1.5 hover:bg-neutral-100 rounded transition-colors text-neutral-600 hover:text-neutral-900 cursor-pointer"
                            title="Website"
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
                                d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
                              />
                            </svg>
                          </button>
                        )}
                        {!googleMapsUrl && !hasWebsite && (
                          <span className="text-sm text-neutral-400">—</span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const displayedWatchedCompetitors = watchlistExpanded 
    ? watchedCompetitors 
    : watchedCompetitors.slice(0, 5);

  // Show loading state when initial fetch is loading OR when generating competitors and no data exists yet
  const showLoadingState = loading || (isGeneratingCompetitors && allTopCompetitors.length === 0 && allClosestCompetitors.length === 0);

  if (showLoadingState) {
    return (
      <Card>
        <CardContent className="p-8">
        {isGeneratingCompetitors ? (
          // Generation loading state
          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-6">
              {/* Animated Map Pin */}
              <div className="absolute inset-0 flex items-center justify-center">
                <MapPin className="w-16 h-16 text-primary-500 animate-pulse" strokeWidth={1.5} />
              </div>
              {/* Spinning Ring */}
              <svg
                className="absolute inset-0 w-24 h-24 transform -rotate-90 animate-spin"
                viewBox="0 0 100 100"
              >
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="4"
                  strokeLinecap="round"
                  strokeDasharray="283"
                  strokeDashoffset="70"
                  className="text-primary-500"
                />
              </svg>
            </div>
            <div className="space-y-2">
              <p className="text-lg font-semibold text-neutral-700">
                Generating Competitor Data
              </p>
              <p className="text-sm text-neutral-500">
                Finding nearby properties and analyzing competitors...
              </p>
              <div className="flex items-center justify-center gap-2 mt-4">
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" style={{ animationDelay: '0s' }}></div>
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        ) : (
          // Initial loading state
          <div className="text-center text-neutral-600">Loading competitors...</div>
        )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="transition-all duration-300 hover:shadow-lg">
      <CardHeader>
        <CardTitle className="text-2xl font-display text-secondary-700 flex items-center gap-2">
          <MapPin className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
          Competitors
        </CardTitle>
      </CardHeader>
      <CardContent>

      {/* Empty State - Show when no competitors exist in any category */}
      {allTopCompetitors.length === 0 && allClosestCompetitors.length === 0 && watchedCompetitors.length === 0 ? (
        <Card className="shadow-sm bg-neutral-50">
          <CardContent className="p-8 text-center">
            <div className="max-w-md mx-auto">
            {isGeneratingCompetitors ? (
              // Loading State
              <div className="py-8">
                <div className="relative w-24 h-24 mx-auto mb-6">
                  {/* Animated Map Pin */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <MapPin className="w-16 h-16 text-primary-500 animate-pulse" strokeWidth={1.5} />
                  </div>
                  {/* Spinning Ring */}
                  <svg
                    className="absolute inset-0 w-24 h-24 transform -rotate-90 animate-spin"
                    viewBox="0 0 100 100"
                  >
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="4"
                      strokeLinecap="round"
                      strokeDasharray="283"
                      strokeDashoffset="70"
                      className="text-primary-500"
                    />
                  </svg>
                </div>
                <div className="space-y-2">
                  <p className="text-lg font-semibold text-neutral-700">
                    Generating Competitor Data
                  </p>
                  <p className="text-sm text-neutral-500">
                    Finding nearby properties and analyzing competitors...
                  </p>
                  <div className="flex items-center justify-center gap-2 mt-4">
                    <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" style={{ animationDelay: '0s' }}></div>
                    <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            ) : (
              // Default Empty State
              <>
                <MapPin className="w-12 h-12 text-neutral-400 mx-auto mb-4" strokeWidth={1.5} />
                <p className="text-neutral-600 mb-2 font-medium">
                  No competitors collected yet
                </p>
                <p className="text-sm text-neutral-500 mb-6">
                  Competitor information including nearby properties, ratings, and reviews will appear here once collected.
                </p>
                {generationSuccess && (
                  <div className="mb-4 p-3 bg-green-50 rounded-lg shadow-sm">
                    <p className="text-sm text-green-700">{generationSuccess}</p>
                  </div>
                )}
                {generationError && (
                  <div className="mb-4 p-3 bg-red-50 rounded-lg shadow-sm">
                    <p className="text-sm text-red-700">{generationError}</p>
                  </div>
                )}
                <button
                  onClick={handleGenerateCompetitors}
                  disabled={isGeneratingCompetitors}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-primary-500 text-white font-semibold rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-primary-300"
                >
                  <MapPin className="w-5 h-5" strokeWidth={2} />
                  Generate Competitor Data
                </button>
              </>
            )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <>

      {/* Watchlist Section */}
      {watchedCompetitors.length > 0 ? (
        renderCompetitorTable(
          displayedWatchedCompetitors,
          'Watchlist',
          `Competitors you're watching (${watchedCompetitors.length} total)`,
          watchedCompetitors,
          watchlistExpanded,
          () => setWatchlistExpanded(!watchlistExpanded),
          true // Show watchlist star so users can remove from watchlist
        )
      ) : (
        <div className="mb-8 last:mb-0">
          <h3 className="text-xl font-bold text-secondary-700 mb-2 font-display">
            Watchlist
          </h3>
          <p className="text-sm text-neutral-600 mb-4">
            Save competitors you want to track
          </p>
          <Card className="shadow-sm bg-neutral-50">
            <CardContent className="p-8 text-center">
            <div className="max-w-md mx-auto">
              <svg
                className="w-12 h-12 text-neutral-400 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                />
              </svg>
              <p className="text-neutral-600 mb-2 font-medium">
                Your watchlist is empty
              </p>
              <p className="text-sm text-neutral-500">
                Click the star icon next to any competitor below to add them to your watchlist for easy tracking.
              </p>
            </div>
          </CardContent>
        </Card>
        </div>
      )}

      {/* Top Competitors Table */}
      {renderCompetitorTable(
        topCompetitors,
        'Top Competitors',
        `Top ${allTopCompetitors.length} highest-rated competitors within 5 miles (minimum ${minReviewCount} reviews)`,
        allTopCompetitors,
        topCompetitorsExpanded,
        () => setTopCompetitorsExpanded(!topCompetitorsExpanded)
      )}

      {/* Closest Competitors Table */}
      {renderCompetitorTable(
        closestCompetitors,
        'Closest Competitors',
        'Competitors within 1.5 miles (ranked by distance)',
        allClosestCompetitors,
        closestCompetitorsExpanded,
        () => setClosestCompetitorsExpanded(!closestCompetitorsExpanded),
        true,
        true // Show empty state for closest competitors
      )}
        </>
      )}
      </CardContent>
    </Card>
  );
}
