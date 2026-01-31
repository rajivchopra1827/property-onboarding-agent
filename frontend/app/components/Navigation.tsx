import Link from 'next/link';
import { ThemeToggle } from './ThemeToggle';

export default function Navigation() {
  return (
    <nav className="sticky top-0 z-[200] bg-background/95 backdrop-blur-md border-b border-border">
      <div className="container mx-auto px-6 py-4 max-w-7xl">
        <div className="flex items-center justify-between">
          <Link
            href="/properties"
            className="text-xl font-semibold text-foreground hover:text-primary-500 transition-colors focus:outline-none focus:ring-4 focus:ring-primary-300 rounded-lg px-2 py-1"
          >
            Property Onboarding Agent
          </Link>
          <div className="flex items-center gap-2">
            <Link
              href="/properties"
              className="px-4 py-2 rounded-lg font-medium text-sm text-foreground hover:text-primary-500 hover:bg-accent transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-primary-300"
            >
              Properties
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </nav>
  );
}

