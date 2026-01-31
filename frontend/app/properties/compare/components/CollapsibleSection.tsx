'use client';

import { useState } from 'react';

interface CollapsibleSectionProps {
  title: string;
  defaultExpanded?: boolean;
  children: React.ReactNode;
}

export default function CollapsibleSection({
  title,
  defaultExpanded = false,
  children
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="bg-card rounded-lg border border-border mb-6 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsExpanded(!isExpanded);
          } else if (e.key === 'Escape' && isExpanded) {
            setIsExpanded(false);
          }
        }}
        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-accent transition-colors focus:outline-none focus:ring-2 focus:ring-primary-300"
        aria-expanded={isExpanded}
        aria-controls={`collapsible-content-${title.replace(/\s+/g, '-').toLowerCase()}`}
      >
        <h2 className="text-xl font-semibold text-foreground">{title}</h2>
        <svg
          className={`w-5 h-5 text-muted-foreground transition-transform duration-200 ${
            isExpanded ? 'rotate-180' : ''
          }`}
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
      </button>
      <div
        id={`collapsible-content-${title.replace(/\s+/g, '-').toLowerCase()}`}
        className={`overflow-hidden transition-all duration-200 ease-out ${
          isExpanded ? 'max-h-[10000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
        aria-hidden={!isExpanded}
      >
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  );
}
