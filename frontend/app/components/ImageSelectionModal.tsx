'use client';

import { useState, useEffect } from 'react';
import { Video, Check, ImageIcon } from 'lucide-react';
import { PropertyImage } from '@/lib/types';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/app/components/ui/dialog';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';

interface ImageSelectionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  images: PropertyImage[];
  propertyId: string;
  onGenerate: (imageIds: string[], theme: string) => Promise<void>;
}

const themeOptions = [
  { value: 'lifestyle', label: 'Lifestyle' },
  { value: 'amenities', label: 'Amenities' },
  { value: 'floor_plans', label: 'Floor Plans' },
  { value: 'special_offers', label: 'Special Offers' },
  { value: 'reviews', label: 'Reviews' },
  { value: 'location', label: 'Location' },
];

// Image Card Component
function ImageCard({
  image,
  isSelected,
  isGenerating,
  onToggle,
}: {
  image: PropertyImage;
  isSelected: boolean;
  isGenerating: boolean;
  onToggle: () => void;
}) {
  const [imageError, setImageError] = useState(false);

  return (
    <div
      className={`
        relative group cursor-pointer rounded-lg overflow-hidden border-2 transition-all
        ${isSelected 
          ? 'border-primary-500 ring-2 ring-primary-200' 
          : 'border-border hover:border-primary-300'
        }
        ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      onClick={() => !isGenerating && onToggle()}
    >
      {/* Image Container */}
      <div className="aspect-square relative bg-neutral-100 dark:bg-neutral-800 w-full">
        {!imageError ? (
          <img
            src={image.image_url}
            alt={image.alt_text || 'Property image'}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-neutral-200 dark:bg-neutral-700">
            <div className="text-center p-2">
              <ImageIcon className="w-8 h-8 text-neutral-400 mx-auto mb-1" />
              <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate px-1">
                                {image.alt_text || 'Image unavailable'}
              </p>
            </div>
          </div>
        )}
        
        {/* Checkbox Overlay */}
        <div className="absolute top-2 left-2 z-10">
          <div
            className={`
              w-6 h-6 rounded-md flex items-center justify-center transition-all shadow-md
              ${isSelected 
                ? 'bg-primary-500 text-white' 
                : 'bg-black/60 text-white group-hover:bg-black/80'
              }
            `}
          >
            {isSelected && <Check className="w-4 h-4" />}
          </div>
        </div>

        {/* Image Tags Badge */}
        {image.image_tags && image.image_tags.length > 0 && !imageError && (
          <div className="absolute bottom-2 left-2 right-2 flex flex-wrap gap-1 z-10">
            {image.image_tags.slice(0, 2).map((tag, idx) => (
              <Badge
                key={idx}
                variant="secondary"
                className="text-xs bg-black/70 text-white px-1.5 py-0.5 backdrop-blur-sm"
              >
                {tag.replace('_', ' ')}
              </Badge>
            ))}
            {image.image_tags.length > 2 && (
              <Badge
                variant="secondary"
                className="text-xs bg-black/70 text-white px-1.5 py-0.5 backdrop-blur-sm"
              >
                +{image.image_tags.length - 2}
              </Badge>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ImageSelectionModal({
  open,
  onOpenChange,
  images,
  propertyId,
  onGenerate,
}: ImageSelectionModalProps) {
  const [selectedImageIds, setSelectedImageIds] = useState<Set<string>>(new Set());
  const [selectedTheme, setSelectedTheme] = useState<string>('lifestyle');
  const [isGenerating, setIsGenerating] = useState(false);

  // Filter out hidden images
  const visibleImages = images.filter(img => !img.is_hidden);

  // Reset selection when modal closes
  useEffect(() => {
    if (!open) {
      setSelectedImageIds(new Set());
      setSelectedTheme('lifestyle');
      setIsGenerating(false);
    }
  }, [open]);

  const handleToggleImage = (imageId: string) => {
    const newSelection = new Set(selectedImageIds);
    if (newSelection.has(imageId)) {
      newSelection.delete(imageId);
    } else {
      newSelection.add(imageId);
    }
    setSelectedImageIds(newSelection);
  };

  const handleSelectAll = () => {
    if (selectedImageIds.size === visibleImages.length) {
      setSelectedImageIds(new Set());
    } else {
      setSelectedImageIds(new Set(visibleImages.map(img => img.id)));
    }
  };

  const handleGenerate = async () => {
    if (selectedImageIds.size === 0) return;

    setIsGenerating(true);
    try {
      await onGenerate(Array.from(selectedImageIds), selectedTheme);
      // Modal will be closed by parent component after successful generation
    } catch (error) {
      console.error('Error generating videos:', error);
      // Keep modal open on error so user can retry
    } finally {
      setIsGenerating(false);
    }
  };

  const selectedCount = selectedImageIds.size;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4">
          <DialogTitle className="text-xl flex items-center gap-2">
            <Video className="w-5 h-5 text-primary-500" />
            Select Images to Generate Videos
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col px-6 pb-4">
          {/* Theme Selector */}
          <div className="flex items-center gap-4 mb-4">
            <label htmlFor="theme-select" className="text-sm font-medium whitespace-nowrap">
              Theme:
            </label>
            <select
              id="theme-select"
              value={selectedTheme}
              onChange={(e) => setSelectedTheme(e.target.value)}
              disabled={isGenerating}
              className="flex-1 px-3 py-2 border border-input rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {themeOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
              disabled={isGenerating || visibleImages.length === 0}
            >
              {selectedImageIds.size === visibleImages.length ? 'Deselect All' : 'Select All'}
            </Button>
          </div>

          {/* Selected Count */}
          {selectedCount > 0 && (
            <div className="text-sm text-muted-foreground mb-4">
              {selectedCount} image{selectedCount !== 1 ? 's' : ''} selected
            </div>
          )}

          {/* Image Grid */}
          <div className="flex-1 overflow-y-auto min-h-0">
            {visibleImages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <Video className="w-12 h-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No images available</p>
                <p className="text-sm text-muted-foreground mt-2">
                  Extract images for this property first
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                {visibleImages.map((image) => (
                  <ImageCard
                    key={image.id}
                    image={image}
                    isSelected={selectedImageIds.has(image.id)}
                    isGenerating={isGenerating}
                    onToggle={() => handleToggleImage(image.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <DialogFooter className="px-6 pb-6 pt-4 border-t">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isGenerating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleGenerate}
            disabled={selectedCount === 0 || isGenerating}
            className="min-w-[160px]"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Generating...
              </>
            ) : (
              <>
                <Video className="w-4 h-4 mr-2" />
                Generate Videos ({selectedCount})
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
