# Phase 1: Selection UI - Detailed Implementation Guide

**Goal:** Add comparison mode to properties list page with multi-select and navigation

**Estimated Time:** 4-6 hours

---

## Overview

This phase adds the ability to:
1. Toggle "Compare Mode" on the properties list page
2. Select 2-5 properties with checkboxes
3. See visual feedback for selected properties
4. Navigate to comparison page with selected property IDs

---

## Step-by-Step Implementation

### Step 1: Add State Management

**File:** `frontend/app/properties/page.tsx`

Add these state variables at the top of the component:

```typescript
export default function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  // NEW: Comparison state
  const [compareMode, setCompareMode] = useState(false);
  const [selectedPropertyIds, setSelectedPropertyIds] = useState<string[]>([]);

  // ... rest of component
}
```

---

### Step 2: Create Compare Mode Toggle

Add this component above the properties grid:

```typescript
// Add this inside the component, after the title section
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
```

---

### Step 3: Add Selection Handler

Add this function inside the component:

```typescript
const handlePropertySelect = (propertyId: string, selected: boolean) => {
  setSelectedPropertyIds(prev => {
    if (selected) {
      // Check max limit
      if (prev.length >= 5) {
        // TODO: Add toast notification
        alert('Maximum 5 properties can be compared at once');
        return prev;
      }
      return [...prev, propertyId];
    } else {
      return prev.filter(id => id !== propertyId);
    }
  });
};
```

---

### Step 4: Modify Property Card to Support Selection

Replace the existing property card Link with this:

```typescript
{properties.map((property) => {
  const isSelected = selectedPropertyIds.includes(property.id);

  return (
    <div
      key={property.id}
      className="relative"
    >
      {/* Checkbox overlay (only in compare mode) */}
      {compareMode && (
        <div className="absolute top-4 left-4 z-10">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => handlePropertySelect(property.id, e.target.checked)}
            className="w-5 h-5 text-primary-500 bg-white border-neutral-300 rounded focus:ring-primary-500 focus:ring-2 cursor-pointer"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

      {/* Property card */}
      <Link
        href={compareMode ? '#' : `/properties/${property.id}`}
        onClick={(e) => {
          if (compareMode) {
            e.preventDefault();
            handlePropertySelect(property.id, !isSelected);
          }
        }}
        className={`
          block bg-white rounded-lg border p-6 shadow-md transition-all duration-300
          ${isSelected
            ? 'border-primary-500 shadow-primary ring-2 ring-primary-200'
            : 'border-neutral-200 hover:shadow-lg hover:-translate-y-1 hover:border-primary-200'
          }
          ${compareMode ? 'cursor-pointer' : ''}
          focus:outline-none focus:ring-4 focus:ring-primary-300
        `}
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
  );
})}
```

---

### Step 5: Create Floating Compare Button

Add this component after the properties grid (before the closing `</div>`):

```typescript
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
```

---

### Step 6: Add CSS Animations

Add these to your global CSS or Tailwind config:

**Option A: Add to `tailwind.config.js`**

```javascript
module.exports = {
  theme: {
    extend: {
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(100px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 200ms ease-out',
        slideUp: 'slideUp 300ms ease-out',
      },
    },
  },
};
```

**Option B: Add to global CSS**

```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    transform: translateY(100px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.animate-fadeIn {
  animation: fadeIn 200ms ease-out;
}

.animate-slideUp {
  animation: slideUp 300ms ease-out;
}
```

---

### Step 7: Create Comparison Page Skeleton

**Create:** `frontend/app/properties/compare/page.tsx`

