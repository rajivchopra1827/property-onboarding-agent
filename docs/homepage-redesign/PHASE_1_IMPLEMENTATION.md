# Phase 1: Table View Toggle - Detailed Implementation Guide

**Goal:** Add basic dual-view with card/table toggle

**Estimated Time:** 4-6 hours

---

## Overview

This phase adds the ability to:
1. Toggle between Card view (current grid) and Table view (new)
2. Display same property data in both formats
3. Enable column sorting in table view
4. Maintain existing filtering/sorting logic

---

## Step-by-Step Implementation

### Step 1: Add View Mode State

**File:** `frontend/app/properties/page.tsx`

Add view mode state at the top of the component:

```typescript
export default function PropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  // NEW: View mode state
  const [viewMode, setViewMode] = useState<'card' | 'table'>('card');
  const [sortBy, setSortBy] = useState<string>('name'); // For table sorting
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // ... rest of component
}
```

---

### Step 2: Create View Toggle Component

Add this component inside `PropertiesPage`, after the header:

```typescript
{/* View Toggle */}
<div className="mb-6 flex items-center justify-between">
  <div className="flex items-center gap-2">
    <span className="text-sm text-neutral-600">View:</span>
    <div className="flex border border-neutral-300 rounded-lg overflow-hidden">
      <button
        onClick={() => setViewMode('card')}
        className={`
          px-4 py-2 text-sm font-medium transition-colors
          ${viewMode === 'card'
            ? 'bg-primary-500 text-white'
            : 'bg-white text-neutral-700 hover:bg-neutral-50'
          }
        `}
        aria-label="Card view"
      >
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
      </button>
      <button
        onClick={() => setViewMode('table')}
        className={`
          px-4 py-2 text-sm font-medium transition-colors border-l border-neutral-300
          ${viewMode === 'table'
            ? 'bg-primary-500 text-white'
            : 'bg-white text-neutral-700 hover:bg-neutral-50'
          }
        `}
        aria-label="Table view"
      >
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
        </svg>
      </button>
    </div>
  </div>
</div>
```

---

### Step 3: Create PropertyTable Component

**Create:** `frontend/app/components/PropertyTable.tsx`

