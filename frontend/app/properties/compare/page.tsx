'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useComparisonData } from './hooks/useComparisonData';
import ComparisonHeader from './components/ComparisonHeader';
import QuickMetricsTable from './components/QuickMetricsTable';
import CollapsibleSection from './components/CollapsibleSection';
import FloorPlansComparison from './components/FloorPlansComparison';
import AmenitiesMatrix from './components/AmenitiesMatrix';
import ReviewsComparison from './components/ReviewsComparison';
import SpecialOffersGrid from './components/SpecialOffersGrid';
import MobileCompareView from './components/MobileCompareView';

export default function ComparisonPage() {
  const searchParams = useSearchParams();
  const ids = searchParams.get('ids')?.split(',') || [];

  const { data, loading, error } = useComparisonData(ids);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-lg text-foreground">Loading comparison...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-lg text-error">{error}</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-lg text-foreground">No properties selected for comparison</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-page">
      {/* Page Header */}
      <div className="container mx-auto px-6 py-8 max-w-7xl">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-secondary-700 dark:text-secondary-300 mb-2 font-display">
              Property Comparison
            </h1>
            <p className="text-lg text-foreground">
              Comparing {data.length} properties
            </p>
          </div>
          <div className="flex gap-4">
            <Link
              href="/properties"
              className="px-4 py-2 text-foreground border border-border rounded-lg hover:bg-accent transition-colors"
            >
              ← Back to List
            </Link>
          </div>
        </div>
      </div>

      {isMobile ? (
        /* Mobile View */
        <div className="container mx-auto px-4 pb-8">
          <MobileCompareView properties={data} />
        </div>
      ) : (
        <>
          {/* Comparison Header - Sticky */}
          <ComparisonHeader properties={data} />

          {/* Comparison Content */}
          <div className="container mx-auto px-6 py-8 max-w-7xl">
            {/* Quick Metrics - Always visible */}
            <div className="mb-6">
              <QuickMetricsTable properties={data} />
            </div>

            {/* Floor Plans Comparison - Default expanded */}
            <CollapsibleSection title="Floor Plans" defaultExpanded={true}>
              <FloorPlansComparison properties={data} />
            </CollapsibleSection>

            {/* Amenities Matrix - Default collapsed */}
            <CollapsibleSection title="Amenities" defaultExpanded={false}>
              <AmenitiesMatrix properties={data} />
            </CollapsibleSection>

            {/* Reviews Comparison - Default collapsed */}
            <CollapsibleSection title="Reviews" defaultExpanded={false}>
              <ReviewsComparison properties={data} />
            </CollapsibleSection>

            {/* Special Offers Grid - Default collapsed */}
            <CollapsibleSection title="Special Offers" defaultExpanded={false}>
              <SpecialOffersGrid properties={data} />
            </CollapsibleSection>
          </div>
        </>
      )}
    </div>
  );
}
