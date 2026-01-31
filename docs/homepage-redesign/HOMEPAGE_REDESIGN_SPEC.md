# Homepage Redesign - Dual View with Intelligence Layer

**Project:** FionaFast Property Onboarding Agent
**Feature:** Smart Property Overview with Card/Table Views
**Date:** 2026-01-30
**Status:** Ready for Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Design Concept](#design-concept)
3. [View Modes](#view-modes)
4. [Intelligence Layer](#intelligence-layer)
5. [Filtering & Sorting](#filtering--sorting)
6. [Implementation Phases](#implementation-phases)
7. [Component Specifications](#component-specifications)
8. [Data Schema](#data-schema)
9. [Design System](#design-system)

---

## Overview

### Vision

Transform the properties list from a simple alphabetical grid into a smart, dual-view dashboard that:
- Automatically surfaces properties needing attention
- Provides flexible viewing modes (Cards for browsing, Table for analysis)
- Enables powerful filtering and sorting
- Shows actionable intelligence (stale data alerts, missing extractions)

### Key Features

- **Dual View Modes:** Toggle between Card grid and Table list
- **Smart Categorization:** Auto-group into "Needs Attention", "Up to Date", etc.
- **Intelligence Layer:** Status badges, insights, contextual alerts
- **Unified Filtering:** City, rating, data health across both views
- **Bulk Operations:** Multi-select and bulk actions in table view

### Success Criteria

- Users can quickly identify properties needing attention
- Switching between views is seamless (<200ms)
- Same intelligence layer works in both views
- Table view enables efficient data comparison
- Filtering/sorting is intuitive and powerful

---

## Design Concept

### The Hybrid Approach

**One data model, two presentation modes:**

```
Properties Data
      ↓
Intelligence Layer (categorization, badges, insights)
      ↓
    ┌───┴───┐
Card View  Table View
```

**User Mental Model:**
1. Filter/sort to find what I need
2. Choose how to view it (cards or table)
3. Take action (refresh, compare, view details)

---

## View Modes

### Card View (Visual Browsing)

**Best for:**
- Quick visual scanning
- Seeing property images
- Getting overall portfolio feel
- Mobile/tablet interfaces
- Presenting to stakeholders

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🚨 NEEDS ATTENTION (2)                                      │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 📸 [Image] Sunset Towers              🔴 Stale        │   │
│ │            1548 6th St, Santa Monica, CA              │   │
│ │            ⭐ 4.2 (127) • $1,450+ • 3 units          │   │
│ │            ⚠️ Data not updated in 32 days            │   │
│ │            [Refresh] [Compare] [View]                 │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                             │
│ 🟢 UP TO DATE (5)                         [Collapse ▲]     │
│ ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│ │ 📸 [Img]   │  │ 📸 [Img]   │  │ 📸 [Img]   │            │
│ │ Park View  │  │ Lakeside   │  │ Met Lofts  │            │
│ │ ⭐ 4.7 🟢  │  │ ⭐ 4.5 🟢  │  │ ⭐ 4.7 🟢  │            │
│ │ $1,650+    │  │ $1,500+    │  │ $1,650+    │            │
│ └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

**Card Components:**
- Property image thumbnail
- Status badge (top-right corner)
- Property name and address
- Quick stats: ⭐ Rating (count) • $Price+ • Units available
- Smart insight (one-line alert)
- Quick actions row

---

### Table View (Data Analysis)

**Best for:**
- Comparing specific metrics
- Sorting by multiple dimensions
- Bulk actions (select multiple, compare)
- Finding specific data quickly
- Data management workflows

**Layout:**
```
┌──────────────────────────────────────────────────────────────────────────┐
│ 🚨 NEEDS ATTENTION (2)                                                   │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ ☐ │Status│ Property      │ Location     │Rating│Price │Units│Days │  │
│ ├───┼──────┼───────────────┼──────────────┼──────┼──────┼─────┼─────┤  │
│ │ ☐ │ 🔴   │ Sunset Towers │ Santa Monica │⭐4.2 │$1,450│ 3   │ 32d │  │
│ │   │Stale │               │ CA           │(127) │      │     │⚠️   │  │
│ │   │      │ ⚠️ Data not updated in 32 days                         │  │
│ │   │      │ [Refresh] [Compare] [View]                             │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│ 🟢 UP TO DATE (5)                                    [Collapse ▲]       │
│ ┌────────────────────────────────────────────────────────────────────┐  │
│ │ ☐ │Status│ Property      │ Location     │Rating│Price │Units│Days │  │
│ ├───┼──────┼───────────────┼──────────────┼──────┼──────┼─────┼─────┤  │
│ │ ☐ │ 🟢   │ Park View Apts│ Los Angeles  │⭐4.7 │$1,650│ 0   │ 2d  │  │
│ │ ☐ │ 🟢   │ Lakeside Res  │ Riverside    │⭐4.5 │$1,500│ 1   │ 3d  │  │
│ │ ☐ │ 🟢   │ Met Lofts     │ Los Angeles  │⭐4.7 │$1,650│ 0   │ 5d  │  │
│ └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│ [ 0 selected ]                        [Compare Selected] [Refresh All]  │
└──────────────────────────────────────────────────────────────────────────┘
```

**Table Features:**
- Sortable columns (click header)
- Multi-select checkboxes
- Expandable rows (click to show insights/actions)
- Bulk action bar (when items selected)
- Compact data presentation

**Columns:**
1. Checkbox - Multi-select
2. Status - Health indicator badge
3. Property - Name (clickable)
4. Location - City, State
5. Rating - Stars + review count
6. Price - Starting price
7. Units - Available units
8. Days - Days since last update

---

## Intelligence Layer

### Smart Categorization

Properties automatically organize into sections based on data health:

| Section | Criteria | Badge | Default State |
|---------|----------|-------|---------------|
| 🚨 **Needs Attention** | `updated_at > 30 days ago` OR missing critical data | 🔴 Red | Expanded |
| 🟡 **Partial Data** | Missing optional extractions | 🟡 Yellow | Collapsed |
| 🟢 **Up to Date** | All data current (<30 days) | 🟢 Green | Collapsed |
| 🆕 **Recently Added** | `created_at < 7 days ago` | 🆕 NEW | Expanded |

### Status Badges

| Badge | Label | Meaning | Trigger |
|-------|-------|---------|---------|
| 🔴 | Stale | Data not refreshed recently | `updated_at > 30 days` |
| 🟡 | Partial | Some data missing | Missing optional fields |
| 🟢 | Complete | All data current | All fields populated, `updated_at < 30 days` |
| 🆕 | NEW | Recently onboarded | `created_at < 7 days` |

### Smart Insights

Contextual alerts shown in card footer / expandable table row:

| Insight | Condition | Action Button |
|---------|-----------|---------------|
| "⚠️ Data not updated in X days" | `days_since_update > 30` | [Refresh Data] |
| "📊 Missing floor plan data" | `floor_plans.count = 0` | [Extract Floor Plans] |
| "⭐ No reviews data on file" | `reviews_summary = null` | [Extract Reviews] |
| "🎁 No special offers extracted" | `special_offers.count = 0` | [Extract Offers] |
| "🏢 Missing amenities data" | `amenities = null` | [Extract Amenities] |
| "📸 No images collected" | `images.count = 0` | [Extract Images] |

---

## Filtering & Sorting

### Unified Filter Bar (Works for Both Views)

```
┌──────────────────────────────────────────────────────────────┐
│ 🔍 [Search properties by name...]                           │
│                                                              │
│ Sort: [Needs Attention ▼]   View: [■■■ Cards] [≡ Table]    │
│                                                              │
│ Filter:                                                      │
│   Location: [All Cities ▼] [+ Santa Monica, Venice]        │
│   Rating:   [4.0+ stars ████████░░] (slider: 0-5.0)        │
│   Data:     [● All  ○ Complete  ○ Partial  ○ Stale]       │
│   Units:    [☑ Has units available]                        │
│   Offers:   [☐ Has special offers]                         │
└──────────────────────────────────────────────────────────────┘
```

### Sort Options

| Option | Logic | Use Case |
|--------|-------|----------|
| **Needs Attention** ⭐ | Stale/incomplete first | Default - find problems |
| Recently Added | `created_at DESC` | See new properties |
| Alphabetical | `property_name ASC` | Find by name |
| Rating (High to Low) | `rating DESC` | Best properties first |
| Price (Low to High) | `starting_price ASC` | Cheapest first |
| Last Updated | `updated_at ASC` | Find stalest data |

### Filter Options

**Location (Multi-select):**
- Extract unique cities from properties
- Allow multiple city selection
- "All Cities" clears filter

**Rating Range (Slider):**
- Min: 0 stars
- Max: 5 stars
- Default: All (0-5)
- Example: "4.0+ stars only"

**Data Health (Radio):**
- ● All (default)
- ○ Complete (all data current)
- ○ Partial (missing some data)
- ○ Stale (not updated >30 days)

**Availability (Checkbox):**
- ☑ Has units available (available_units > 0)
- ☐ Show all

**Special Offers (Checkbox):**
- ☑ Has active offers (special_offers.count > 0)
- ☐ Show all

---

## Implementation Phases

### Phase 1: Table View Toggle (4-6 hours)

**Goal:** Basic dual-view with table/card toggle

**Tasks:**
- [ ] Add view mode state (`'card' | 'table'`)
- [ ] Create view toggle button (Card/Table icons)
- [ ] Create PropertyTable component with basic columns
- [ ] Add sortable column headers
- [ ] Conditional render based on view mode
- [ ] Style table to match design system

**Deliverables:**
- Users can toggle between card grid and table list
- Same data shown in both views
- Columns are sortable

---

### Phase 2: Intelligence Layer in Table (6-8 hours)

**Goal:** Add smart insights and status to table

**Tasks:**
- [ ] Add expandable row functionality (click to expand)
- [ ] Calculate data health status per property
- [ ] Show status badge in Status column
- [ ] Show smart insights in expanded row
- [ ] Add quick action buttons in expanded row
- [ ] Style expanded rows consistently

**Deliverables:**
- Table rows can expand to show details
- Status badges appear in table
- Same insights as card view

---

### Phase 3: Smart Categorization (4-6 hours)

**Goal:** Auto-group properties by health status

**Tasks:**
- [ ] Implement categorization logic
- [ ] Create collapsible section headers
- [ ] Render sections: Needs Attention, Partial, Up to Date, Recent
- [ ] Default expand/collapse states
- [ ] Works in both card and table views

**Deliverables:**
- Properties auto-organize into sections
- "Needs Attention" always expanded
- Collapsible section headers

---

### Phase 4: Multi-Select & Bulk Actions (4-6 hours)

**Goal:** Enable bulk operations in table view

**Tasks:**
- [ ] Add checkboxes to table rows
- [ ] Track selected property IDs in state
- [ ] Show bulk action bar when items selected
- [ ] Implement "Compare Selected" (navigate to compare page)
- [ ] Implement "Refresh All Selected" (trigger re-extraction)
- [ ] Add "Clear Selection" action

**Deliverables:**
- Users can select multiple properties
- Bulk action bar appears
- Compare and refresh work with selected items

---

### Phase 5: Enhanced Filtering & Search (6-8 hours)

**Goal:** Rich filtering across both views

**Tasks:**
- [ ] Add search input (filter by name)
- [ ] Implement city multi-select dropdown
- [ ] Add rating range slider
- [ ] Add data health radio buttons
- [ ] Add availability checkbox
- [ ] Add special offers checkbox
- [ ] Update URL params with filter state
- [ ] Restore filters from URL on load

**Deliverables:**
- Full filtering toolbar
- Filters apply to both views
- Filter state persists in URL

---

### Phase 6: Polish & UX Enhancements (4-6 hours)

**Goal:** Smooth experience with preferences

**Tasks:**
- [ ] Smooth view toggle animation
- [ ] Save view preference to localStorage
- [ ] Add empty states ("No properties match filters")
- [ ] Add loading skeleton states
- [ ] Keyboard shortcuts (arrow keys in table)
- [ ] Optimize performance (virtualization if needed)

**Deliverables:**
- Professional, polished UX
- User preferences saved
- Fast, smooth interactions

---

## Component Specifications

### 1. FilterBar

**Purpose:** Unified filtering/sorting/view controls

**Props:**
```typescript
interface FilterBarProps {
  viewMode: 'card' | 'table';
  onViewModeChange: (mode: 'card' | 'table') => void;
  sortBy: SortOption;
  onSortChange: (sort: SortOption) => void;
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
}

type SortOption =
  | 'needs-attention'
  | 'recent'
  | 'alphabetical'
  | 'rating'
  | 'price'
  | 'last-updated';

interface Filters {
  search: string;
  cities: string[];
  ratingMin: number | null;
  dataHealth: 'all' | 'complete' | 'partial' | 'stale';
  hasUnits: boolean | null;
  hasOffers: boolean | null;
}
```

**Behavior:**
- Shows all filter controls
- View toggle triggers mode change
- Filter changes trigger re-render of property list

---

### 2. PropertySection

**Purpose:** Collapsible section for categorized properties

**Props:**
```typescript
interface PropertySectionProps {
  title: string;
  badge: '🚨' | '🟡' | '🟢' | '🆕';
  count: number;
  defaultExpanded: boolean;
  viewMode: 'card' | 'table';
  properties: PropertyWithHealth[];
  onPropertySelect?: (id: string, selected: boolean) => void;
  selectedIds?: string[];
}
```

**Behavior:**
- Section header with badge, title, count
- Click header to expand/collapse
- Renders PropertyList in chosen view mode

---

### 3. PropertyCard (Enhanced)

**Purpose:** Card view representation with intelligence

**Props:**
```typescript
interface PropertyCardProps {
  property: PropertyWithHealth;
  onRefresh?: (id: string) => void;
  onCompare?: (id: string) => void;
}

interface PropertyWithHealth extends Property {
  healthStatus: 'stale' | 'partial' | 'complete' | 'new';
  daysSinceUpdate: number;
  insights: Insight[];
  missingData: string[];
  hasImage: boolean;
  imageUrl?: string;
}

interface Insight {
  type: 'warning' | 'info' | 'error';
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}
```

**Layout:**
```
┌──────────────────────────────────────┐
│ 📸 [Image]              🔴 Badge     │
│                                      │
│ Property Name                        │
│ Address                              │
│                                      │
│ ⭐ 4.2 (127) • $1,450+ • 3 units    │
│                                      │
│ ⚠️ Insight message                  │
│                                      │
│ [Action 1] [Action 2] [View]         │
└──────────────────────────────────────┘
```

---

### 4. PropertyTable

**Purpose:** Table view with sortable columns and expandable rows

**Props:**
```typescript
interface PropertyTableProps {
  properties: PropertyWithHealth[];
  sortBy: string;
  sortDirection: 'asc' | 'desc';
  onSort: (column: string) => void;
  selectedIds: string[];
  onSelect: (id: string, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
}
```

**Columns:**
```typescript
const columns = [
  { key: 'select', label: '', width: '40px' },
  { key: 'status', label: 'Status', width: '80px', sortable: false },
  { key: 'name', label: 'Property', width: '200px', sortable: true },
  { key: 'location', label: 'Location', width: '150px', sortable: true },
  { key: 'rating', label: 'Rating', width: '100px', sortable: true },
  { key: 'price', label: 'Price', width: '100px', sortable: true },
  { key: 'units', label: 'Units', width: '80px', sortable: true },
  { key: 'updated', label: 'Updated', width: '100px', sortable: true }
];
```

**Behavior:**
- Click column header to sort
- Click row to expand (show insights)
- Checkbox selection
- Sticky header on scroll

---

### 5. BulkActionBar

**Purpose:** Actions for selected properties (table view only)

**Props:**
```typescript
interface BulkActionBarProps {
  selectedCount: number;
  onCompare: () => void;
  onRefreshAll: () => void;
  onClear: () => void;
}
```

**Layout:**
```
┌────────────────────────────────────────────────────────┐
│ 3 properties selected  [Compare] [Refresh All] [Clear]│
└────────────────────────────────────────────────────────┘
```

---

## Data Schema

### Enhanced Property Type

```typescript
interface PropertyWithHealth extends Property {
  // Calculated health fields
  healthStatus: 'stale' | 'partial' | 'complete' | 'new';
  daysSinceUpdate: number;
  dataCompleteness: number; // 0-100%

  // Insights
  insights: Insight[];
  missingData: MissingDataType[];

  // Quick stats
  hasFloorPlans: boolean;
  hasReviews: boolean;
  hasAmenities: boolean;
  hasSpecialOffers: boolean;
  hasImages: boolean;
  hasCompetitors: boolean;

  // Display helpers
  imageUrl?: string;
  startingPrice?: number;
  availableUnits?: number;
}

type MissingDataType =
  | 'floor_plans'
  | 'reviews'
  | 'amenities'
  | 'special_offers'
  | 'images'
  | 'competitors'
  | 'branding';

interface Insight {
  type: 'warning' | 'info' | 'error';
  message: string;
  priority: number; // 1-5, higher = more urgent
  action?: {
    label: string;
    route: string; // e.g., '/properties/123/extract/floor-plans'
  };
}
```

---

## Design System

### Colors

```typescript
// Status colors
const statusColors = {
  stale: {
    bg: '#FEE2E2',    // Red-100
    text: '#991B1B',  // Red-800
    border: '#EF4444' // Red-500
  },
  partial: {
    bg: '#FEF3C7',    // Yellow-100
    text: '#92400E',  // Yellow-800
    border: '#F59E0B' // Yellow-500
  },
  complete: {
    bg: '#D1FAE5',    // Green-100
    text: '#065F46',  // Green-800
    border: '#10B981' // Green-500
  },
  new: {
    bg: '#E0E7FF',    // Indigo-100
    text: '#3730A3',  // Indigo-800
    border: '#6366F1' // Indigo-500
  }
};
```

### Typography

```typescript
// Table typography
const tableStyles = {
  headerText: 'text-sm font-semibold text-neutral-700',
  cellText: 'text-sm text-neutral-900',
  expandedText: 'text-sm text-neutral-600',
  actionButton: 'text-xs font-medium'
};
```

### Spacing

```typescript
// Table spacing
const tablePadding = {
  cell: 'px-4 py-3',
  header: 'px-4 py-3',
  expandedRow: 'px-4 py-3 bg-neutral-50'
};
```

---

## Testing Checklist

### Phase 1: Table View
- [ ] View toggle switches between card and table
- [ ] Table displays all properties correctly
- [ ] Column sorting works (click header)
- [ ] Table layout is responsive
- [ ] Both views show same data

### Phase 2: Intelligence Layer
- [ ] Status badges appear correctly
- [ ] Rows can expand/collapse
- [ ] Insights show in expanded rows
- [ ] Quick actions work
- [ ] Calculations accurate (days since update, etc.)

### Phase 3: Categorization
- [ ] Properties auto-group correctly
- [ ] "Needs Attention" section appears when relevant
- [ ] Sections can expand/collapse
- [ ] Default states correct (Needs Attention expanded)

### Phase 4: Bulk Actions
- [ ] Checkboxes work in table
- [ ] Bulk action bar appears when items selected
- [ ] "Compare Selected" navigates correctly
- [ ] "Refresh All" triggers extractions
- [ ] "Clear" deselects all

### Phase 5: Filtering
- [ ] Search filters by name
- [ ] City filter works
- [ ] Rating slider works
- [ ] Data health filter works
- [ ] Filters combine correctly (AND logic)
- [ ] URL params update with filters
- [ ] Filters restore from URL

### Phase 6: Polish
- [ ] View toggle animation smooth
- [ ] Preferences save to localStorage
- [ ] Empty states show correctly
- [ ] Loading states work
- [ ] Keyboard shortcuts functional
- [ ] Performance acceptable (100+ properties)

---

**Ready to build!** Start with Phase 1 and work incrementally through the phases.
