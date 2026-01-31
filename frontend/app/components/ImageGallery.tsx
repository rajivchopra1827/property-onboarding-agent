'use client';

import { useEffect, useState, useRef } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { PropertyImage } from '@/lib/types';
import { getCategoryDisplayName, getAllCategoryIds } from '@/lib/imageCategories';
import { supabase } from '@/lib/supabase';

interface ImageGalleryProps {
  images: PropertyImage[];
  initialIndex?: number;
  onClose: () => void;
  onImageUpdate?: (updatedImage: PropertyImage) => void;
}

export default function ImageGallery({ images, initialIndex = 0, onClose, onImageUpdate }: ImageGalleryProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [localImages, setLocalImages] = useState<PropertyImage[]>(images);
  const [unavailableImageIds, setUnavailableImageIds] = useState<Set<string>>(new Set());
  const currentImageIdRef = useRef<string | null>(null);
  const previousImageIdRef = useRef<string | null>(null);
  const previousImagesIdsRef = useRef<string>('');
  const isSavingRef = useRef<boolean>(false);
  const lastSaveTimeRef = useRef<number>(0);
  
  // Tag editing state
  const [activeTags, setActiveTags] = useState<string[]>([]);
  const [selectedPrimary, setSelectedPrimary] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isTogglingHidden, setIsTogglingHidden] = useState(false);
  const justNavigatedFromHideRef = useRef<boolean>(false);

  const allCategories = getAllCategoryIds();

  // Update ref when current index changes
  useEffect(() => {
    const currentImage = localImages[currentIndex];
    if (currentImage?.id) {
      currentImageIdRef.current = currentImage.id;
    }
  }, [currentIndex, localImages]);

  // Update isSaving ref when isSaving state changes
  useEffect(() => {
    isSavingRef.current = isSaving;
  }, [isSaving]);

  // Sync local images with prop changes, preserving current image by ID
  useEffect(() => {
    const currentImageId = currentImageIdRef.current;
    
    // Filter out unavailable images from the incoming images
    const availableImages = images.filter((img) => !unavailableImageIds.has(img.id));
    
    // Check if images actually changed by comparing IDs (not just reference)
    const currentImagesIds = JSON.stringify(availableImages.map(img => img.id).sort());
    const previousImagesIdsSorted = previousImagesIdsRef.current ? JSON.parse(previousImagesIdsRef.current).sort() : [];
    const currentImagesIdsSorted = availableImages.map(img => img.id).sort();
    
    // Check if IDs are the same (just reordered) vs actually changed (added/removed)
    const idsAreSame = JSON.stringify(currentImagesIdsSorted) === JSON.stringify(previousImagesIdsSorted);
    const imagesJustReordered = idsAreSame && previousImagesIdsRef.current !== '';
    
    // Update localImages differently based on whether images were reordered or actually changed
    if (imagesJustReordered) {
      // Images were just reordered - merge new data into existing order to preserve currentIndex
      // This prevents currentImageId from changing when images are reordered
      const imagesById = new Map(availableImages.map(img => [img.id, img]));
      const mergedImages = localImages
        .filter((img) => !unavailableImageIds.has(img.id))
        .map(img => {
          const updated = imagesById.get(img.id);
          return updated || img; // Use updated version if available, otherwise keep existing
        });
      setLocalImages(mergedImages);
    } else {
      // Images were actually added/removed - use new array, filtering unavailable
      setLocalImages(availableImages);
    }
    
    // Update previousImagesIdsRef with sorted IDs for comparison
    previousImagesIdsRef.current = JSON.stringify(currentImagesIdsSorted);
    
    // CRITICAL: Skip index update if images were just reordered (same IDs, different order)
    // AND we're saving or recently saved - this prevents bouncing during tag updates
    if (currentImageId) {
      const newIndex = availableImages.findIndex(img => img.id === currentImageId);
      const timeSinceLastSave = Date.now() - lastSaveTimeRef.current;
      const recentlySaved = timeSinceLastSave < 1000; // Increased to 1 second
      
      // Skip index update if we just navigated from hiding an image (to prevent override)
      if (justNavigatedFromHideRef.current) {
        return;
      }
      
      // Skip index update if images were just reordered AND we're saving or recently saved
      if (imagesJustReordered && (isSavingRef.current || recentlySaved)) {
        return;
      }
      
      // Only update index if it actually changed AND we found the image
      if (newIndex !== -1 && newIndex !== currentIndex) {
        setCurrentIndex(newIndex);
      }
    }
  }, [images, unavailableImageIds]);

  const currentImage = localImages[currentIndex];
  const currentImageId = currentImage?.id;

  // Initialize tag editor when image changes (by ID, not object reference)
  // Only reset tags when navigating to a DIFFERENT image, not when the same image moves position
  useEffect(() => {
    // Only reset tags if we're navigating to a DIFFERENT image
    if (currentImage && currentImageId && currentImageId !== previousImageIdRef.current) {
      const tags = currentImage.image_tags || [];
      // Filter out invalid/removed categories
      const validTags = tags.filter(tag => allCategories.includes(tag));
      const newActiveTags = validTags.length > 0 ? [...validTags] : [];
      const newSelectedPrimary = validTags.length > 0 ? validTags[0] : '';
      setActiveTags(newActiveTags);
      setSelectedPrimary(newSelectedPrimary);
      setError(null);
      previousImageIdRef.current = currentImageId;
    } else if (currentImageId && !previousImageIdRef.current) {
      // First load - initialize
      previousImageIdRef.current = currentImageId;
    }
  }, [currentImageId, allCategories]); // Only depend on ID to avoid resetting when object reference changes

  // Auto-save when tags change
  useEffect(() => {
    if (!currentImage?.id || isSaving) {
      return;
    }
    
    const currentTags = currentImage.image_tags || [];
    // Filter out invalid categories from current tags for comparison
    const validCurrentTags = currentTags.filter(tag => allCategories.includes(tag));
    
    const newTags = selectedPrimary && activeTags.includes(selectedPrimary)
      ? [selectedPrimary, ...activeTags.filter(t => t !== selectedPrimary)]
      : activeTags;
    
    // Only save if tags actually changed
    const tagsChanged = JSON.stringify(newTags) !== JSON.stringify(validCurrentTags);
    if (tagsChanged) {
      handleAutoSave(newTags);
    }
  }, [activeTags, selectedPrimary, currentImage?.id, isSaving, allCategories]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowLeft') {
        setCurrentIndex((prev) => (prev === 0 ? localImages.length - 1 : prev - 1));
      } else if (e.key === 'ArrowRight') {
        setCurrentIndex((prev) => (prev === localImages.length - 1 ? 0 : prev + 1));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [localImages.length, onClose]);

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? localImages.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === localImages.length - 1 ? 0 : prev + 1));
  };

  const handleToggleTag = (tag: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if ((e.target as HTMLElement).closest('.star-button')) {
      return;
    }

    if (activeTags.includes(tag)) {
      // Allow removing tags even if it's the last one (images can have no tags)
      const newActiveTags = activeTags.filter(t => t !== tag);
      setActiveTags(newActiveTags);
      
      // Update primary if needed
      if (selectedPrimary === tag) {
        setSelectedPrimary(newActiveTags.length > 0 ? newActiveTags[0] : '');
      }
    } else {
      const newActiveTags = [...activeTags, tag];
      setActiveTags(newActiveTags);
      
      // Set as primary if no primary is selected
      if (!selectedPrimary || !activeTags.includes(selectedPrimary)) {
        setSelectedPrimary(tag);
      }
    }
  };

  const handleSetPrimary = (tag: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // If tag is not active, activate it first
    if (!activeTags.includes(tag)) {
      const newActiveTags = [...activeTags, tag];
      setActiveTags(newActiveTags);
    }
    
    // Set as primary
    setSelectedPrimary(tag);
  };

  const handleAutoSave = async (tagsToSave: string[]) => {
    if (!currentImage?.id || isSaving) {
      return;
    }

    const imageIdToSave = currentImage.id; // Capture ID before async operation
    const currentIndexAtSave = currentIndex; // Capture index before async operation

    setIsSaving(true);
    setError(null);

    try {
      const { error: updateError, data } = await supabase
        .from('property_images')
        .update({ image_tags: tagsToSave })
        .eq('id', imageIdToSave)
        .select()
        .single();

      if (updateError) {
        throw updateError;
      }

      // Only update if we're still on the same image (user hasn't navigated away)
      if (currentIndexAtSave === currentIndex && localImages[currentIndex]?.id === imageIdToSave) {
        const updatedImage = { ...localImages[currentIndex], image_tags: tagsToSave };
        const updatedImages = localImages.map((img) =>
          img.id === imageIdToSave ? updatedImage : img
        );
        setLocalImages(updatedImages);

        // Notify parent component
        if (onImageUpdate && data) {
          onImageUpdate(data as PropertyImage);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save tags');
      console.error('Error auto-saving tags:', err);
    } finally {
      setIsSaving(false);
      // Track when save completed to prevent index bouncing
      lastSaveTimeRef.current = Date.now();
    }
  };

  const handleToggleHidden = async () => {
    if (!currentImage?.id || isTogglingHidden || isSaving) {
      return;
    }

    const imageIdToToggle = currentImage.id;
    const currentIndexAtToggle = currentIndex;
    const newHiddenStatus = !currentImage.is_hidden;

    setIsTogglingHidden(true);
    setError(null);

    try {
      const { error: updateError, data } = await supabase
        .from('property_images')
        .update({ is_hidden: newHiddenStatus })
        .eq('id', imageIdToToggle)
        .select()
        .single();

      if (updateError) {
        throw updateError;
      }

      // Only update if we're still on the same image (user hasn't navigated away)
      if (currentIndexAtToggle === currentIndex && localImages[currentIndex]?.id === imageIdToToggle) {
        const updatedImage = { ...localImages[currentIndex], is_hidden: newHiddenStatus };
        const updatedImages = localImages.map((img) =>
          img.id === imageIdToToggle ? updatedImage : img
        );
        setLocalImages(updatedImages);

        // Notify parent component
        if (onImageUpdate && data) {
          onImageUpdate(data as PropertyImage);
        }

        // If hiding, navigate to next image (or previous if at the end)
        if (newHiddenStatus && localImages.length > 1) {
          const nextIndex = currentIndex === localImages.length - 1 
            ? currentIndex - 1 
            : currentIndex + 1;
          
          // Set flag to prevent sync useEffect from overriding this navigation
          justNavigatedFromHideRef.current = true;
          setCurrentIndex(nextIndex);
          
          // Clear flag after a short delay to allow sync to complete
          setTimeout(() => {
            justNavigatedFromHideRef.current = false;
          }, 1500);
        }
        // If unhiding, stay on current image (no navigation needed)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle hidden status');
      console.error('Error toggling hidden status:', err);
    } finally {
      setIsTogglingHidden(false);
    }
  };

  if (localImages.length === 0) return null;

  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col">
      {/* Top Navigation Bar */}
      <div className="border-b border-neutral-200 bg-white px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-secondary-700 font-display">Property Onboarding Agent</h1>
          
          {/* Previous Button */}
          {localImages.length > 1 && (
            <button
              onClick={handlePrevious}
              className="text-neutral-700 hover:text-neutral-900 transition-colors p-2 rounded-lg hover:bg-neutral-100 focus:outline-none focus:ring-4 focus:ring-primary-300"
              aria-label="Previous image"
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
                  d="M15.75 19.5L8.25 12l7.5-7.5"
                />
              </svg>
            </button>
          )}

          {/* Next Button */}
          {localImages.length > 1 && (
            <button
              onClick={handleNext}
              className="text-neutral-700 hover:text-neutral-900 transition-colors p-2 rounded-lg hover:bg-neutral-100 focus:outline-none focus:ring-4 focus:ring-primary-300"
              aria-label="Next image"
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
                  d="M8.25 4.5l7.5 7.5-7.5 7.5"
                />
              </svg>
            </button>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Hide/Unhide Button - Enhanced and Always Visible */}
          {currentImage && (
            <button
              onClick={handleToggleHidden}
              disabled={isTogglingHidden || isSaving}
              className={`
                flex items-center gap-2 px-6 py-3 rounded-lg transition-all focus:outline-none focus:ring-4 focus:ring-primary-300 font-semibold text-base shadow-md
                ${currentImage?.is_hidden
                  ? 'bg-amber-500 text-white hover:bg-amber-600 border-2 border-amber-600'
                  : 'bg-neutral-200 text-neutral-700 hover:bg-neutral-300 border-2 border-neutral-400'
                }
                ${(isTogglingHidden || isSaving) ? 'opacity-50 cursor-not-allowed' : ''}
              `}
              aria-label={currentImage?.is_hidden ? 'Unhide image' : 'Hide image'}
              title={currentImage?.is_hidden ? 'Click to unhide this image' : 'Click to hide this image'}
            >
              {isTogglingHidden ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  <span className="font-semibold">Saving...</span>
                </>
              ) : currentImage?.is_hidden ? (
                <>
                  <Eye className="w-6 h-6" strokeWidth={2.5} />
                  <span className="font-semibold">Unhide Image</span>
                </>
              ) : (
                <>
                  <EyeOff className="w-6 h-6" strokeWidth={2.5} />
                  <span className="font-semibold">Hide Image</span>
                </>
              )}
            </button>
          )}

          {/* Close Button */}
          <button
            onClick={onClose}
            className="text-neutral-500 hover:text-neutral-700 transition-colors p-2 rounded-lg hover:bg-neutral-100 focus:outline-none focus:ring-4 focus:ring-primary-300"
            aria-label="Close gallery"
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
      </div>

      {/* Main Content Area - Side by Side */}
      <div className="flex-1 flex min-h-0">
        {/* Image Section - 2/3 width */}
        <div className="w-2/3 flex flex-col items-center justify-center bg-neutral-50 p-8 relative">
          {/* Left Arrow */}
          {localImages.length > 1 && (
            <button
              onClick={handlePrevious}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-600 hover:text-neutral-900 bg-white/80 hover:bg-white shadow-lg rounded-full p-3 transition-all focus:outline-none focus:ring-4 focus:ring-primary-300 z-10"
              aria-label="Previous image"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 19.5L8.25 12l7.5-7.5"
                />
              </svg>
            </button>
          )}

          {/* Image */}
          <div className="flex-1 flex items-center justify-center w-full relative">
            {/* Hidden Image Badge - Top of Image */}
            {currentImage?.is_hidden && (
              <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 px-3 py-1.5 bg-neutral-100 text-neutral-600 rounded-lg text-sm font-medium border border-neutral-300 shadow-md">
                <EyeOff className="w-4 h-4" strokeWidth={2} />
                <span>Hidden</span>
              </div>
            )}

            {/* On-Image Hide/Unhide Button */}
            {currentImage && (
              <button
                onClick={handleToggleHidden}
                disabled={isTogglingHidden || isSaving}
                className={`
                  absolute bottom-4 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 px-6 py-3 rounded-lg shadow-lg font-semibold text-base transition-all focus:outline-none focus:ring-4 disabled:opacity-50 disabled:cursor-not-allowed
                  ${currentImage?.is_hidden
                    ? 'bg-white text-neutral-700 hover:bg-neutral-200 hover:shadow-xl hover:scale-105 border-2 border-neutral-300 focus:ring-neutral-300'
                    : 'bg-white text-neutral-700 hover:bg-neutral-50 border-2 border-neutral-400 focus:ring-neutral-300'
                  }
                `}
                aria-label={currentImage?.is_hidden ? 'Unhide image' : 'Hide image'}
                title={currentImage?.is_hidden ? 'Click to unhide this image' : 'Click to hide this image'}
              >
                {isTogglingHidden ? (
                  <>
                    <svg
                      className="animate-spin h-5 w-5"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    <span>Saving...</span>
                  </>
                ) : currentImage?.is_hidden ? (
                  <>
                    <Eye className="w-6 h-6" strokeWidth={2.5} />
                    <span>Unhide Image</span>
                  </>
                ) : (
                  <>
                    <EyeOff className="w-6 h-6" strokeWidth={2.5} />
                    <span>Hide Image</span>
                  </>
                )}
              </button>
            )}

            {/* Hidden Image Overlay - Subtle */}
            {currentImage?.is_hidden && (
              <div className="absolute inset-0 bg-white/50 backdrop-blur-[1px] rounded-lg z-20 pointer-events-none"></div>
            )}
            
            <img
              src={currentImage.image_url}
              alt={currentImage.alt_text || 'Property image'}
              className={`
                max-w-full max-h-full object-contain rounded-lg shadow-lg transition-all
                ${currentImage?.is_hidden 
                  ? 'opacity-60' 
                  : 'opacity-100'
                }
              `}
              onError={(e) => {
                // Mark image as unavailable
                const unavailableSet = new Set(unavailableImageIds);
                unavailableSet.add(currentImage.id);
                setUnavailableImageIds(unavailableSet);
                
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                
                // Remove from localImages and adjust index
                const updatedImages = localImages.filter(img => img.id !== currentImage.id);
                setLocalImages(updatedImages);
                
                // Adjust current index if needed
                if (currentIndex >= updatedImages.length && updatedImages.length > 0) {
                  setCurrentIndex(updatedImages.length - 1);
                } else if (updatedImages.length === 0) {
                  // No more images available, close gallery
                  onClose();
                }
              }}
            />
          </div>

          {/* Right Arrow */}
          {localImages.length > 1 && (
            <button
              onClick={handleNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-600 hover:text-neutral-900 bg-white/80 hover:bg-white shadow-lg rounded-full p-3 transition-all focus:outline-none focus:ring-4 focus:ring-primary-300 z-10"
              aria-label="Next image"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M8.25 4.5l7.5 7.5-7.5 7.5"
                />
              </svg>
            </button>
          )}

          {/* Image Counter Below Image */}
          {localImages.length > 1 && (
            <div className="mt-4 flex items-center gap-3">
              <div className="text-sm font-medium text-neutral-600">
                {currentIndex + 1} / {localImages.length}
              </div>
            </div>
          )}
        </div>

        {/* Tag Editor Section - 1/3 width */}
        <div className="w-1/3 border-l border-neutral-200 bg-white flex flex-col overflow-hidden">
          {/* Header */}
          <div className="px-6 py-4 border-b border-neutral-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-secondary-700 font-display">Edit Tags</h2>
              {isSaving && (
                <div className="flex items-center gap-2 text-sm text-neutral-500">
                  <svg
                    className="animate-spin h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  <span>Saving...</span>
                </div>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {/* Error Message */}
            {error && (
              <div className="bg-error-light text-error-dark px-4 py-3 rounded-lg shadow-sm">
                <div className="flex items-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                    className="w-5 h-5"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                    />
                  </svg>
                  <span className="font-medium text-sm">{error}</span>
                </div>
              </div>
            )}

            {/* Instructions */}
            <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-3">
              <p className="text-sm text-neutral-700 leading-relaxed">
                <strong>How to use:</strong> Click a tag name to toggle it on/off. Click the star ⭐ to activate a tag and make it primary (or change the primary tag). Only one tag can be primary at a time.
              </p>
            </div>

            {/* Tags Section */}
            <div className="space-y-3">
              <h3 className="text-base font-semibold text-neutral-900">Tags</h3>
              <div className="flex flex-col gap-2">
                {[...allCategories].sort((a, b) => {
                  const nameA = getCategoryDisplayName(a);
                  const nameB = getCategoryDisplayName(b);
                  return nameA.localeCompare(nameB);
                }).map((category) => {
                  const isActive = activeTags.includes(category);
                  const isPrimary = selectedPrimary === category;
                  
                  return (
                    <div
                      key={category}
                      className={`
                        inline-flex items-center gap-1 px-3 py-2 rounded-full text-sm font-medium transition-all self-start
                        ${isActive
                          ? isPrimary
                            ? 'bg-primary-500 text-white shadow-md'
                            : 'bg-primary-100 text-primary-900 border-2 border-primary-300'
                          : 'bg-white text-neutral-700 border-2 border-neutral-300'
                        }
                      `}
                    >
                      {/* Star Button - Using emoji for better rendering */}
                      <button
                        type="button"
                        onClick={(e) => handleSetPrimary(category, e)}
                        disabled={isSaving}
                        className={`
                          star-button flex-shrink-0 p-0.5 rounded focus:outline-none focus:ring-2 focus:ring-primary-300
                          transition-all text-base leading-none
                          cursor-pointer hover:scale-110
                          ${isSaving ? 'opacity-50 cursor-not-allowed' : ''}
                        `}
                        title={isPrimary 
                          ? 'Primary tag (click to change)' 
                          : isActive
                            ? 'Click to make primary'
                            : 'Click to activate and make primary'
                        }
                      >
                        {isPrimary ? '⭐' : '☆'}
                      </button>
                      
                      <button
                        type="button"
                        onClick={(e) => handleToggleTag(category, e)}
                        disabled={isSaving}
                        className={`
                          focus:outline-none focus:ring-2 focus:ring-primary-300 rounded
                          disabled:opacity-50 disabled:cursor-not-allowed
                          ${isActive ? 'cursor-pointer' : 'cursor-pointer hover:bg-neutral-50'}
                        `}
                        title={isActive ? 'Click to remove tag' : 'Click to add tag'}
                      >
                        {getCategoryDisplayName(category)}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