```typescript
'use client';

import Link from 'next/link';
import { Property } from '@/lib/types';

interface PropertyTableProps {
  properties: Property[];
  sortBy: string;
  sortDirection: 'asc' | 'desc';
  onSort: (column: string) => void;
}

export default function PropertyTable({
  properties,
  sortBy,
  sortDirection,
  onSort
}: PropertyTableProps) {
  const getDisplayName = (property: Property) => {
    if (property.property_name) return property.property_name;
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

  const getLocation = (property: Property) => {
    const parts = [property.city, property.state].filter(Boolean);
    return parts.length > 0 ? parts.join(', ') : '—';
  };

  const handleSort = (column: string) => {
    onSort(column);
  };

  const SortIcon = ({ column }: { column: string }) => {
    if (sortBy !== column) {
      return (
        <svg className="w-4 h-4 text-neutral-400" fill="currentColor" viewBox="0 0 20 20">
          <path d="M5 12a1 1 0 102 0V6.414l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L5 6.414V12zM15 8a1 1 0 10-2 0v5.586l-1.293-1.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L15 13.586V8z" />
        </svg>
      );
    }
    return sortDirection === 'asc' ? (
      <svg className="w-4 h-4 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
        <path d="M3 3a1 1 0 000 2h11a1 1 0 100-2H3zM3 7a1 1 0 000 2h7a1 1 0 100-2H3zM3 11a1 1 0 100 2h4a1 1 0 100-2H3zM15 8a1 1 0 10-2 0v5.586l-1.293-1.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L15 13.586V8z" />
      </svg>
    ) : (
      <svg className="w-4 h-4 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
        <path d="M3 3a1 1 0 000 2h11a1 1 0 100-2H3zM3 7a1 1 0 000 2h5a1 1 0 000-2H3zM3 11a1 1 0 100 2h4a1 1 0 100-2H3zM13 16a1 1 0 102 0v-5.586l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 101.414 1.414L13 10.414V16z" />
      </svg>
    );
  };

  return (
    <div className="bg-white rounded-lg border border-neutral-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-neutral-200">
          <thead className="bg-neutral-50">
            <tr>
              <th
                onClick={() => handleSort('name')}
                className="px-6 py-3 text-left text-xs font-medium text-neutral-700 uppercase tracking-wider cursor-pointer hover:bg-neutral-100 transition-colors"
              >
                <div className="flex items-center gap-2">
                  Property
                  <SortIcon column="name" />
                </div>
              </th>
              <th
                onClick={() => handleSort('location')}
                className="px-6 py-3 text-left text-xs font-medium text-neutral-700 uppercase tracking-wider cursor-pointer hover:bg-neutral-100 transition-colors"
              >
                <div className="flex items-center gap-2">
                  Location
                  <SortIcon column="location" />
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-neutral-700 uppercase tracking-wider">
                Website
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-neutral-700 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-neutral-200">
            {properties.map((property) => (
              <tr
                key={property.id}
                className="hover:bg-neutral-50 transition-colors"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <Link
                    href={`/properties/${property.id}`}
                    className="text-sm font-medium text-neutral-900 hover:text-primary-500"
                  >
                    {getDisplayName(property)}
                  </Link>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-neutral-700">
                    {getLocation(property)}
                  </div>
                </td>
                <td className="px-6 py-4">
                  {property.website_url && (
                    <a
                      href={property.website_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-500 hover:text-primary-600 truncate block max-w-xs"
                    >
                      {property.website_url}
                    </a>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <Link
                    href={`/properties/${property.id}`}
                    className="text-primary-500 hover:text-primary-600 font-medium"
                  >
                    View Details →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {properties.length === 0 && (
        <div className="text-center py-12 text-neutral-600">
          No properties found
        </div>
      )}
    </div>
  );
}
```

---

### Step 4: Add Sort Logic

Add sorting function in `PropertiesPage`:

```typescript
const handleSort = (column: string) => {
  if (sortBy === column) {
    // Toggle direction if same column
    setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
  } else {
    // New column, default to ascending
    setSortBy(column);
    setSortDirection('asc');
  }
};

// Sort properties based on current sort state
const sortedProperties = useMemo(() => {
  if (viewMode !== 'table') return properties;

  return [...properties].sort((a, b) => {
    let aValue: any;
    let bValue: any;

    switch (sortBy) {
      case 'name':
        aValue = a.property_name || a.website_url || '';
        bValue = b.property_name || b.website_url || '';
        break;
      case 'location':
        aValue = [a.city, a.state].filter(Boolean).join(', ');
        bValue = [b.city, b.state].filter(Boolean).join(', ');
        break;
      default:
        return 0;
    }

    if (sortDirection === 'asc') {
      return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
    } else {
      return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
    }
  });
}, [properties, sortBy, sortDirection, viewMode]);
```

---

### Step 5: Conditional Rendering

Replace the existing properties grid with conditional rendering:

```typescript
{/* Properties Display - Card or Table View */}
{properties.length === 0 ? (
  <div className="text-center py-16">
    <p className="text-lg text-neutral-800">
      No properties found. Start by extracting information from a property website.
    </p>
  </div>
) : viewMode === 'card' ? (
  // Card View (existing grid)
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {sortedProperties.map((property) => (
      <Link
        key={property.id}
        href={`/properties/${property.id}`}
        className="block bg-white rounded-lg border border-neutral-200 p-6 shadow-md transition-all duration-300 hover:shadow-lg hover:-translate-y-1 hover:border-primary-200 focus:outline-none focus:ring-4 focus:ring-primary-300"
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
        <div className="mt-4 text-sm text-primary-500 font-medium">
          View Details →
        </div>
      </Link>
    ))}
  </div>
) : (
  // Table View (new)
  <PropertyTable
    properties={sortedProperties}
    sortBy={sortBy}
    sortDirection={sortDirection}
    onSort={handleSort}
  />
)}
```

