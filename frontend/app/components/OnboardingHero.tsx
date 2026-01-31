'use client';

import { useEffect, useState } from 'react';
import { 
  Building2, 
  Image, 
  Palette, 
  Star, 
  Layout, 
  Tag, 
  MessageSquare, 
  MapPin, 
  ChevronRight,
  Sparkles
} from 'lucide-react';

interface OnboardingHeroProps {
  url: string;
  completedSteps: string[];
  totalSteps: number;
}

// Step order matching the extraction steps
const STEP_ORDER = [
  'property_info',
  'images',
  'brand_identity',
  'amenities',
  'floor_plans',
  'special_offers',
  'classify_images',
  'reviews',
  'competitors'
];

// Icon mapping for each step
const STEP_ICONS = {
  property_info: Building2,
  images: Image,
  brand_identity: Palette,
  amenities: Star,
  floor_plans: Layout,
  special_offers: Tag,
  classify_images: Sparkles,
  reviews: MessageSquare,
  competitors: MapPin,
};

export default function OnboardingHero({ url, completedSteps, totalSteps }: OnboardingHeroProps) {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

  // AI-focused messages that cycle through
  const messages = [
    { text: 'Working AI magic...', icon: '✨' },
    { text: 'Analyzing content...', icon: '🔍' },
    { text: 'Discovering pages...', icon: '🌐' },
    { text: 'Processing with AI...', icon: '🤖' },
    { text: 'Crawling website...', icon: '🕷️' },
    { text: 'Extracting insights...', icon: '💡' },
  ];

  // Calculate progress percentage
  const progress = totalSteps > 0 ? (completedSteps.length / totalSteps) * 100 : 0;

  // Cycle through messages
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % messages.length);
    }, 3500); // Change message every 3.5 seconds

    return () => clearInterval(interval);
  }, []);

  const currentMessage = messages[currentMessageIndex];
  
  // Determine which step is currently active (first incomplete step)
  const getCurrentStepIndex = () => {
    for (let i = 0; i < STEP_ORDER.length; i++) {
      if (!completedSteps.includes(STEP_ORDER[i])) {
        return i;
      }
    }
    return STEP_ORDER.length; // All completed
  };
  
  const currentStepIndex = getCurrentStepIndex();

  return (
    <div className="rounded-lg border border-border shadow-md bg-gradient-to-br from-muted via-primary-50/30 dark:via-primary-900/20 to-secondary-50/30 dark:to-secondary-900/20 p-6 mb-8 overflow-hidden relative">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-50/20 dark:from-primary-900/10 via-transparent to-secondary-50/20 dark:to-secondary-900/10 pointer-events-none" />

      <div className="relative z-10">
        {/* Header */}
        <div className="text-center mb-4">
          <h1 className="text-4xl font-bold text-secondary-700 dark:text-secondary-300 mb-2 font-display">
            Onboarding Property
          </h1>
          <p className="text-lg text-foreground leading-relaxed">
            {url}
          </p>
        </div>

        {/* Horizontal Icon Flow */}
        <div className="flex flex-col items-center justify-center gap-4 py-4">
          {/* SVG Gradient Definitions */}
          <svg width="0" height="0" className="absolute">
            <defs>
              <linearGradient id="iconGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#FF1B8D" />
                <stop offset="100%" stopColor="#7B1FA2" />
              </linearGradient>
            </defs>
          </svg>

          {/* Icon Row - 9 steps */}
          <div className="relative w-full max-w-5xl flex items-center justify-center gap-1 md:gap-2 overflow-x-auto pb-2 px-2">
            {STEP_ORDER.map((stepKey, index) => {
              const IconComponent = STEP_ICONS[stepKey as keyof typeof STEP_ICONS];
              const isCompleted = completedSteps.includes(stepKey);
              const isActive = currentStepIndex === index;
              
              return (
                <div key={stepKey} className="flex items-center flex-shrink-0">
                  <div className="flex flex-col items-center gap-1">
                    <div className={`relative w-9 h-9 md:w-11 md:h-11 transition-all duration-300 ${
                      isCompleted ? 'scale-110' : isActive ? 'scale-110 animate-icon-pulse' : 'opacity-50'
                    }`}>
                      {isCompleted || isActive ? (
                        <IconComponent 
                          className="w-full h-full"
                          style={{ stroke: 'url(#iconGradient)' }}
                          strokeWidth={2.5}
                        />
                      ) : (
                        <IconComponent 
                          className="w-full h-full text-neutral-400"
                          strokeWidth={1.5}
                        />
                      )}
                    </div>
                  </div>
                  {index < STEP_ORDER.length - 1 && (
                    <ChevronRight className="w-3 h-3 md:w-4 md:h-4 text-primary-400 flex-shrink-0 mx-0.5 md:mx-1" />
                  )}
                </div>
              );
            })}
          </div>

          {/* Horizontal Progress Bar */}
          <div className="w-full max-w-5xl h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-500 to-secondary-500 transition-all duration-500 ease-out rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Message Display */}
          <div className="min-h-[50px] flex flex-col items-center justify-center mt-2">
            <div
              key={currentMessageIndex}
              className="animate-step-fade flex flex-col items-center gap-2"
            >
              <div className="flex items-center gap-2">
                <span className="text-2xl">{currentMessage.icon}</span>
                <span className="text-lg font-semibold text-foreground">
                  {currentMessage.text}
                </span>
              </div>
            </div>
          </div>

          {/* Progress Text */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {completedSteps.length} of {totalSteps} steps completed
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
