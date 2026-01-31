'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Property } from '@/lib/types';
import AddPropertyForm from '@/app/components/AddPropertyForm';
import { Card, CardContent } from '@/app/components/ui/card';
import { Checkbox } from '@/app/components/ui/checkbox';
import { Button } from '@/app/components/ui/button';

export default function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  
  // Comparison state
  const [compareMode, setCompareMode] = useState(false);
  const [selectedPropertyIds, setSelectedPropertyIds] = useState<string[]>([]);

  useEffect(() => {
    async function fetchProperties() {
      try {
        setLoading(true);
        const { data, error: fetchError } = await supabase
          .from('properties')
          .select('*')
          .order('created_at', { ascending: false });

        if (fetchError) {
          throw fetchError;
        }

        setProperties(data || []);
        setError(null);
      } catch (err: any) {
        const errorMessage = err?.message || err?.error?.message || JSON.stringify(err) || 'Failed to load properties';
        setError(errorMessage);
        console.error('Error fetching properties:', {
          error: err,
          message: err?.message,
          details: err?.details,
          hint: err?.hint,
          code: err?.code,
          supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL || 'not set',
          hasAnonKey: !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
        });
      } finally {
        setLoading(false);
      }
    }

    fetchProperties();
  }, []);

  const getDisplayName = (property: Property) => {
    if (property.property_name) {
      return property.property_name;
    }
    if (property.website_url) {
      try {
        const url = new URL(property.website_url);
        return url.hostname.replace('www.', '');
      } catch {
        return property.website_url;
      }
    }
    return 'Unnamed Property';
  };

  const getAddress = (property: Property) => {
    const parts = [
      property.street_address,
      property.city,
      property.state,
      property.zip_code,
    ].filter(Boolean);
    return parts.length > 0 ? parts.join(', ') : null;
  };

  const handlePropertySelect = (propertyId: string, selected: boolean) => {
    setSelectedPropertyIds(prev => {
      if (selected) {
        // Check max limit
        if (prev.length >= 5) {
          alert('Maximum 5 properties can be compared at once');
          return prev;
        }
        return [...prev, propertyId];
      } else {
        return prev.filter(id => id !== propertyId);
      }
    });
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="text-lg text-neutral-800">Loading properties...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="text-lg text-error">
          Error: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="container mx-auto px-6 py-8 max-w-7xl">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold text-secondary-700 mb-2 font-display">
                Properties
              </h1>
              <p className="text-lg text-neutral-800 leading-relaxed">
                Select a property to view its details and images
              </p>
            </div>
            <Button
              onClick={() => setShowAddForm(true)}
              className="h-12 shadow-primary hover:shadow-primary-lg hover:-translate-y-0.5 active:translate-y-0"
            >
              + Add New Property
            </Button>
          </div>
        </div>

        {/* Compare Mode Toggle */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={compareMode}
                onChange={(e) => {
                  setCompareMode(e.target.checked);
                  if (!e.target.checked) {
                    // Clear selections when disabling compare mode
                    setSelectedPropertyIds([]);
                  }
                }}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
              <span className="ms-3 text-sm font-medium text-neutral-900">
                Compare Mode
              </span>
            </label>

            {compareMode && (
              <span className="text-xs text-neutral-600 animate-fadeIn">
                Select 2-5 properties to compare
              </span>
            )}
          </div>

          {selectedPropertyIds.length > 0 && (
            <button
              onClick={() => {
                setCompareMode(false);
                setSelectedPropertyIds([]);
              }}
              className="text-sm text-neutral-600 hover:text-neutral-900"
            >
              Clear Selection ({selectedPropertyIds.length})
            </button>
          )}
        </div>

        {showAddForm && (
          <div className="mb-8">
            <AddPropertyForm onClose={() => setShowAddForm(false)} />
          </div>
        )}

        {properties.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-lg text-neutral-800">
              No properties found. Start by extracting information from a property website.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {properties.map((property) => {
              const isSelected = selectedPropertyIds.includes(property.id);

              return (
                <Card
                  key={property.id}
                  className={`
                    transition-all duration-300 cursor-pointer
                    ${isSelected
                      ? 'shadow-primary ring-2 ring-primary-200'
                      : 'hover:shadow-lg hover:-translate-y-1'
                    }
                  `}
                  onClick={() => {
                    if (compareMode) {
                      handlePropertySelect(property.id, !isSelected);
                    }
                  }}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start gap-3">
                      {compareMode && (
                        <div className="pt-1 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={(checked) => handlePropertySelect(property.id, checked === true)}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <Link
                          href={compareMode ? '#' : `/properties/${property.id}`}
                          onClick={(e) => {
                            if (compareMode) {
                              e.preventDefault();
                            }
                          }}
                          className="block"
                        >
                          <h2 className="text-xl font-semibold text-neutral-900 mb-2">
                            {getDisplayName(property)}
                          </h2>
                          {getAddress(property) && (
                            <p className="text-sm text-neutral-700 mb-2">
                              {getAddress(property)}
                            </p>
                          )}
                          {property.website_url && (
                            <p className="text-xs text-neutral-600 truncate">
                              {property.website_url}
                            </p>
                          )}
                          {!compareMode && (
                            <div className="mt-4 text-sm text-primary-500 font-medium">
                              View Details →
                            </div>
                          )}
                          {compareMode && isSelected && (
                            <div className="mt-4 flex items-center gap-2 text-sm text-primary-600 font-medium">
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                              Selected
                            </div>
                          )}
                        </Link>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Floating Compare Button */}
        {selectedPropertyIds.length >= 2 && (
          <div className="fixed bottom-6 right-6 z-50 animate-slideUp">
            <button
              onClick={() => {
                const queryString = selectedPropertyIds.join(',');
                window.location.href = `/properties/compare?ids=${queryString}`;
              }}
              className="flex items-center gap-3 bg-primary-500 text-white font-semibold px-6 py-4 rounded-lg shadow-lg hover:bg-primary-600 hover:shadow-xl transition-all duration-200 hover:-translate-y-1 focus:outline-none focus:ring-4 focus:ring-primary-300"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <span>Compare Selected ({selectedPropertyIds.length})</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