---

### Step 6: Import PropertyTable

Add import at top of `page.tsx`:

```typescript
import PropertyTable from '@/app/components/PropertyTable';
```

---

## Testing Checklist

After implementing, test these scenarios:

### View Toggle
- [ ] **Card view shows by default** - Properties display as grid
- [ ] **Click table button** - View switches to table layout
- [ ] **Click card button** - View switches back to card grid
- [ ] **Same properties in both views** - Count matches
- [ ] **Visual feedback** - Active view button highlighted

### Table View
- [ ] **Table displays correctly** - All properties shown
- [ ] **Columns aligned** - Headers match data
- [ ] **Property name clickable** - Links to detail page
- [ ] **Website links work** - Open in new tab
- [ ] **"View Details" links work** - Navigate to detail page

### Table Sorting
- [ ] **Click "Property" header** - Sorts alphabetically A-Z
- [ ] **Click "Property" again** - Reverses to Z-A
- [ ] **Sort icon updates** - Shows up/down arrow correctly
- [ ] **Click "Location" header** - Sorts by city/state
- [ ] **Active column highlighted** - Visual indicator present

### Responsive Behavior
- [ ] **Desktop (1280px+)** - Table fits comfortably
- [ ] **Tablet (768px)** - Table scrolls horizontally if needed
- [ ] **Mobile (375px)** - Card view recommended, table scrollable

---

## Visual Result

### Card View (Existing - Enhanced)
```
┌─────────────────────────────────────────────┐
│ Properties              [+ Add Property]    │
│                                             │
│ View: [■■■ Selected] [≡ Outline]           │
│       ↑ Cards        ↑ Table                │
│                                             │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│ │ Card     │  │ Card     │  │ Card     │   │
│ │ Sunset   │  │ Park     │  │ Harbor   │   │
│ │ Towers   │  │ View     │  │ Heights  │   │
│ └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────┘
```

### Table View (New)
```
┌──────────────────────────────────────────────────────────┐
│ Properties                        [+ Add Property]       │
│                                                          │
│ View: [■■■ Outline] [≡ Selected]                        │
│       ↑ Cards       ↑ Table                              │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ Property ↑    │ Location ↓  │ Website  │ Actions  │  │
│ ├──────────────┼─────────────┼──────────┼──────────┤  │
│ │ Harbor       │ Riverside   │ link     │ View →   │  │
│ │ Met Lofts    │ LA          │ link     │ View →   │  │
│ │ Park View    │ LA          │ link     │ View →   │  │
│ │ Sunset       │ Santa Mon   │ link     │ View →   │  │
│ └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## Common Issues & Solutions

### Issue: Table not displaying
**Solution:** Check PropertyTable import path, ensure component exported correctly

### Issue: Sort not working
**Solution:** Verify sortedProperties useMemo dependencies, check sort logic

### Issue: Toggle button not highlighting
**Solution:** Check conditional className logic: `viewMode === 'card'` condition

### Issue: Horizontal scroll on mobile
**Solution:** Add `overflow-x-auto` to table wrapper div

### Issue: Click anywhere in row navigates
**Solution:** Only property name should be `<Link>`, keep row as `<tr>`

---

## Next Steps

Once Phase 1 is complete and tested:
1. Commit changes: `git commit -m "feat: add table view toggle (Phase 1)"`
2. Move to Phase 2: Intelligence Layer in Table
3. Reference `HOMEPAGE_REDESIGN_SPEC.md` for Phase 2 details

---

**You're ready to build!** Start with Step 1 and work through sequentially.
