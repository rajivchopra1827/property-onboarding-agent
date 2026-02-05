'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Building2 } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';

export default function Navigation() {
  const pathname = usePathname();
  const isPropertiesRoute = pathname?.startsWith('/properties');

  return (
    <nav className="sticky top-0 z-[200] bg-background/95 backdrop-blur-md">
      <div className="container mx-auto px-6 py-4 max-w-7xl">
        <div className="flex items-center justify-between">
          <Link
            href="/properties"
            className="flex items-center gap-2 text-2xl font-bold font-display text-foreground hover:text-transparent hover:bg-clip-text hover:bg-[image:var(--gradient-primary)] transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-primary-300 rounded-lg px-2 py-1"
          >
            <Building2 className="w-6 h-6 text-primary-500 shrink-0" strokeWidth={2.5} />
            Property Onboarding Agent
          </Link>
          <div className="flex items-center gap-2">
            <Link
              href="/properties"
              className={`relative px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-primary-300 ${
                isPropertiesRoute
                  ? 'text-primary-500'
                  : 'text-foreground hover:text-primary-500 hover:bg-accent'
              }`}
            >
              Properties
              {isPropertiesRoute && (
                <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-[image:var(--gradient-primary)] rounded-full" />
              )}
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </div>
      {/* Gradient bottom line */}
      <div className="h-[2px] bg-[image:var(--gradient-primary)]" />
    </nav>
  );
}
