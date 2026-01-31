'use client';

import { useEffect, useState, Fragment } from 'react';
import { MessageSquare } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { PropertyReview, PropertyReviewsSummary } from '@/lib/types';

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

  useEffect(() => {
    async function fetchReviews() {
      try {
        setLoading(true);

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
      } catch (err) {
        console.error('Error fetching reviews:', err);
      } finally {
        setLoading(false);
      }
    }

    if (propertyId) {
      fetchReviews();
    }
  }, [propertyId]);

  const generateSentimentSummary = async () => {
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
        <tr
          className={`border-b border-neutral-100 transition-all ${
            shouldShowExpand ? 'hover:bg-neutral-50 cursor-pointer' : ''
          }`}
          onClick={() => shouldShowExpand && toggleReviewExpansion(review.id)}
        >
          {/* Reviewer Column */}
          <td className="py-4 px-4 align-top">
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
                  <p className="font-semibold text-neutral-900">
                    {review.reviewer_name || 'Anonymous'}
                  </p>
                  {review.is_local_guide && (
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium flex-shrink-0">
                      Local Guide
                    </span>
                  )}
                </div>
              </div>
              {/* Row 2: Rating */}
              <div className="flex items-center gap-2">
                {renderStars(review.stars)}
                {review.stars && (
                  <span className="text-sm font-medium text-neutral-700">
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
          </td>

          {/* Review Text Column */}
          <td className="py-4 px-4 align-top">
            <div className="space-y-2">
              {/* Review Text */}
              <div>
                {reviewText ? (
                  <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-wrap">
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
                    <div className="flex items-center gap-1.5 bg-primary-50 border border-primary-200 rounded-full px-3 py-1.5">
                      <svg
                        className="w-4 h-4 text-primary-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
                        />
                      </svg>
                      <span className="text-xs font-semibold text-primary-700">
                        Owner Response
                      </span>
                    </div>
                  )}
                  {shouldShowExpand && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleReviewExpansion(review.id);
                      }}
                      className="flex items-center gap-1 text-primary-600 hover:text-primary-700 font-medium text-sm"
                    >
                      {isExpanded ? (
                        <>
                          <span>Read less</span>
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 15l7-7 7 7"
                            />
                          </svg>
                        </>
                      ) : (
                        <>
                          <span>Read more</span>
                          <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 9l-7 7-7-7"
                            />
                          </svg>
                        </>
                      )}
                    </button>
                  )}
                </div>
              )}
              
              {/* Owner Response - shown when expanded */}
              {isExpanded && review.response_from_owner_text && (
                <div className="pt-3 border-t border-neutral-200 animate-in fade-in duration-200">
                  <p className="text-xs font-semibold text-neutral-600 mb-2">
                    Response from owner
                  </p>
                  <p className="text-sm text-neutral-700 italic leading-relaxed">
                    {review.response_from_owner_text}
                  </p>
                  {review.response_from_owner_date && (
                    <p className="text-xs text-neutral-500 mt-1">
                      {formatDate(review.response_from_owner_date)}
                    </p>
                  )}
                </div>
              )}
            </div>
          </td>
        </tr>
      </Fragment>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md">
        <div className="text-center text-neutral-600">Loading reviews...</div>
      </div>
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
    <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md transition-all duration-300 hover:shadow-lg">
      <h2 className="text-2xl font-bold text-secondary-700 mb-6 font-display flex items-center gap-2">
        <MessageSquare className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
        Reviews
      </h2>

      {/* Empty State */}
      {!reviewsSummary &&
      allPositiveReviews.length === 0 &&
      allNegativeReviews.length === 0 ? (
        <div className="rounded-lg border border-neutral-200 shadow-sm bg-neutral-50 p-8 text-center">
          <div className="max-w-md mx-auto">
            <MessageSquare className="w-12 h-12 text-neutral-400 mx-auto mb-4" strokeWidth={1.5} />
            <p className="text-neutral-600 mb-2 font-medium">
              No reviews collected yet
            </p>
            <p className="text-sm text-neutral-500">
              Review information including ratings, sentiment summaries, and individual reviews will appear here once collected.
            </p>
          </div>
        </div>
      ) : (
        <>

      {/* Overall Rating and Review Count */}
      {reviewsSummary && (
        <div className="mb-8 pb-6 border-b border-neutral-200">
          <div className="flex items-center gap-6">
            {reviewsSummary.overall_rating && (
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-secondary-700">
                  {reviewsSummary.overall_rating.toFixed(1)}
                </span>
                <div className="flex items-center gap-1 mb-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <svg
                      key={star}
                      className={`w-6 h-6 ${
                        star <= Math.round(reviewsSummary.overall_rating!)
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
              </div>
            )}
            {reviewsSummary.review_count && (
              <div>
                <p className="text-lg font-semibold text-neutral-900">
                  {reviewsSummary.review_count}{' '}
                  {reviewsSummary.review_count === 1 ? 'review' : 'reviews'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sentiment Summary */}
      <div className="mb-8 pb-6 border-b border-neutral-200">
        <h3 className="text-lg font-semibold text-neutral-900 mb-3">
          Review Summary
        </h3>
        {sentimentLoading ? (
          <div className="text-neutral-600 text-sm">Generating summary...</div>
        ) : reviewsSummary?.sentiment_summary ? (
          <p className="text-base text-neutral-700 leading-relaxed">
            {reviewsSummary.sentiment_summary}
          </p>
        ) : (
          <p className="text-neutral-500 text-sm italic">
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
              <h3 className="text-lg font-semibold text-neutral-900">
                Positive Reviews ({allPositiveReviews.length})
              </h3>
              <p className="text-sm text-neutral-600 mt-1">
                4-5 star reviews, sorted by most recent
              </p>
            </div>
            {allPositiveReviews.length > 5 && (
              <button
                onClick={() => setPositiveReviewsExpanded(!positiveReviewsExpanded)}
                className="text-sm text-secondary-600 hover:text-secondary-700 font-medium transition-colors"
              >
                {positiveReviewsExpanded ? 'Show less' : `Show all (${allPositiveReviews.length})`}
              </button>
            )}
          </div>
          {displayedPositiveReviews.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border border-neutral-200 shadow-sm">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-neutral-200 bg-neutral-50">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide w-1/3">
                      Reviewer
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                      Review
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {displayedPositiveReviews.map((review) => renderReviewRow(review))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-neutral-500 text-sm italic">
              No positive reviews to display.
            </p>
          )}
        </div>

        {/* Negative Reviews Table */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-neutral-900">
                Negative Reviews ({allNegativeReviews.length})
              </h3>
              <p className="text-sm text-neutral-600 mt-1">
                1-3 star reviews, sorted by most recent
              </p>
            </div>
            {allNegativeReviews.length > 5 && (
              <button
                onClick={() => setNegativeReviewsExpanded(!negativeReviewsExpanded)}
                className="text-sm text-secondary-600 hover:text-secondary-700 font-medium transition-colors"
              >
                {negativeReviewsExpanded ? 'Show less' : `Show all (${allNegativeReviews.length})`}
              </button>
            )}
          </div>
          {displayedNegativeReviews.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border border-neutral-200 shadow-sm">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-neutral-200 bg-neutral-50">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide w-1/3">
                      Reviewer
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-neutral-800 uppercase tracking-wide">
                      Review
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {displayedNegativeReviews.map((review) => renderReviewRow(review))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-neutral-500 text-sm italic">
              No negative reviews to display.
            </p>
          )}
        </div>
      </div>
        </>
      )}
    </div>
  );
}

