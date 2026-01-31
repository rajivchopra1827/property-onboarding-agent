import Link from 'next/link';

export default function Navigation() {
  return (
    <nav className="sticky top-0 z-[200] bg-white/95 backdrop-blur-md border-b border-neutral-200">
      <div className="container mx-auto px-6 py-4 max-w-7xl">
        <div className="flex items-center justify-between">
          <Link
            href="/properties"
            className="text-xl font-semibold text-neutral-900 hover:text-primary-500 transition-colors focus:outline-none focus:ring-4 focus:ring-primary-300 rounded-lg px-2 py-1"
          >
            Property Onboarding Agent
          </Link>
          <div className="flex items-center gap-2">
            <Link
              href="/properties"
              className="px-4 py-2 rounded-lg font-medium text-sm text-neutral-800 hover:text-primary-500 hover:bg-neutral-100 transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-primary-300"
            >
              Properties
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

