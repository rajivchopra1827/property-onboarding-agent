'use client';

import { useEffect, useState, useRef } from 'react';
import { Megaphone, Play, Download, AlertCircle, Video, Image as ImageIcon, ChevronDown, ChevronUp } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import { PropertySocialPost, PropertyImage } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Badge } from '@/app/components/ui/badge';
import { Button } from '@/app/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/app/components/ui/dialog';
import EmptyState from './EmptyState';
import ImageSelectionModal from './ImageSelectionModal';

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

// Video player component with autoplay on hover
function VideoPlayer({
  src,
  poster,
  className,
  aspectRatio = 'square',
  onError,
}: {
  src: string;
  poster?: string;
  className?: string;
  aspectRatio?: 'square' | 'reel';
  onError?: () => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isHovering, setIsHovering] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!videoRef.current) return;

    if (isHovering && !hasError) {
      videoRef.current.play().catch(() => {
        // Autoplay failed, likely due to browser restrictions
      });
    } else {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  }, [isHovering, hasError]);

  const handleError = () => {
    setHasError(true);
    setIsLoading(false);
    onError?.();
  };

  const handleLoadedData = () => {
    setIsLoading(false);
  };

  if (hasError && poster) {
    // Fallback to poster image if video fails to load
    return (
      <div className={`relative ${className}`}>
        <img
          src={poster}
          alt="Post content"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 flex items-center justify-center bg-black/30">
          <div className="text-white text-center">
            <AlertCircle className="w-8 h-8 mx-auto mb-2" />
            <p className="text-xs">Video unavailable</p>
          </div>
        </div>
      </div>
    );
  }

  const aspectClass = aspectRatio === 'reel' ? 'aspect-[9/16]' : 'aspect-square';

  return (
    <div
      className={`relative ${aspectClass} ${className}`}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-neutral-100">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
        </div>
      )}
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        className="w-full h-full object-cover"
        muted
        loop
        playsInline
        preload="metadata"
        onError={handleError}
        onLoadedData={handleLoadedData}
      />
      {!isHovering && !isLoading && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 transition-opacity">
          <div className="w-12 h-12 rounded-full bg-white/90 flex items-center justify-center shadow-lg">
            <Play className="w-6 h-6 text-primary-500 ml-1" fill="currentColor" />
          </div>
        </div>
      )}
      {/* Video indicator badge */}
      <Badge
        variant="secondary"
        className="absolute bottom-2 right-2 bg-black/70 text-white"
      >
        <Video className="w-3 h-3 mr-1" />
        Reel
      </Badge>
    </div>
  );
}

