'use client';

import { useEffect, useState } from 'react';
import { Megaphone } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { PropertySocialPost } from '@/lib/types';

interface SocialPostsSectionProps {
  propertyId: string;
}

const themeDisplayNames: Record<string, string> = {
  lifestyle: 'Lifestyle',
  amenities: 'Amenities',
  floor_plans: 'Floor Plans',
  special_offers: 'Special Offers',
  reviews: 'Reviews',
  location: 'Location',
};

export default function SocialPostsSection({ propertyId }: SocialPostsSectionProps) {
  const [posts, setPosts] = useState<PropertySocialPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedPost, setExpandedPost] = useState<string | null>(null);
  const [selectedPost, setSelectedPost] = useState<PropertySocialPost | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [currentThemeIndex, setCurrentThemeIndex] = useState(0);

  const fetchSocialPosts = async () => {
    try {
      setLoading(true);
      setErrorMessage(null);

      const { data, error } = await supabase
        .from('property_social_posts')
        .select('*')
        .eq('property_id', propertyId)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('Error fetching social posts:', error);
        setPosts([]);
      } else {
        setPosts(data || []);
      }
    } catch (err) {
      console.error('Error fetching social posts:', err);
      setPosts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (propertyId) {
      fetchSocialPosts();
    }
  }, [propertyId]);

  // Progress steps for loading state
  const progressSteps = [
    { message: 'Analyzing your property...', icon: '🏠' },
    { message: 'Crafting captions...', icon: '✍️' },
    { message: 'Selecting images...', icon: '🖼️' },
    { message: 'Generating hashtags...', icon: '#' },
    { message: 'Creating mockups...', icon: '🎨' },
    { message: 'Almost done...', icon: '✓' },
  ];

  // Theme hints for content being generated
  const themeHints = [
    { theme: 'lifestyle', icon: '✨', label: 'Lifestyle' },
    { theme: 'amenities', icon: '🏊', label: 'Amenities' },
    { theme: 'floor_plans', icon: '📐', label: 'Floor Plans' },
    { theme: 'special_offers', icon: '🎁', label: 'Special Offers' },
    { theme: 'reviews', icon: '⭐', label: 'Reviews' },
    { theme: 'location', icon: '📍', label: 'Location' },
  ];

  // Cycle through progress steps during generation
  useEffect(() => {
    if (!isGenerating) {
      setCurrentStep(0);
      setCurrentThemeIndex(0);
      return;
    }

    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % progressSteps.length);
    }, 5000); // Change step every 5 seconds

    const themeInterval = setInterval(() => {
      setCurrentThemeIndex((prev) => (prev + 1) % themeHints.length);
    }, 3000); // Change theme hint every 3 seconds

    return () => {
      clearInterval(stepInterval);
      clearInterval(themeInterval);
    };
  }, [isGenerating]);

  const handleGeneratePosts = async () => {
    if (!propertyId) {
      setErrorMessage('Property ID is missing. Please refresh the page.');
      return;
    }

    try {
      setIsGenerating(true);
      setCurrentStep(0);
      setCurrentThemeIndex(0);
      setErrorMessage(null);
      setSuccessMessage(null);

      const response = await fetch(`/api/properties/${propertyId}/social-posts/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ post_count: 8 }),
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Failed to generate posts');
      }

      // Show success message
      setSuccessMessage(result.message || `Successfully generated ${result.count} posts!`);

      // Auto-refresh posts after a short delay
      setTimeout(() => {
        fetchSocialPosts();
        // Clear success message after refresh
        setTimeout(() => setSuccessMessage(null), 3000);
      }, 1000);
    } catch (error: any) {
      console.error('Error generating posts:', error);
      setErrorMessage(error.message || 'Failed to generate posts. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md">
        <h2 className="text-2xl font-bold text-secondary-700 mb-4 font-display flex items-center gap-2">
          <Megaphone className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
          Social Media Posts
        </h2>
        <p className="text-neutral-600">Loading posts...</p>
      </div>
    );
  }

  if (posts.length === 0 && !isGenerating) {
    return (
      <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md transition-all duration-300 hover:shadow-lg">
        <h2 className="text-2xl font-bold text-secondary-700 mb-4 font-display flex items-center gap-2">
          <Megaphone className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
          Social Media Posts
        </h2>
        <div className="rounded-lg border border-neutral-200 shadow-sm bg-neutral-50 p-8 text-center">
          <div className="max-w-md mx-auto">
            <Megaphone className="w-12 h-12 text-neutral-400 mx-auto mb-4" strokeWidth={1.5} />
            <p className="text-neutral-600 mb-2 font-medium">
              Ready to create some magic?
            </p>
            <p className="text-sm text-neutral-500 mb-6">
              Click the button below and we'll create amazing, ready-to-post social media content for you!
            </p>
            
            {/* Generate Button */}
            <button
              onClick={handleGeneratePosts}
              disabled={isGenerating}
              className="inline-flex items-center gap-2 px-6 py-3 bg-primary-500 text-white font-semibold rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-4 focus:ring-primary-300"
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
              Generate Posts
            </button>

            {/* Error Message */}
            {errorMessage && (
              <div className="mt-4 p-3 bg-error-light border border-error-dark rounded-lg">
                <p className="text-sm text-error-dark">{errorMessage}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Show loading state during generation
  if (isGenerating) {
    const currentProgress = ((currentStep + 1) / progressSteps.length) * 100;
    const circumference = 2 * Math.PI * 45; // radius = 45
    const strokeDashoffset = circumference - (currentProgress / 100) * circumference;

    return (
      <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md transition-all duration-300 hover:shadow-lg">
        <h2 className="text-2xl font-bold text-secondary-700 mb-4 font-display flex items-center gap-2">
          <Megaphone className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
          Social Media Posts
        </h2>
        <div className="rounded-lg border border-neutral-200 shadow-sm bg-gradient-to-br from-neutral-50 via-primary-50/30 to-secondary-50/30 p-8 text-center">
          <div className="max-w-md mx-auto">
            {/* Main Loading Container */}
            <div className="flex flex-col items-center justify-center gap-6">
              {/* Progress Ring with Morphing Shape */}
              <div className="relative w-32 h-32 flex items-center justify-center">
                {/* Progress Ring */}
                <svg className="absolute inset-0 w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
                  {/* Background Circle */}
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="4"
                    className="text-neutral-200"
                  />
                  {/* Progress Circle */}
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="url(#progressGradient)"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    className="transition-all duration-500 ease-out"
                  />
                  <defs>
                    <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#FF1B8D" />
                      <stop offset="100%" stopColor="#7B1FA2" />
                    </linearGradient>
                  </defs>
                </svg>

                {/* Morphing Shape in Center */}
                <div className="relative z-10 w-20 h-20 flex items-center justify-center">
                  <div
                    className="w-16 h-16 bg-gradient-to-br from-primary-500 to-secondary-500 animate-morph-shape animate-pulse-glow"
                    style={{
                      background: 'linear-gradient(135deg, #FF1B8D 0%, #7B1FA2 100%)',
                    }}
                  />

                  {/* Particle Effects */}
                  {[...Array(8)].map((_, i) => (
                    <div
                      key={i}
                      className="absolute w-2 h-2 bg-primary-400 rounded-full animate-float"
                      style={{
                        left: `${50 + 60 * Math.cos((i * Math.PI * 2) / 8)}%`,
                        top: `${50 + 60 * Math.sin((i * Math.PI * 2) / 8)}%`,
                        animationDelay: `${i * 0.2}s`,
                        animationDuration: `${3 + (i % 3)}s`,
                      }}
                    />
                  ))}

                  {/* Sparkle Effects */}
                  {[
                    { left: '35%', top: '25%' },
                    { left: '65%', top: '30%' },
                    { left: '40%', top: '70%' },
                    { left: '70%', top: '75%' },
                  ].map((pos, i) => (
                    <div
                      key={`sparkle-${i}`}
                      className="absolute w-1 h-1 bg-primary-300 rounded-full animate-sparkle"
                      style={{
                        left: pos.left,
                        top: pos.top,
                        animationDelay: `${i * 0.5}s`,
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* Progress Step Message */}
              <div className="min-h-[60px] flex flex-col items-center justify-center">
                <div
                  key={currentStep}
                  className="animate-step-fade flex flex-col items-center gap-2"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{progressSteps[currentStep].icon}</span>
                    <span className="text-base font-semibold text-neutral-700">
                      {progressSteps[currentStep].message}
                    </span>
                  </div>
                </div>
              </div>

              {/* Theme Hints */}
              <div className="flex flex-wrap items-center justify-center gap-3 mt-2">
                {themeHints.map((hint, index) => (
                  <div
                    key={hint.theme}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border transition-all duration-300 ${
                      index === currentThemeIndex
                        ? 'bg-primary-100 border-primary-300 scale-110 shadow-md animate-theme-icon'
                        : 'bg-white border-neutral-200 opacity-60'
                    }`}
                  >
                    <span className="text-sm">{hint.icon}</span>
                    <span className="text-xs font-medium text-neutral-700">
                      {hint.label}
                    </span>
                  </div>
                ))}
              </div>

              {/* Generating with AI Text */}
              <div className="flex items-center gap-2 mt-2">
                <span className="text-sm text-neutral-600">
                  Generating with{' '}
                  <span className="font-semibold bg-gradient-to-r from-primary-500 to-secondary-500 bg-clip-text text-transparent">
                    AI
                  </span>
                  ...
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-neutral-200 p-8 shadow-md transition-all duration-300 hover:shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-secondary-700 font-display flex items-center gap-2">
          <Megaphone className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
          Social Media Posts ({posts.length})
        </h2>
        {successMessage && (
          <div className="px-4 py-2 bg-success-light border border-success-dark rounded-lg">
            <p className="text-sm text-success-dark font-medium">{successMessage}</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {posts.map((post) => (
          <div
            key={post.id}
            className="border border-neutral-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => setSelectedPost(post)}
          >
            {/* Mockup Image or Original Image */}
            <div className="relative aspect-square bg-neutral-100">
              <img
                src={post.image_url}
                alt={`${themeDisplayNames[post.theme] || post.theme} post`}
                className="w-full h-full object-cover"
              />
              {/* Theme Badge */}
              <div className="absolute top-2 left-2 bg-black/70 text-white px-2 py-1 rounded text-xs font-semibold uppercase">
                {themeDisplayNames[post.theme] || post.theme}
              </div>
            </div>

            {/* Post Info */}
            <div className="p-4">
              <p className="text-sm text-neutral-600 mb-2 line-clamp-2">
                {post.caption}
              </p>
              <div className="flex items-center justify-between text-xs text-neutral-500">
                <span>{post.hashtags.length} hashtags</span>
                {post.cta && (
                  <span className="text-primary-600 font-medium">{post.cta}</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Post Detail Modal */}
      {selectedPost && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedPost(null)}
        >
          <div
            className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-white border-b border-neutral-200 px-6 py-4 flex items-center justify-between">
              <h3 className="text-xl font-bold text-secondary-700">
                {themeDisplayNames[selectedPost.theme] || selectedPost.theme} Post
              </h3>
              <button
                onClick={() => setSelectedPost(null)}
                className="text-neutral-500 hover:text-neutral-700 transition-colors"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                  className="w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Image */}
              <div className="relative aspect-square bg-neutral-100 rounded-lg overflow-hidden">
                <img
                  src={selectedPost.image_url}
                  alt={`${themeDisplayNames[selectedPost.theme] || selectedPost.theme} post`}
                  className="w-full h-full object-cover"
                />
                {selectedPost.mockup_image_url && (
                  <div className="absolute top-2 right-2 bg-black/70 text-white px-2 py-1 rounded text-xs">
                    Mockup Available
                  </div>
                )}
              </div>

              {/* Caption */}
              <div>
                <h4 className="text-sm font-semibold text-neutral-700 mb-2 uppercase tracking-wide">
                  Caption
                </h4>
                <p className="text-base text-neutral-900 leading-relaxed">
                  {selectedPost.caption}
                </p>
              </div>

              {/* Hashtags */}
              {selectedPost.hashtags && selectedPost.hashtags.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-neutral-700 mb-2 uppercase tracking-wide">
                    Hashtags ({selectedPost.hashtags.length})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedPost.hashtags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-xs font-medium"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* CTA */}
              {selectedPost.cta && (
                <div>
                  <h4 className="text-sm font-semibold text-neutral-700 mb-2 uppercase tracking-wide">
                    Call to Action
                  </h4>
                  <p className="text-base text-neutral-900 font-medium">
                    {selectedPost.cta}
                  </p>
                </div>
              )}

              {/* Metadata */}
              <div className="pt-4 border-t border-neutral-200">
                <div className="grid grid-cols-2 gap-4 text-sm text-neutral-600">
                  <div>
                    <span className="font-semibold">Platform:</span> {selectedPost.platform}
                  </div>
                  <div>
                    <span className="font-semibold">Type:</span> {selectedPost.post_type}
                  </div>
                  {selectedPost.created_at && (
                    <div>
                      <span className="font-semibold">Created:</span>{' '}
                      {new Date(selectedPost.created_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

