'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import OnboardingProgressCard from '@/app/components/OnboardingProgressCard';
import OnboardingHero from '@/app/components/OnboardingHero';

interface OnboardingSession {
  id: string;
  property_id: string | null;
  url: string;
  status: string;
  current_step: string | null;
  completed_steps: string[];
  errors: Array<{ extraction_type?: string; error?: string; message?: string }>;
  created_at: string;
  updated_at: string;
}

const EXTRACTION_STEPS = [
  { key: 'property_info', name: 'Property Information', description: 'Extracting property name, address, and contact information' },
  { key: 'images', name: 'Images', description: 'Collecting images from the website' },
  { key: 'brand_identity', name: 'Brand Identity', description: 'Analyzing brand colors, fonts, and design elements' },
  { key: 'amenities', name: 'Amenities', description: 'Identifying building and apartment amenities' },
  { key: 'floor_plans', name: 'Floor Plans', description: 'Extracting floor plan details and pricing' },
  { key: 'special_offers', name: 'Special Offers', description: 'Finding special offers and promotions' },
  { key: 'classify_images', name: 'Classify Images', description: 'Tagging images with AI to categorize them' },
  { key: 'reviews', name: 'Reviews', description: 'Gathering reviews and ratings' },
  { key: 'competitors', name: 'Competitors', description: 'Identifying nearby competitor properties' },
];

export default function OnboardingProgressPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.session_id as string;

  const [session, setSession] = useState<OnboardingSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pollDelay, setPollDelay] = useState(2000); // Start at 2 seconds

  const fetchSessionStatus = async () => {
    try {
      const response = await fetch(`/api/properties/onboard/${sessionId}/status`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch session status');
      }

      setSession(data.session);
      setError(null);

      // Reset poll delay on successful fetch
      setPollDelay(2000);

      // If completed and has property_id, redirect after a short delay
      if (data.session.status === 'completed' && data.session.property_id) {
        setTimeout(() => {
          router.push(`/properties/${data.session.property_id}`);
        }, 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
      setLoading(false);
      // Increase poll delay on error (exponential backoff, max 10s)
      setPollDelay((prev) => Math.min(prev * 1.5, 10000));
    }
  };

  useEffect(() => {
    if (!sessionId) {
      setError('Invalid session ID');
      setLoading(false);
      return;
    }

    let isMounted = true;
    let timeoutId: NodeJS.Timeout | null = null;

    const scheduleNextPoll = () => {
      if (!isMounted) return;

      const currentSession = session;
      // Stop polling if session is completed or failed
      if (currentSession && (currentSession.status === 'completed' || currentSession.status === 'failed')) {
        return;
      }

      timeoutId = setTimeout(() => {
        if (isMounted) {
          fetchSessionStatus().finally(() => {
            scheduleNextPoll();
          });
        }
      }, pollDelay);
    };

    // Initial fetch
    fetchSessionStatus().finally(() => {
      if (isMounted) {
        setLoading(false);
        scheduleNextPoll();
      }
    });

    return () => {
      isMounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [sessionId, pollDelay]);

  const handleRetry = async (extractionType: string) => {
    try {
      const response = await fetch(`/api/properties/onboard/${sessionId}/retry`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ extraction_type: extractionType }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to retry extraction');
      }

      // Refresh session status immediately
      await fetchSessionStatus();
    } catch (err) {
      console.error('Error retrying extraction:', err);
      setError(err instanceof Error ? err.message : 'Failed to retry extraction');
    }
  };

  const getStepStatus = (stepKey: string): 'pending' | 'in_progress' | 'completed' | 'error' => {
    if (!session) return 'pending';

    // Check if step has an error
    const stepError = session.errors.find(
      err => err.extraction_type === stepKey || err.message?.includes(stepKey)
    );

    if (stepError) {
      return 'error';
    }

    // Check if step is completed
    if (session.completed_steps.includes(stepKey)) {
      return 'completed';
    }

    // Check if step is currently in progress
    if (session.current_step === stepKey) {
      return 'in_progress';
    }

    return 'pending';
  };

  const getStepError = (stepKey: string): string | undefined => {
    if (!session) return undefined;
    const stepError = session.errors.find(
      err => err.extraction_type === stepKey
    );
    return stepError?.error || stepError?.message;
  };

  if (loading && !session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="text-lg text-neutral-800">Loading onboarding status...</div>
      </div>
    );
  }

  if (error && !session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="text-lg text-error">
          Error: {error}
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="text-lg text-neutral-800">Session not found</div>
      </div>
    );
  }

  const isCompleted = session.status === 'completed';
  const isFailed = session.status === 'failed';

  return (
    <div className="min-h-screen bg-gradient-page">
      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Hero Section - Show during onboarding */}
        {!isCompleted && (
          <OnboardingHero
            url={session.url}
            completedSteps={session.completed_steps}
            totalSteps={EXTRACTION_STEPS.length}
          />
        )}

        {/* Status Messages */}
        {isCompleted && (
          <div className="mb-8 p-4 bg-success-light border border-success rounded-lg">
            <p className="text-success-dark font-semibold">
              ✓ Onboarding completed! Redirecting to property page...
            </p>
          </div>
        )}
        {isFailed && (
          <div className="mb-8 p-4 bg-error-light border border-error rounded-lg">
            <p className="text-error-dark font-semibold">
              ✗ Onboarding failed. Some steps may have completed successfully.
            </p>
          </div>
        )}

        {/* Progress Cards */}
        <div className="space-y-4">
          {EXTRACTION_STEPS.map((step, index) => {
            const stepStatus = getStepStatus(step.key);
            const stepError = getStepError(step.key);
            return (
              <OnboardingProgressCard
                key={step.key}
                stepName={step.key}
                stepDescription={step.description}
                status={stepStatus}
                error={stepError}
                delay={index * 100}
                onRetry={stepStatus === 'error' ? () => handleRetry(step.key) : undefined}
              />
            );
          })}
        </div>

        {isCompleted && session.property_id && (
          <div className="mt-8 text-center">
            <p className="text-neutral-600 mb-4">
              Taking you to the property page...
            </p>
          </div>
        )}

        {isFailed && (
          <div className="mt-8 text-center">
            <button
              onClick={() => router.push('/properties')}
              className="px-6 py-3 bg-primary-500 text-white font-semibold rounded-lg shadow-primary transition-all duration-200 hover:bg-primary-600 hover:shadow-primary-lg hover:-translate-y-0.5 focus:outline-none focus:ring-4 focus:ring-primary-300"
            >
              Back to Properties
            </button>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}

