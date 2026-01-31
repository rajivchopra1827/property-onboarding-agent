'use client';

interface ExtractionLoadingStateProps {
  toolName: string;
  isGenerating: boolean;
}

export default function ExtractionLoadingState({
  toolName,
  isGenerating,
}: ExtractionLoadingStateProps) {
  if (!isGenerating) {
    return null;
  }

  return (
    <div className="rounded-lg border border-neutral-200 shadow-sm bg-gradient-to-br from-neutral-50 via-primary-50/30 to-secondary-50/30 p-8 text-center">
      <div className="max-w-md mx-auto">
        {/* Main Loading Container */}
        <div className="flex flex-col items-center justify-center gap-6">
          {/* Infinite Loading Spinner - No Progress Indication */}
          <div className="relative w-32 h-32 flex items-center justify-center">
            {/* Spinning Ring - Full Circle, No Progress */}
            <svg className="absolute inset-0 w-32 h-32" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="currentColor"
                strokeWidth="4"
                className="text-neutral-200"
              />
              {/* Animated Spinning Arc - Infinite Loop */}
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="url(#loadingGradient)"
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray="70 283"
                className="animate-spin"
                style={{
                  transformOrigin: '50% 50%',
                }}
              />
              <defs>
                <linearGradient id="loadingGradient" x1="0%" y1="0%" x2="100%" y2="100%">
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

          {/* Processing Message */}
          <div className="min-h-[60px] flex flex-col items-center justify-center">
            <div className="flex flex-col items-center gap-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl">⏳</span>
                <span className="text-base font-semibold text-neutral-700">
                  Processing...
                </span>
              </div>
            </div>
          </div>

          {/* Generating with AI Text */}
          <div className="flex items-center gap-2 mt-2">
            <span className="text-sm text-neutral-600">
              Extracting {toolName} with{' '}
              <span className="font-semibold bg-gradient-to-r from-primary-500 to-secondary-500 bg-clip-text text-transparent">
                AI
              </span>
              ...
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}


