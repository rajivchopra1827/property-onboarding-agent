# Property Comparison Dashboard - Implementation Specification

**Project:** FionaFast Property Onboarding Agent
**Feature:** Property Comparison Dashboard
**Date:** 2026-01-30
**Status:** Ready for Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [User Flow](#user-flow)
3. [Technical Architecture](#technical-architecture)
4. [Implementation Phases](#implementation-phases)
5. [Design System](#design-system)
6. [Component Specifications](#component-specifications)
7. [Data Schema](#data-schema)
8. [API Requirements](#api-requirements)
9. [Testing Strategy](#testing-strategy)

---

## Overview

### Vision

A side-by-side property comparison tool that enables rapid multi-property decision-making by surfacing key differences through visual hierarchy, calculated insights, and intelligent highlighting.

### Key Features

- **Multi-select comparison mode** on properties list page
- **Side-by-side column comparison** with sticky headers
- **Calculated insights** (price/sqft, review confidence, amenity density)
- **Visual differentiation** (green highlights for best values, crown icons)
- **Collapsible sections** for progressive disclosure
- **PDF export** for stakeholder sharing
- **Responsive design** (desktop columns, tablet scroll, mobile cards)

### Success Criteria

- Users can select 2-5 properties and compare in <5 seconds
- Key differences (price, rating, amenities) are obvious at a glance
- Comparison view works seamlessly on desktop and tablet
- PDF export preserves information hierarchy

---

## User Flow

### Selection Flow (Properties List Page)

```
1. User navigates to /properties
2. User toggles "Compare Mode" switch
3. Checkboxes appear on property cards
4. User selects 2-5 properties (checked state with pink border glow)
5. Floating action button appears: "Compare Selected (N)"
6. User clicks compare button
7. Navigate to /properties/compare?ids=uuid1,uuid2,uuid3
```

### Comparison View Flow

```
1. Page loads with property IDs from query params
2. Fetch all property data in parallel (properties, floor_plans, amenities, reviews, etc.)
3. Render comparison grid with:
   - Fixed property headers (names, ratings)
   - Quick Metrics section (always visible)
   - Collapsible detail sections (Floor Plans, Amenities, Reviews, etc.)
4. User can:
   - Scroll vertically through sections
   - Scroll horizontally (if needed on smaller screens)
   - Expand/collapse sections
   - Export to PDF
   - Return to properties list
```

---

## Technical Architecture

### Routes

```
/properties                    # Existing - add comparison mode
/properties/compare            # New - comparison view
```

### Key Technologies

- **Next.js 14** (App Router)
- **React 18** (Client Components for interactivity)
- **Supabase** (Database queries)
- **Tailwind CSS** (Styling)
- **react-pdf** or **jsPDF** (PDF export)

### Data Flow

```
Properties List Page
  ↓
  useState for selectedPropertyIds: string[]
  ↓
  Navigate with query params: ?ids=id1,id2,id3
  ↓
Comparison Page
  ↓
  useSearchParams to extract IDs
  ↓
  Parallel fetch:
    - properties table
    - property_floor_plans table
    - property_amenities table
    - property_reviews_summary table
    - property_special_offers table
  ↓
  Calculate derived metrics (price/sqft, review confidence, etc.)
  ↓
  Render comparison grid
```

---

## Implementation Phases

### Phase 1: Selection UI (Week 1)

**Goal:** Enable property selection and navigation to comparison route

**Files to Modify:**
- `frontend/app/properties/page.tsx`

**Files to Create:**
- `frontend/app/properties/compare/page.tsx` (skeleton)

**Tasks:**
1. Add "Compare Mode" toggle to properties page header
2. Add checkbox overlay to property cards (conditional render)
3. Track selected property IDs in state
4. Add floating action button (fixed bottom, shows when 2+ selected)
5. Add navigation to `/properties/compare?ids=...`
6. Create skeleton comparison page that displays selected property names

**Acceptance Criteria:**
- [ ] Compare mode toggle works (enables/disables checkboxes)
- [ ] Clicking checkboxes updates selection state
- [ ] Selected cards show visual feedback (pink border glow)
- [ ] Floating button shows correct count
- [ ] Button disabled when <2 properties selected
- [ ] Toast warning when attempting to select 6th property
- [ ] Navigation to comparison page works with correct query params
- [ ] Comparison page displays "Comparing: Property1, Property2, ..." as placeholder

---

### Phase 2: Comparison Grid Foundation (Week 2)

**Goal:** Build basic comparison layout with data fetching

**Files to Create:**
- `frontend/app/properties/compare/components/ComparisonHeader.tsx`
- `frontend/app/properties/compare/components/QuickMetricsTable.tsx`
- `frontend/app/properties/compare/hooks/useComparisonData.ts`
- `frontend/lib/types.ts` (add comparison types)

**Tasks:**
1. Implement `useComparisonData` hook for parallel data fetching
2. Create fixed header component with property names and ratings
3. Create Quick Metrics table component (rating, reviews, price ranges)
4. Implement responsive column grid layout (Tailwind)
5. Add loading states (skeleton loaders)
6. Add error handling (missing properties, fetch failures)

**Acceptance Criteria:**
- [ ] All property data fetches in parallel
- [ ] Property headers are sticky on scroll
- [ ] Quick Metrics section displays correctly
- [ ] Layout is responsive (4 cols on desktop, scroll on smaller)
- [ ] Loading state shows skeleton
- [ ] Error state shows helpful message

---

### Phase 3: Rich Comparison Features (Week 3)

**Goal:** Add detailed comparison sections with highlighting

**Files to Create:**
- `frontend/app/properties/compare/components/FloorPlansComparison.tsx`
- `frontend/app/properties/compare/components/AmenitiesMatrix.tsx`
- `frontend/app/properties/compare/components/ReviewsComparison.tsx`
- `frontend/app/properties/compare/components/SpecialOffersGrid.tsx`
- `frontend/app/properties/compare/utils/comparisonHelpers.ts`

**Tasks:**
1. Implement Floor Plans comparison with calculated price/sqft
2. Implement Amenities matrix (checkmark grid)
3. Implement Reviews comparison with sentiment summary
4. Implement Special Offers grid
5. Add "best value" highlighting logic (green backgrounds, crown icons)
6. Add collapsible section behavior
7. Add empty states for missing data

**Acceptance Criteria:**
- [ ] Floor plans show price, sqft, price/sqft, availability
- [ ] Price/sqft calculated correctly per unit type
- [ ] Amenities show checkmark/X/dash for has/missing/unknown
- [ ] Best values highlighted in green with crown icon
- [ ] Sections can expand/collapse smoothly
- [ ] Empty states show when data missing

---

### Phase 4: Export & Polish (Week 4)

**Goal:** Add PDF export and polish UX

**Files to Create:**
- `frontend/app/properties/compare/components/PDFExportButton.tsx`
- `frontend/app/properties/compare/utils/pdfTemplate.ts`

**Tasks:**
1. Implement PDF generation (landscape layout, 4 properties per page)
2. Add export button with loading state
3. Add mobile responsive layout (card-based for <768px)
4. Add smooth animations (expand/collapse, hover states)
5. Add keyboard navigation support
6. Polish styling (spacing, typography, shadows)

**Acceptance Criteria:**
- [ ] PDF export generates correctly with all data
- [ ] PDF preserves highlighting and structure
- [ ] Mobile view uses card layout with dropdowns
- [ ] Animations are smooth (200ms ease-out)
- [ ] Keyboard navigation works (arrow keys between cells)
- [ ] All accessibility requirements met (ARIA labels, focus indicators)

---

## Design System

### Color Palette

```typescript
// Primary (Pink/Purple)
primary-500: '#EC4899'    // Main brand color
primary-600: '#DB2777'    // Hover state
primary-100: '#FCE7F3'    // Light background

// Secondary (Purple)
secondary-700: '#7C3AED'  // Headings

// Semantic Colors for Comparison
success-light: '#B9F6CA'  // Best value background
success-dark: '#1B5E20'   // Best value text
error-light: '#FFCDD2'    // Worst value background
error-dark: '#B71C1C'     // Worst value text

// Neutral
neutral-50: '#FAFAFA'     // Page background
neutral-200: '#E5E5E5'    // Borders
neutral-500: '#737373'    // Secondary text
neutral-900: '#171717'    // Primary text
```

### Typography Scale

```typescript
// Headings
text-4xl: 36px, font-bold     // Page title
text-xl: 20px, font-bold      // Property names
text-lg: 18px, font-semibold  // Section titles

// Body
text-base: 16px, font-normal  // Metric values
text-sm: 14px, font-semibold  // Metric labels
text-xs: 12px, font-semibold  // Badges/tags
```

### Spacing (8px Grid)

```typescript
spacing-2: 8px    // Tight spacing
spacing-4: 16px   // Standard gap
spacing-6: 24px   // Section spacing
spacing-8: 32px   // Large spacing
```

### Shadows

```typescript
shadow-md: '0 4px 6px -1px rgb(0 0 0 / 0.1)'      // Cards
shadow-lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)'    // Hover state
shadow-primary: '0 0 0 3px rgb(236 72 153 / 0.2)' // Selected state
```

---

## Component Specifications

### 1. CompareToggle (in properties/page.tsx)

**Purpose:** Enable/disable comparison mode

**Props:**
```typescript
interface CompareToggleProps {
  isEnabled: boolean;
  onToggle: (enabled: boolean) => void;
}
```

**State:** None (controlled by parent)

**Behavior:**
- Toggle switch UI (Tailwind toggle)
- When enabled: show checkboxes on all property cards
- When disabled: hide checkboxes, clear selections

---

### 2. PropertyCard (modified in properties/page.tsx)

**Purpose:** Display property with optional comparison checkbox

**Props:**
```typescript
interface PropertyCardProps {
  property: Property;
  compareMode: boolean;
  isSelected: boolean;
  onSelect: (propertyId: string, selected: boolean) => void;
}
```

**Behavior:**
- Show checkbox in top-left when compareMode = true
- Add pink border glow when isSelected = true
- Checkbox click calls onSelect
- Card click navigates to detail page (unless compareMode active)

---

### 3. CompareFloatingButton (in properties/page.tsx)

**Purpose:** Show selection count and trigger comparison

**Props:**
```typescript
interface CompareFloatingButtonProps {
  selectedCount: number;
  selectedIds: string[];
  onCompare: () => void;
}
```

**Behavior:**
- Fixed position: bottom-right
- Show when selectedCount >= 2
- Animate in with slide-up
- Display: "Compare Selected (N)"
- Click navigates to /properties/compare?ids=...

---

### 4. ComparisonHeader

**Purpose:** Sticky header with property names and key metrics

**Props:**
```typescript
interface ComparisonHeaderProps {
  properties: PropertyWithData[];
}

interface PropertyWithData {
  property: Property;
  reviewsSummary: PropertyReviewsSummary | null;
}
```

**Layout:**
```
┌────────────┬────────────┬────────────┬────────────┐
│ Property 1 │ Property 2 │ Property 3 │ Property 4 │
│ Logo/Image │ Logo/Image │ Logo/Image │ Logo/Image │
│ Name       │ Name       │ Name       │ Name       │
│ 4.2 ★★★★   │ 4.7 ★★★★★  │ 3.9 ★★★    │ 4.5 ★★★★   │
└────────────┴────────────┴────────────┴────────────┘
```

**Behavior:**
- Sticky position on scroll
- Equal width columns (min 200px, max 280px)
- Horizontal scroll if needed

---

### 5. QuickMetricsTable

**Purpose:** Always-visible comparison of key metrics

**Props:**
```typescript
interface QuickMetricsTableProps {
  properties: PropertyWithData[];
}
```

**Metrics to Display:**
- Overall Rating
- Review Count
- Starting Price (Studio or lowest tier)
- 1BR Price
- 2BR Price

**Behavior:**
- Light gray background to separate from detail sections
- Best value in each row gets green background + crown icon
- Numeric values right-aligned

---

### 6. FloorPlansComparison

**Purpose:** Detailed floor plan comparison

**Props:**
```typescript
interface FloorPlansComparisonProps {
  properties: PropertyWithFloorPlans[];
}

interface PropertyWithFloorPlans {
  property: Property;
  floorPlans: PropertyFloorPlan[];
}
```

**Calculated Fields:**
- Price per Sqft = `min_price / size_sqft`

**Layout:**
- Group by bedroom count (Studio, 1BR, 2BR, etc.)
- Show: Name, Price, Sqft, Price/Sqft, Availability
- Highlight best price/sqft with green background

**Behavior:**
- Collapsible section (starts expanded)
- Empty state: "No floor plans available"

---

### 7. AmenitiesMatrix

**Purpose:** Checkmark grid for amenity comparison

**Props:**
```typescript
interface AmenitiesMatrixProps {
  properties: PropertyWithAmenities[];
}

interface PropertyWithAmenities {
  property: Property;
  amenities: PropertyAmenities | null;
}
```

**Behavior:**
- Create union of all amenities across properties
- For each amenity, show:
  - ✓ (green checkmark) if property has it
  - ✗ (red X) if property doesn't have it
  - – (gray dash) if unknown
- Separate Building vs Apartment amenities

---

### 8. ReviewsComparison

**Purpose:** Review summary comparison

**Props:**
```typescript
interface ReviewsComparisonProps {
  properties: PropertyWithReviews[];
}

interface PropertyWithReviews {
  property: Property;
  reviewsSummary: PropertyReviewsSummary | null;
}
```

**Display:**
- Rating (stars + number)
- Review count
- Sentiment summary (2-3 lines from AI)
- Link to full reviews

---

### 9. PDFExportButton

**Purpose:** Generate PDF export of comparison

**Props:**
```typescript
interface PDFExportButtonProps {
  properties: PropertyWithData[];
}
```

**Behavior:**
- Button in top-right of comparison page
- Click shows loading spinner
- Generate PDF in landscape orientation
- Include: Property headers, Quick Metrics, Floor Plans, Amenities
- Auto-download with filename: `property-comparison-YYYY-MM-DD.pdf`

---

## Data Schema

### TypeScript Interfaces

```typescript
// Existing types (from lib/types.ts)
interface Property {
  id: string;
  property_name: string | null;
  street_address: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  phone: string | null;
  email: string | null;
  office_hours: Record<string, any> | null;
  website_url: string | null;
  created_at: string;
  updated_at: string;
}

interface PropertyFloorPlan {
  id: string;
  property_id: string;
  name: string;
  size_sqft: number | null;
  bedrooms: number | null;
  bathrooms: number | null;
  price_string: string | null;
  min_price: number | null;
  max_price: number | null;
  available_units: number | null;
  is_available: boolean | null;
  created_at: string;
  updated_at: string;
}

interface PropertyAmenities {
  id: string;
  property_id: string;
  amenities_data: {
    building_amenities?: string[];
    apartment_amenities?: string[];
  };
  created_at: string;
  updated_at: string;
}

interface PropertyReviewsSummary {
  id: string;
  property_id: string;
  overall_rating: number | null;
  review_count: number | null;
  sentiment_summary: string | null;
  google_maps_place_id: string | null;
  google_maps_url: string | null;
  created_at: string;
  updated_at: string;
}

interface PropertySpecialOffer {
  id: string;
  property_id: string;
  floor_plan_id: string | null;
  offer_description: string;
  valid_until: string | null;
  descriptive_text: string | null;
  created_at: string;
  updated_at: string;
}

// New types for comparison
interface ComparisonData {
  properties: Property[];
  floorPlans: Map<string, PropertyFloorPlan[]>;
  amenities: Map<string, PropertyAmenities | null>;
  reviewsSummaries: Map<string, PropertyReviewsSummary | null>;
  specialOffers: Map<string, PropertySpecialOffer[]>;
}

interface FloorPlanWithCalculations extends PropertyFloorPlan {
  pricePerSqft: number | null;
  isBestValue: boolean;
}

interface ComparisonMetrics {
  propertyId: string;
  overallRating: number | null;
  reviewCount: number | null;
  startingPrice: number | null;
  oneBrPrice: number | null;
  twoBrPrice: number | null;
  reviewConfidence: number | null; // rating * log(reviewCount)
}
```

---

## API Requirements

### Data Fetching Functions

```typescript
// In frontend/app/properties/compare/hooks/useComparisonData.ts

async function fetchComparisonData(propertyIds: string[]): Promise<ComparisonData> {
  const supabase = createClientComponentClient();

  // Parallel fetch all data
  const [
    { data: properties, error: propsError },
    { data: floorPlans, error: plansError },
    { data: amenities, error: amenitiesError },
    { data: reviewsSummaries, error: reviewsError },
    { data: specialOffers, error: offersError }
  ] = await Promise.all([
    supabase.from('properties').select('*').in('id', propertyIds),
    supabase.from('property_floor_plans').select('*').in('property_id', propertyIds),
    supabase.from('property_amenities').select('*').in('property_id', propertyIds),
    supabase.from('property_reviews_summary').select('*').in('property_id', propertyIds),
    supabase.from('property_special_offers').select('*').in('property_id', propertyIds)
  ]);

  // Handle errors
  if (propsError) throw propsError;

  // Group data by property_id
  const floorPlansMap = new Map<string, PropertyFloorPlan[]>();
  const amenitiesMap = new Map<string, PropertyAmenities | null>();
  const reviewsMap = new Map<string, PropertyReviewsSummary | null>();
  const offersMap = new Map<string, PropertySpecialOffer[]>();

  // ... grouping logic ...

  return {
    properties: properties || [],
    floorPlans: floorPlansMap,
    amenities: amenitiesMap,
    reviewsSummaries: reviewsMap,
    specialOffers: offersMap
  };
}
```

---

## Testing Strategy

### Unit Tests

- [ ] `comparisonHelpers.ts` - Test calculation functions (price/sqft, best value detection)
- [ ] Component prop validation
- [ ] Data transformation logic

### Integration Tests

- [ ] Selection flow (toggle → select → navigate)
- [ ] Comparison page data fetching
- [ ] PDF export generation

### Manual Testing Checklist

- [ ] Select 2 properties → comparison works
- [ ] Select 5 properties → comparison works
- [ ] Try to select 6th property → shows warning
- [ ] Comparison layout looks correct on desktop (1920px)
- [ ] Comparison layout looks correct on tablet (768px)
- [ ] Comparison layout looks correct on mobile (375px)
- [ ] Best value highlighting works correctly
- [ ] Collapsible sections work smoothly
- [ ] PDF export includes all data
- [ ] Back button returns to properties list

---

## Next Steps

### Phase 1 - Start Here

1. Open `frontend/app/properties/page.tsx`
2. Add state: `const [compareMode, setCompareMode] = useState(false)`
3. Add state: `const [selectedIds, setSelectedIds] = useState<string[]>([])`
4. Add compare mode toggle UI
5. Modify property cards to show checkboxes when `compareMode === true`
6. Add floating action button
7. Test selection flow

### Questions to Resolve

- [ ] PDF library preference? (react-pdf vs jsPDF vs html2pdf)
- [ ] Mobile breakpoint strategy? (Card-based or simplified table?)
- [ ] Animation library? (Framer Motion vs Tailwind transitions?)

---

## References

- Existing codebase: `/frontend/app/properties/page.tsx`
- Data models: `/backend/database/models.py`
- Supabase schema: `/supabase/migrations/`
- Design system: Existing Tailwind config in properties pages

---

**Ready to build!** Start with Phase 1 and work incrementally.
