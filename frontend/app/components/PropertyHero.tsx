'use client';

import Link from 'next/link';
import { MapPin } from 'lucide-react';
import { Badge } from '@/app/components/ui/badge';
import { Property, PropertyImage, PropertyBranding } from '@/lib/types';

interface PropertyHeroProps {
  property: Property;
  branding: PropertyBranding | null;
  images: PropertyImage[];
  address: string | null;
}

export default function PropertyHero({ property, branding, images, address }: PropertyHeroProps) {
  // Find hero image - prefer exterior/hero tags
  const heroImage = images.find(img =>
    img.image_tags?.some(tag =>
      tag.toLowerCase().includes('exterior') || tag.toLowerCase().includes('hero')
    )
  ) || images[0] || null;

  const logo = branding?.branding_data?.logo;

  return (
    <section className="relative -mx-6 mb-8 overflow-hidden rounded-2xl min-h-[280px]">
      {/* Background */}
      <div className="absolute inset-0">
        {heroImage ? (
          <img
            src={heroImage.image_url}
            alt={heroImage.alt_text || 'Property hero image'}
            className="object-cover w-full h-full"
          />
        ) : (
          <div className="w-full h-full bg-gradient-hero" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-black/20" />
      </div>

      {/* Content overlay */}
      <div className="relative z-10 flex flex-col justify-end p-8 min-h-[280px]">
        {/* Breadcrumb */}
        <Link
          href="/properties"
          className="text-white/70 hover:text-white text-sm mb-4 transition-colors inline-block w-fit"
        >
          Properties &gt; {property.property_name || 'Property'}
        </Link>

        {/* Logo + Name row */}
        <div className="flex items-center gap-4 mb-2">
          {logo && (
            <img
              src={logo}
              alt="Property logo"
              className="h-12 w-auto object-contain rounded bg-white/10 p-1"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
              }}
            />
          )}
          <h1 className="text-4xl md:text-5xl font-display font-bold text-white">
            {property.property_name || 'Unnamed Property'}
          </h1>
        </div>

        {/* Address */}
        {address && (
          <p className="text-white/80 flex items-center gap-2 text-lg mt-1">
            <MapPin className="w-5 h-5 shrink-0" />
            {address}
          </p>
        )}

        {/* Quick stat badges */}
        <div className="flex gap-3 mt-4 flex-wrap">
          {images.length > 0 && (
            <Badge variant="outline" className="text-white border-white/30 bg-white/10 backdrop-blur-sm">
              {images.length} {images.length === 1 ? 'image' : 'images'}
            </Badge>
          )}
        </div>
      </div>
    </section>
  );
}