// Video generation status indicator
function VideoGenerationStatus({ status }: { status: string | null }) {
  if (!status || status === 'completed') return null;

  const statusConfig: Record<string, { label: string; color: string; animate: boolean }> = {
    pending: { label: 'Queued', color: 'bg-neutral-500', animate: false },
    processing: { label: 'Generating...', color: 'bg-primary-500', animate: true },
    failed: { label: 'Failed', color: 'bg-error', animate: false },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-black/50">
      <div className="text-center text-white">
        <div className={`w-8 h-8 mx-auto mb-2 rounded-full ${config.color} ${config.animate ? 'animate-pulse' : ''} flex items-center justify-center`}>
          <Video className="w-4 h-4" />
        </div>
        <p className="text-sm font-medium">{config.label}</p>
      </div>
    </div>
  );
}

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
  const [generateAsVideos, setGenerateAsVideos] = useState(false);
  const [images, setImages] = useState<PropertyImage[]>([]);
  const [imageSelectionModalOpen, setImageSelectionModalOpen] = useState(false);
  const [showErrorDetails, setShowErrorDetails] = useState(false);
  const [errorDetails, setErrorDetails] = useState<string[]>([]);

  const fetchSocialPosts = async () => {
    try {
      setLoading(true);
      setErrorMessage(null);

      const { data, error } = await supabase
        .from('property_social_posts')
        .select('*')
        .eq('property_id', propertyId)
        .order('created_at', { ascending: false });

      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/f16407c2-76f5-4de5-b5c6-75f34b83f90e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'SocialPostsSection.tsx:178',message:'Fetched posts from database',data:{error:error?.message,postsCount:data?.length,videoPostsCount:data?.filter((p:any)=>p.is_video).length,videoPosts:data?.filter((p:any)=>p.is_video).map((p:any)=>({id:p.id,is_video:p.is_video,video_url:p.video_url,theme:p.theme}))},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
      // #endregion

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
      fetchImages();
    }
  }, [propertyId]);

  const fetchImages = async () => {
    try {
      const { data, error } = await supabase
        .from('property_images')
        .select('*')
        .eq('property_id', propertyId)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('Error fetching images:', error);
        setImages([]);
      } else {
        // Ensure is_hidden defaults to false
        const imagesWithDefaults = (data || []).map((img: PropertyImage) => ({
          ...img,
          is_hidden: img.is_hidden ?? false,
        }));
        setImages(imagesWithDefaults);
      }
    } catch (err) {
      console.error('Error fetching images:', err);
      setImages([]);
    }
  };

  const handleGenerateVideos = async (imageIds: string[], theme: string) => {
    try {
      setIsGenerating(true);
      setErrorMessage(null);
      setSuccessMessage(null);

      const response = await fetch(`/api/properties/${propertyId}/social-posts/generate-videos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_ids: imageIds,
          theme: theme,
        }),
      });

      const result = await response.json();

      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/f16407c2-76f5-4de5-b5c6-75f34b83f90e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'SocialPostsSection.tsx:247',message:'API response received',data:{responseOk:response.ok,resultSuccess:result.success,resultKeys:Object.keys(result),videosCount:result.videos?.length,totalSucceeded:result.total_succeeded,totalFailed:result.total_failed,errorsCount:result.errors?.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Failed to generate videos');
      }

      // Safely extract result values with defaults
      const totalSucceeded = result.total_succeeded ?? 0;
      const totalFailed = result.total_failed ?? 0;
      const errors = result.errors ?? [];
      const videos = result.videos ?? [];

      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/f16407c2-76f5-4de5-b5c6-75f34b83f90e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'SocialPostsSection.tsx:256',message:'Extracted result values',data:{totalSucceeded,totalFailed,errorsCount:errors.length,videosCount:videos.length,videoUrls:videos.map((v:any)=>v.video_url)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
      // #endregion

      // Show success message
      const successMsg = totalSucceeded > 0
        ? `Successfully generated ${totalSucceeded} video${totalSucceeded !== 1 ? 's' : ''}${totalFailed > 0 ? ` (${totalFailed} failed)` : ''}`
        : 'Video generation completed';
      setSuccessMessage(successMsg);

      // Show errors if any
      if (errors.length > 0) {
        // Build user-friendly error details with safe error handling
        const details: string[] = [];
        try {
          errors.forEach((err: any) => {
            try {
              let imageId = 'Unknown image';
              if (err?.image_id) {
                if (typeof err.image_id === 'string' && err.image_id.length > 0) {
                  imageId = `Image ${err.image_id.slice(0, 8)}...`;
                } else {
                  imageId = 'Image (invalid ID)';
                }
              }
              const errorMsg = err?.error || err?.message || 'Unknown error';
              details.push(`${imageId}: ${errorMsg}`);
            } catch (e) {
              // If we can't parse this error, just stringify it
              try {
                details.push(`Error: ${JSON.stringify(err)}`);
              } catch {
                details.push('Error: Unable to display error details');
              }
            }
          });
        } catch (e) {
          // If mapping fails entirely, show a generic message
          details.push(`Failed to parse error details. ${totalFailed} video${totalFailed !== 1 ? 's' : ''} failed.`);
        }
        
        setErrorDetails(details);
        setShowErrorDetails(false); // Start collapsed
        
        // Show summary error message
        const errorMsg = totalSucceeded > 0
          ? `${totalFailed} video${totalFailed !== 1 ? 's' : ''} failed to generate. Click to see details.`
          : `Video generation failed. Click to see details.`;
        
        setErrorMessage(errorMsg);
      } else {
        setErrorMessage(null); // Clear any previous errors
        setErrorDetails([]);
        setShowErrorDetails(false);
      }

      // Close modal and refresh posts
      setImageSelectionModalOpen(false);
      
      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/f16407c2-76f5-4de5-b5c6-75f34b83f90e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'SocialPostsSection.tsx:311',message:'About to refresh posts',data:{totalSucceeded,videosCount:videos.length,willRefreshIn:'1000ms'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
      // #endregion
      
      setTimeout(() => {
        fetchSocialPosts();
        // Clear success message after refresh
        setTimeout(() => {
          setSuccessMessage(null);
          // Keep error message visible longer if there were errors
          if (errors.length === 0) {
            setErrorMessage(null);
          }
        }, errors.length > 0 ? 10000 : 3000);
      }, 1000);
    } catch (error) {
      console.error('Error generating videos:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate videos. Please try again.';
      setErrorMessage(errorMessage);
      // Keep modal open on error so user can retry
    } finally {
      setIsGenerating(false);
    }
  };

  // Progress steps for loading state
  const progressSteps = [
    { message: 'Analyzing your property...', icon: '~' },
    { message: 'Crafting captions...', icon: '~' },
    { message: 'Selecting images...', icon: '~' },
    { message: 'Generating hashtags...', icon: '#' },
    { message: generateAsVideos ? 'Creating video reels...' : 'Creating mockups...', icon: '~' },
    { message: 'Almost done...', icon: '~' },
  ];

  // Theme hints for content being generated
  const themeHints = [
    { theme: 'lifestyle', icon: '~', label: 'Lifestyle' },
    { theme: 'amenities', icon: '~', label: 'Amenities' },
    { theme: 'floor_plans', icon: '~', label: 'Floor Plans' },
    { theme: 'special_offers', icon: '~', label: 'Special Offers' },
    { theme: 'reviews', icon: '~', label: 'Reviews' },
    { theme: 'location', icon: '~', label: 'Location' },
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
        body: JSON.stringify({
          post_count: 8,
          generate_as_videos: generateAsVideos,
        }),
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Failed to generate posts');
      }

      // Show success message
      const videoSuffix = generateAsVideos ? ' (videos will generate in background)' : '';
      setSuccessMessage(result.message || `Successfully generated ${result.count} posts!${videoSuffix}`);

      // Auto-refresh posts after a short delay
      setTimeout(() => {
        fetchSocialPosts();
        // Clear success message after refresh
        setTimeout(() => setSuccessMessage(null), 3000);
      }, 1000);
    } catch (error) {
      console.error('Error generating posts:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate posts. Please try again.';
      setErrorMessage(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async (post: PropertySocialPost, e: React.MouseEvent) => {
    e.stopPropagation();

    const url = post.is_video && post.video_url ? post.video_url : post.image_url;
    const extension = post.is_video && post.video_url ? 'mp4' : 'jpg';

    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${post.theme}-post-${post.id.slice(0, 8)}.${extension}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-display text-secondary-700 flex items-center gap-2">
            <Megaphone className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
            Social Media Posts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Loading posts...</p>
        </CardContent>
      </Card>
    );
  }

  if (posts.length === 0 && !isGenerating) {
    return (
      <Card className="transition-all duration-300 hover:shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl font-display text-secondary-700 dark:text-secondary-300 flex items-center gap-2">
            <Megaphone className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
            Social Media Posts
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Generate as Videos Toggle */}
          <div className="mb-6 p-4 bg-neutral-50 dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-700">
            <label className="flex items-center gap-3 cursor-pointer">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={generateAsVideos}
                  onChange={(e) => setGenerateAsVideos(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-neutral-300 dark:bg-neutral-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Video className="w-5 h-5 text-primary-500" />
                  <span className="font-semibold text-foreground">Generate as Video Reels</span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  Create 9:16 vertical video reels optimized for Instagram and TikTok
                </p>
              </div>
            </label>
          </div>

          <EmptyState
            icon={Megaphone}
            title="Ready to create some magic?"
            description="Click the button below and we'll create amazing, ready-to-post social media content for you!"
            actionLabel={generateAsVideos ? "Generate Video Reels" : "Generate Posts"}
            onAction={handleGeneratePosts}
            disabled={isGenerating}
            actionIcon={
              generateAsVideos ? (
                <Video className="w-5 h-5" />
              ) : (
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
              )
            }
          />
          {/* Error Message */}
          {errorMessage && (
            <div className="mt-4 p-3 bg-error-light dark:bg-error/20 border border-error-dark dark:border-error rounded-lg">
              <p className="text-sm text-error-dark dark:text-error">{errorMessage}</p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Show loading state during generation
  if (isGenerating) {
    const currentProgress = ((currentStep + 1) / progressSteps.length) * 100;
    const circumference = 2 * Math.PI * 45; // radius = 45
    const strokeDashoffset = circumference - (currentProgress / 100) * circumference;

    return (
      <Card className="transition-all duration-300 hover:shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl font-display text-secondary-700 flex items-center gap-2">
            <Megaphone className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
            Social Media Posts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Card className="bg-gradient-to-br from-neutral-50 via-primary-50/30 to-secondary-50/30">
            <CardContent className="p-8 text-center">
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
                    <span className="text-base font-semibold text-foreground">
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
                    <span className="text-xs font-medium text-foreground">
                      {hint.label}
                    </span>
                  </div>
                ))}
              </div>

              {/* Generating with AI Text */}
              <div className="flex items-center gap-2 mt-2">
                <span className="text-sm text-neutral-600">
                  {generateAsVideos ? 'Generating video reels with ' : 'Generating with '}
                  <span className="font-semibold bg-gradient-to-r from-primary-500 to-secondary-500 bg-clip-text text-transparent">
                    AI
                  </span>
                  ...
                </span>
              </div>
            </div>
          </div>
            </CardContent>
          </Card>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="transition-all duration-300 hover:shadow-lg">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-2xl font-display text-secondary-700 flex items-center gap-2">
            <Megaphone className="w-6 h-6 text-primary-500" strokeWidth={2.5} />
            Social Media Posts ({posts.length})
          </CardTitle>
          <div className="flex items-center gap-3">
            {successMessage && (
              <div className="px-4 py-2 bg-success-light rounded-lg shadow-sm">
                <p className="text-sm text-success-dark font-medium">{successMessage}</p>
              </div>
            )}
            <Button
              onClick={() => setImageSelectionModalOpen(true)}
              variant="default"
              size="sm"
              className="flex items-center gap-2"
            >
              <Video className="w-4 h-4" />
              Generate Videos
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {posts.map((post) => (
          <Card
            key={post.id}
            className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => setSelectedPost(post)}
          >
            {/* Mockup Image, Video, or Original Image */}
            <div className="relative bg-neutral-100">
              {(() => {
                // #region agent log
                if (post.is_video) {
                  fetch('http://127.0.0.1:7243/ingest/f16407c2-76f5-4de5-b5c6-75f34b83f90e',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'SocialPostsSection.tsx:669',message:'Rendering video post',data:{postId:post.id,is_video:post.is_video,video_url:post.video_url,video_generation_status:post.video_generation_status,hasVideoUrl:!!post.video_url},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
                }
                // #endregion
                return null;
              })()}
              {post.is_video && post.video_url ? (
                <VideoPlayer
                  src={post.video_url.startsWith('http') ? post.video_url : `/api/videos/${encodeURIComponent(post.video_url)}`}
                  poster={post.image_url}
                  aspectRatio="square"
                />
              ) : post.is_video && post.video_generation_status && post.video_generation_status !== 'completed' ? (
                <div className="relative aspect-square">
                  {post.image_url && (
                    <img
                      src={post.image_url}
                      alt={`${themeDisplayNames[post.theme] || post.theme} post`}
                      className="w-full h-full object-cover opacity-50"
                    />
                  )}
                  <VideoGenerationStatus status={post.video_generation_status} />
                </div>
              ) : post.image_url ? (
                <div className="relative aspect-square">
                  <img
                    src={post.image_url}
                    alt={`${themeDisplayNames[post.theme] || post.theme} post`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                    }}
                  />
                </div>
              ) : (
                <div className="aspect-square w-full h-full flex items-center justify-center bg-muted">
                  <Megaphone className="w-12 h-12 text-muted-foreground" />
                </div>
              )}
              {/* Theme Badge */}
              <Badge
                variant="secondary"
                className="absolute top-2 left-2 bg-black/70 text-white uppercase"
              >
                {themeDisplayNames[post.theme] || post.theme}
              </Badge>
              {/* Download Button */}
              <button
                onClick={(e) => handleDownload(post, e)}
                className="absolute top-2 right-2 p-2 bg-black/70 hover:bg-black/90 text-white rounded-full transition-colors"
                title={post.is_video ? "Download video" : "Download image"}
              >
                <Download className="w-4 h-4" />
              </button>
            </div>

            {/* Post Info */}
            <CardContent className="p-4">
              <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                {post.caption}
              </p>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{post.hashtags?.length || 0} hashtags</span>
                {post.cta && (
                  <span className="text-primary-600 font-medium">{post.cta}</span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Post Detail Modal */}
      {selectedPost && (
        <Dialog open={!!selectedPost} onOpenChange={(open) => !open && setSelectedPost(null)}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-xl text-secondary-700 dark:text-secondary-300 flex items-center gap-2">
                {selectedPost.is_video && <Video className="w-5 h-5 text-primary-500" />}
                {themeDisplayNames[selectedPost.theme] || selectedPost.theme} Post
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-6">
              {/* Video or Image */}
              <div className="relative bg-neutral-100 rounded-lg overflow-hidden">
                {selectedPost.is_video && selectedPost.video_url ? (
                  <div className="aspect-[9/16] max-h-[60vh] mx-auto">
                    <video
                      src={selectedPost.video_url.startsWith('http') ? selectedPost.video_url : `/api/videos/${encodeURIComponent(selectedPost.video_url)}`}
                      poster={selectedPost.image_url}
                      className="w-full h-full object-contain bg-black"
                      controls
                      autoPlay
                      loop
                      playsInline
                    />
                  </div>
                ) : (
                  <div className="aspect-square">
                    <img
                      src={selectedPost.image_url}
                      alt={`${themeDisplayNames[selectedPost.theme] || selectedPost.theme} post`}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                {selectedPost.mockup_image_url && !selectedPost.is_video && (
                  <div className="absolute top-2 right-2 bg-black/70 text-white px-2 py-1 rounded text-xs">
                    Mockup Available
                  </div>
                )}
                {selectedPost.is_video && (
                  <div className="absolute top-2 right-2 bg-primary-500 text-white px-2 py-1 rounded text-xs flex items-center gap-1">
                    <Video className="w-3 h-3" />
                    Video Reel
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
                      <Badge
                        key={index}
                        variant="outline"
                        className="bg-primary-100 text-primary-700 shadow-sm"
                      >
                        #{tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* CTA */}
              {selectedPost.cta && (
                <div>
                  <h4 className="text-sm font-semibold text-foreground mb-2 uppercase tracking-wide">
                    Call to Action
                  </h4>
                  <p className="text-base text-foreground font-medium">
                    {selectedPost.cta}
                  </p>
                </div>
              )}

              {/* Download Button */}
              <div className="pt-4">
                <Button
                  onClick={(e) => handleDownload(selectedPost, e)}
                  className="w-full"
                  variant="default"
                >
                  <Download className="w-4 h-4 mr-2" />
                  {selectedPost.is_video ? 'Download Video' : 'Download Image'}
                </Button>
              </div>

              {/* Metadata */}
              <div className="pt-4 border-t border-border">
                <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                  <div>
                    <span className="font-semibold">Platform:</span> {selectedPost.platform}
                  </div>
                  <div>
                    <span className="font-semibold">Type:</span> {selectedPost.is_video ? 'Video Reel' : selectedPost.post_type}
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
          </DialogContent>
        </Dialog>
      )}

      {/* Image Selection Modal */}
      <ImageSelectionModal
        open={imageSelectionModalOpen}
        onOpenChange={(open) => {
          setImageSelectionModalOpen(open);
          if (!open) {
            // Clear error message when modal closes
            setErrorMessage(null);
          }
        }}
        images={images}
        propertyId={propertyId}
        onGenerate={handleGenerateVideos}
      />

      {/* Error Message for Video Generation */}
      {errorMessage && (
        <div className="px-6 pb-4">
          <div className="p-3 bg-error-light dark:bg-error/20 border border-error-dark dark:border-error rounded-lg">
            <button
              onClick={() => setShowErrorDetails(!showErrorDetails)}
              className="w-full text-left flex items-center justify-between gap-2"
            >
              <p className="text-sm text-error-dark dark:text-error font-medium">{errorMessage}</p>
              {errorDetails.length > 0 && (
                showErrorDetails ? (
                  <ChevronUp className="w-4 h-4 text-error-dark dark:text-error flex-shrink-0" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-error-dark dark:text-error flex-shrink-0" />
                )
              )}
            </button>
            {showErrorDetails && errorDetails.length > 0 && (
              <div className="mt-3 pt-3 border-t border-error-dark/20 dark:border-error/20">
                <ul className="space-y-2">
                  {errorDetails.map((detail, index) => (
                    <li key={index} className="text-xs text-error-dark dark:text-error">
                      • {detail}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
      </CardContent>
    </Card>
  );
}
