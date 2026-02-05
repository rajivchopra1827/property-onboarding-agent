'use client';

import { useEffect, useState, Fragment, useCallback } from 'react';
import { MessageSquare } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { PropertyReview, PropertyReviewsSummary } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/app/components/ui/table';
import EmptyState from './EmptyState';

interface ReviewsSectionProps {
  propertyId: string;
}

export default function ReviewsSection({ propertyId }: ReviewsSectionProps) {
  const [reviewsSummary, setReviewsSummary] = useState<PropertyReviewsSummary | null>(null);
  const [allPositiveReviews, setAllPositiveReviews] = useState<PropertyReview[]>([]);
  const [allNegativeReviews, setAllNegativeReviews] = useState<PropertyReview[]>([]);
  const [positiveReviewsExpanded, setPositiveReviewsExpanded] = useState(false);
  const [negativeReviewsExpanded, setNegativeReviewsExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sentimentLoading, setSentimentLoading] = useState(false);
  const [expandedReviews, setExpandedReviews] = useState<Set<string>>(new Set());
  const [isCollectingReviews, setIsCollectingReviews] = useState(false);
  const [collectionError, setCollectionError] = useState<string | null>(null);
  const [collectionSuccess, setCollectionSuccess] = useState<string | null>(null);

  const generateSentimentSummary = useCallback(async () => {
    try {
      setSentimentLoading(true);
      const response = await fetch(`/api/properties/${propertyId}/reviews/sentiment`, {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        if (data.sentiment_summary) {
          setReviewsSummary((prev) =>
            prev
              ? { ...prev, sentiment_summary: data.sentiment_summary }
              : null
          );
        }
      }
    } catch (error) {
      console.error('Error generating sentiment summary:', error);
    } finally {
      setSentimentLoading(false);
    }
  }, [propertyId]);

  const fetchReviews = useCallback(async (showLoading: boolean = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }

      // Fetch reviews summary
      const { data: summaryData, error: summaryError } = await supabase
        .from('property_reviews_summary')
        .select('*')
        .eq('property_id', propertyId)
        .single();

      if (summaryError && summaryError.code !== 'PGRST116') {
        // PGRST116 is "not found" error, which is okay
        console.error('Error fetching reviews summary:', summaryError);
      } else {
        setReviewsSummary(summaryData);
      }

      // Fetch all positive reviews (4-5 stars)
      const { data: positiveData, error: positiveError } = await supabase
        .from('property_reviews')
        .select('*')
        .eq('property_id', propertyId)
        .in('stars', [4, 5])
        .order('published_at', { ascending: false });

      if (positiveError) {
        console.error('Error fetching positive reviews:', positiveError);
        setAllPositiveReviews([]);
      } else {
        setAllPositiveReviews(positiveData || []);
      }

      // Fetch all negative reviews (1-3 stars)
      const { data: negativeData, error: negativeError } = await supabase
        .from('property_reviews')
        .select('*')
        .eq('property_id', propertyId)
        .in('stars', [1, 2, 3])
        .order('published_at', { ascending: false });

      if (negativeError) {
        console.error('Error fetching negative reviews:', negativeError);
        setAllNegativeReviews([]);
      } else {
        setAllNegativeReviews(negativeData || []);
      }

      // Generate sentiment summary if it doesn't exist
      if (summaryData && !summaryData.sentiment_summary && (positiveData?.length || negativeData?.length)) {
        generateSentimentSummary();
      }

      // If reviews were collected, reset the collecting state
      if (summaryData || positiveData?.length || negativeData?.length) {
        setIsCollectingReviews(false);
      }
    } catch (err) {
      console.error('Error fetching reviews:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, [propertyId, generateSentimentSummary]);

  useEffect(() => {
    if (propertyId) {
      fetchReviews();
    }
  }, [propertyId, fetchReviews]);


  const handleCollectReviews = async () => {
    if (!propertyId || isCollectingReviews) return;
    
    try {
      setIsCollectingReviews(true);
      setCollectionError(null);
      setCollectionSuccess(null);

      const response = await fetch(`/api/properties/${propertyId}/extract/reviews`, {
        method: 'POST',
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Failed to collect reviews');
      }

      setCollectionSuccess('Reviews collection started! This may take a few minutes.');
      
      // Refresh reviews after a delay (without showing loading spinner)
      setTimeout(() => {
        fetchReviews(false);
        setTimeout(() => setCollectionSuccess(null), 3000);
      }, 2000);
    } catch (error: any) {
      console.error('Error collecting reviews:', error);
      setCollectionError(error.message || 'Failed to collect reviews. Please try again.');
      setIsCollectingReviews(false);
      setTimeout(() => setCollectionError(null), 5000);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Unknown date';
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - date.getTime());
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 30) return `${diffDays} days ago`;
      if (diffDays < 365) {
        const months = Math.floor(diffDays / 30);
        return `${months} ${months === 1 ? 'month' : 'months'} ago`;
      }
      const years = Math.floor(diffDays / 365);
      return `${years} ${years === 1 ? 'year' : 'years'} ago`;
    } catch {
      return 'Unknown date';
    }
  };

  const toggleReviewExpansion = (reviewId: string) => {
    setExpandedReviews((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(reviewId)) {
        newSet.delete(reviewId);
      } else {
        newSet.add(reviewId);
      }
      return newSet;
    });
  };

  const renderStars = (stars: number | null) => {
    if (!stars) return null;
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={`w-5 h-5 ${
              star <= stars
                ? 'text-yellow-400 fill-current'
                : 'text-muted-foreground'
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

  const renderReviewRow = (review: PropertyReview) => {
    const isExpanded = expandedReviews.has(review.id);
    const reviewText = review.review_text || '';
    const hasOwnerResponse = !!review.response_from_owner_text;
    // Show "Read more" if text is long OR if there's an owner response to expand
    const shouldShowExpand = reviewText.length > 200 || hasOwnerResponse;
    const shouldTruncate = reviewText.length > 200;
    const displayText = shouldTruncate && !isExpanded
      ? reviewText.substring(0, 200) + '...'
      : reviewText;

    return (
      <Fragment key={review.id}>
        <TableRow
          className={`transition-all ${
            shouldShowExpand ? 'hover:bg-neutral-50 cursor-pointer' : ''
          }`}
          style={{
            borderLeft: `3px solid ${
              review.stars && review.stars >= 4 ? 'var(--success)' :
              review.stars && review.stars <= 2 ? 'var(--error)' :
              'var(--warning)'
            }`,
          }}
          onClick={() => shouldShowExpand && toggleReviewExpansion(review.id)}
        >
          {/* Reviewer Column */}
          <TableCell className="align-top">
            <div className="space-y-1.5">
              {/* Row 1: Name and Avatar on same line */}
              <div className="flex items-center gap-2">
                {review.reviewer_photo_url ? (
                  <img
                    src={review.reviewer_photo_url}
                    alt={review.reviewer_name || 'Reviewer'}
                    className="w-6 h-6 rounded-full object-cover flex-shrink-0"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-6 h-6 rounded-full bg-primary-200 flex items-center justify-center text-primary-700 font-semibold text-xs flex-shrink-0">
                    {(review.reviewer_name || 'R')[0].toUpperCase()}
                  </div>
                )}
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-semibold text-foreground">
                    {review.reviewer_name || 'Anonymous'}
                  </p>
                  {review.is_local_guide && (
                    <Badge variant="secondary" className="text-xs flex-shrink-0 bg-blue-100 text-blue-700">
                      Local Guide
                    </Badge>
                  )}
                </div>
              </div>
              {/* Row 2: Rating */}
              <div className="flex items-center gap-2">
                {renderStars(review.stars)}
                {review.stars && (
                  <span className="text-sm font-medium text-foreground">
                    {review.stars}/5
                  </span>
                )}
              </div>
              {/* Row 3: Timestamp */}
              <div>
                <span className="text-sm text-neutral-600">
                  {formatDate(review.published_at)}
                </span>
              </div>
            </div>
          </TableCell>

          {/* Review Text Column */}
          <TableCell className="align-top">
            <div className="space-y-2">
              {/* Review Text */}
              <div>
                {reviewText ? (
                  <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                    {displayText}
                  </p>
                ) : (
                  <p className="text-sm text-neutral-400 italic">No review text</p>
                )}
              </div>

              {/* Owner Response Badge and Read More - Below Text */}
              {(hasOwnerResponse || shouldShowExpand) && (
                <div className="flex items-center gap-3 flex-wrap">
                  {hasOwnerResponse && (
                    <Badge variant="outline" className="bg-primary-50 text-primary-700 shadow-sm">
                      Owner Response
                    </Badge>
                  )}
                  {shouldShowExpand && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleReviewExpansion(review.id);
                      }}
                      className="h-auto p-0 text-primary-600 hover:text-primary-700 font-medium text-sm"
                    >
                      {isExpanded ? 'Read less' : 'Read more'}
                    </Button>
                  )}
                </div>
              )}
              
              {/* Owner Response - shown when expanded */}
              {isExpanded && review.response_from_owner_text && (
                <div className="pt-3 border-t border-border animate-in fade-in duration-200">
                  <p className="text-xs font-semibold text-neutral-600 mb-2">
                    Response from owner
                  </p>
                  <p className="text-sm text-foreground italic leading-relaxed">
                    {review.response_from_owner_text}
                  </p>
                  {review.response_from_owner_date && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDate(review.response_from_owner_date)}
                    </p>
                  )}
                </div>
              )}
            </div>
          </TableCell>
        </TableRow>
      </Fragment>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-8">
          <div className="text-center text-neutral-600">Loading reviews...</div>
        </CardContent>
      </Card>
    );
  }

  // Calculate displayed reviews based on expanded state
  const displayedPositiveReviews = positiveReviewsExpanded 
    ? allPositiveReviews 
    : allPositiveReviews.slice(0, 5);
  
  const displayedNegativeReviews = negativeReviewsExpanded 
    ? allNegativeReviews 
    : allNegativeReviews.slice(0, 5);

  return (
    <Card className="transition-all duration-300 hover:shadow-lg">
      <CardHeader>
        <CardTitle className="text-2xl font-display text-secondary-700 flex items-center gap-2">
          <MessageSquare className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
          Reviews
        </CardTitle>
      </CardHeader>
      <CardContent>
      {/* Empty State */}
      {!reviewsSummary &&
      allPositiveReviews.length === 0 &&
      allNegativeReviews.length === 0 ? (
        <>
          <EmptyState
            icon={MessageSquare}
            title="No reviews collected yet"
            description="Review information including ratings, sentiment summaries, and individual reviews will appear here once collected."
            actionLabel="Collect Reviews"
            onAction={handleCollectReviews}
            disabled={isCollectingReviews}
            actionIcon={<MessageSquare className="w-5 h-5" strokeWidth={2} />}
          />
          {collectionSuccess && (
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg shadow-sm">
              <p className="text-sm text-green-700 dark:text-green-300">{collectionSuccess}</p>
            </div>
          )}
          {collectionError && (
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg shadow-sm">
              <p className="text-sm text-red-700 dark:text-red-300">{collectionError}</p>
            </div>
          )}
        </>
      ) : (
        <>

      {/* Overall Rating and Review Count */}
      {reviewsSummary && (
        <div className="mb-8 pb-6 border-b border-border">
          <div className="flex items-center gap-6">
            {reviewsSummary.overall_rating && (
              <>
                {/* Circular Rating Indicator */}
                <div className="relative w-20 h-20 shrink-0">
                  <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 80 80">
                    <circle cx="40" cy="40" r="35" fill="none" stroke="currentColor" strokeWidth="5" className="text-neutral-200" />
                    <circle
                      cx="40" cy="40" r="35"
                      fill="none"
                      stroke="url(#ratingGradient)"
                      strokeWidth="5"
                      strokeLinecap="round"
                      strokeDasharray={`${(reviewsSummary.overall_rating / 5) * 220} 220`}
                    />
                    <defs>
                      <linearGradient id="ratingGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#FF1B8D" />
                        <stop offset="100%" stopColor="#7B1FA2" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-secondary-700 font-display">
                      {reviewsSummary.overall_rating.toFixed(1)}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="flex items-center gap-1 mb-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <svg
                        key={star}
                        className={`w-6 h-6 ${
                          star <= Math.round(reviewsSummary.overall_rating!)
                            ? 'fill-[url(#starGradient)]'
                            : 'text-muted-foreground fill-current'
                        }`}
                        viewBox="0 0 20 20"
                      >
                        <defs>
                          <linearGradient id="starGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#FF1B8D" />
                            <stop offset="100%" stopColor="#7B1FA2" />
                          </linearGradient>
                        </defs>
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                  {reviewsSummary.review_count && (
                    <p className="text-lg font-semibold text-foreground">
                      {reviewsSummary.review_count}{' '}
                      {reviewsSummary.review_count === 1 ? 'review' : 'reviews'}
                    </p>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Sentiment Summary */}
      <div className="mb-8 pb-6 border-b border-border">
        <h3 className="text-lg font-semibold text-foreground mb-3">
          Review Summary
        </h3>
        {sentimentLoading ? (
          <div className="text-neutral-600 text-sm">Generating summary...</div>
        ) : reviewsSummary?.sentiment_summary ? (
          <p className="text-base text-foreground leading-relaxed">
            {reviewsSummary.sentiment_summary}
          </p>
        ) : (
          <p className="text-muted-foreground text-sm italic">
            No sentiment summary available.
          </p>
        )}
      </div>

      {/* Reviews Table */}
      <div className="space-y-8">
        {/* Positive Reviews Table */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-foreground">
                Positive Reviews ({allPositiveReviews.length})
              </h3>
              <p className="text-sm text-neutral-600 mt-1">
                4-5 star reviews, sorted by most recent
              </p>
            </div>
            {allPositiveReviews.length > 5 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPositiveReviewsExpanded(!positiveReviewsExpanded)}
                className="text-sm text-secondary-600 hover:text-secondary-700"
              >
                {positiveReviewsExpanded ? 'Show less' : `Show all (${allPositiveReviews.length})`}
              </Button>
            )}
          </div>
          {displayedPositiveReviews.length > 0 ? (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow className="bg-neutral-50">
                    <TableHead className="w-1/3 uppercase tracking-wide">Reviewer</TableHead>
                    <TableHead className="uppercase tracking-wide">Review</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {displayedPositiveReviews.map((review) => renderReviewRow(review))}
                </TableBody>
              </Table>
            </Card>
          ) : (
            <p className="text-muted-foreground text-sm italic">
              No positive reviews to display.
            </p>
          )}
        </div>

        {/* Negative Reviews Table */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-foreground">
                Negative Reviews ({allNegativeReviews.length})
              </h3>
              <p className="text-sm text-neutral-600 mt-1">
                1-3 star reviews, sorted by most recent
              </p>
            </div>
            {allNegativeReviews.length > 5 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setNegativeReviewsExpanded(!negativeReviewsExpanded)}
                className="text-sm text-secondary-600 hover:text-secondary-700"
              >
                {negativeReviewsExpanded ? 'Show less' : `Show all (${allNegativeReviews.length})`}
              </Button>
            )}
          </div>
          {displayedNegativeReviews.length > 0 ? (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow className="bg-neutral-50">
                    <TableHead className="w-1/3 uppercase tracking-wide">Reviewer</TableHead>
                    <TableHead className="uppercase tracking-wide">Review</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {displayedNegativeReviews.map((review) => renderReviewRow(review))}
                </TableBody>
              </Table>
            </Card>
          ) : (
            <p className="text-muted-foreground text-sm italic">
              No negative reviews to display.
            </p>
          )}
        </div>
      </div>
        </>
      )}
      </CardContent>
    </Card>
  );
}