```typescript
'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { Property } from '@/lib/types';

export default function ComparisonPage() {
  const searchParams = useSearchParams();
  const ids = searchParams.get('ids')?.split(',') || [];

  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProperties() {
      if (ids.length === 0) {
        setError('No properties selected for comparison');
        setLoading(false);
        return;
      }

      try {
        const { data, error: fetchError } = await supabase
          .from('properties')
          .select('*')
          .in('id', ids);

        if (fetchError) throw fetchError;

        setProperties(data || []);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to load properties');
      } finally {
        setLoading(false);
      }
    }

    fetchProperties();
  }, [ids]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="text-lg text-neutral-800">Loading comparison...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="text-lg text-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="container mx-auto px-6 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-secondary-700 mb-2 font-display">
              Property Comparison
            </h1>
            <p className="text-lg text-neutral-800">
              Comparing {properties.length} properties
            </p>
          </div>
          <div className="flex gap-4">
            <Link
              href="/properties"
              className="px-4 py-2 text-neutral-700 border border-neutral-300 rounded-lg hover:bg-neutral-100 transition-colors"
            >
              ← Back to List
            </Link>
            <button
              className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
              onClick={() => alert('PDF export coming in Phase 4!')}
            >
              Export PDF
            </button>
          </div>
        </div>

        {/* Property Names (temporary display) */}
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Selected Properties:</h2>
          <ul className="space-y-2">
            {properties.map(property => (
              <li key={property.id} className="text-neutral-700">
                • {property.property_name || property.website_url}
              </li>
            ))}
          </ul>
          <p className="mt-6 text-sm text-neutral-600">
            Full comparison grid coming in Phase 2!
          </p>
        </div>
      </div>
    </div>
  );
}
```

---

## Testing Checklist

After implementing, test these scenarios:

- [ ] **Toggle Compare Mode** - Switch turns on/off smoothly
- [ ] **Select 1 property** - Checkbox works, no compare button (need 2+)
- [ ] **Select 2 properties** - Compare button appears with correct count
- [ ] **Select 5 properties** - All selected, compare button shows (5)
- [ ] **Try to select 6th** - Alert shows "Maximum 5 properties"
- [ ] **Deselect a property** - Checkbox unchecks, count updates
- [ ] **Toggle off compare mode** - Selections clear, checkboxes disappear
- [ ] **Click compare button** - Navigates to /properties/compare?ids=...
- [ ] **Comparison page loads** - Shows property names
- [ ] **Back button works** - Returns to properties list

---

## Visual Result

After Phase 1, you should see:

**Properties List (Compare Mode OFF):**
```
┌─────────────────────────────────────────────┐
│ Properties              [+ Add Property]    │
│                                             │
│ [ ] Compare Mode                            │
│                                             │
│ [Property Cards...]                         │
└─────────────────────────────────────────────┘
```

**Properties List (Compare Mode ON, 2 selected):**
```
┌─────────────────────────────────────────────┐
│ Properties              [+ Add Property]    │
│                                             │
│ [✓] Compare Mode  Select 2-5 properties     │
│     Clear Selection (2)                     │
│                                             │
│ ┌──────┐  ┌──────┐  ┌──────┐               │
│ │☑ Card│  │☑ Card│  │☐ Card│               │
│ │PINK  │  │PINK  │  │GRAY  │               │
│ └──────┘  └──────┘  └──────┘               │
│                                             │
│                   [Compare Selected (2)] ←  │
│                   Floating button           │
└─────────────────────────────────────────────┘
```

---

## Common Issues & Solutions

### Issue: Checkbox not visible
**Solution:** Ensure z-index is set on checkbox container: `z-10`

### Issue: Card click still navigates in compare mode
**Solution:** Check that `onClick` prevents default when `compareMode === true`

### Issue: Selection doesn't update
**Solution:** Verify `handlePropertySelect` is correctly updating state

### Issue: Compare button doesn't appear
**Solution:** Check that `selectedPropertyIds.length >= 2` condition is correct

---

## Next Steps

Once Phase 1 is complete and tested:
1. Commit changes: `git commit -m "feat: add property comparison selection UI (Phase 1)"`
2. Move to Phase 2: Build comparison grid with data fetching
3. Reference `COMPARISON_DASHBOARD_SPEC.md` for Phase 2 details

---

**You're ready to build!** Start with Step 1 and work through sequentially.
