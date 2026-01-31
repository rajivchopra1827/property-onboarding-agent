# Shadcn Component Recommendations

## Overview
This document outlines shadcn/ui components that would enhance the Property Onboarding Agent UI/UX. Based on analysis of the current codebase, here are components that would provide immediate value.

---

## High Priority Components

### 1. **Sonner (Toast Notifications)** ⭐⭐⭐
**Current State:** Using `Alert` components and custom error divs scattered throughout the app
**Why Add:** 
- Better UX for non-blocking notifications
- Auto-dismissing toasts for success/error messages
- Consistent notification system across the app
- Less intrusive than Alert components

**Use Cases:**
- Replace error messages in `AddPropertyForm.tsx`
- Success messages in `SocialPostsSection.tsx` 
- Error notifications in `ImageGallery.tsx`
- General success/error feedback throughout the app

**Files to Update:**
- `frontend/app/components/AddPropertyForm.tsx`
- `frontend/app/components/SocialPostsSection.tsx`
- `frontend/app/components/ImageGallery.tsx`
- `frontend/app/components/StatusMessage.tsx`

---

### 2. **Tooltip** ⭐⭐⭐
**Current State:** No tooltips - users may miss helpful context
**Why Add:**
- Provide additional context without cluttering the UI
- Helpful hints for complex features
- Better accessibility

**Use Cases:**
- Image category tags explanation
- Extraction button tooltips
- Competitor watchlist actions
- Form field help text
- Badge explanations

**Files to Enhance:**
- `frontend/app/properties/[id]/page.tsx` (extraction buttons)
- `frontend/app/components/ImageGallery.tsx` (tag explanations)
- `frontend/app/components/CompetitorsSection.tsx` (action buttons)

---

### 3. **Dropdown Menu** ⭐⭐⭐
**Current State:** Using buttons with onClick handlers for actions
**Why Add:**
- Cleaner action menus
- Better organization of multiple actions
- Consistent with modern UI patterns

**Use Cases:**
- Image actions (hide/show, delete, set primary)
- Competitor actions (add to watchlist, view details)
- Property card actions (edit, delete, compare)
- Review actions (expand, filter)

**Files to Enhance:**
- `frontend/app/components/ImageGallery.tsx` (image actions)
- `frontend/app/components/CompetitorsSection.tsx` (competitor actions)
- `frontend/app/properties/page.tsx` (property card actions)

---

### 4. **Select** ⭐⭐
**Current State:** Using basic inputs and checkboxes
**Why Add:**
- Better form UX for dropdown selections
- Consistent styling
- Accessible by default

**Use Cases:**
- Filter properties by status
- Sort options (date, name, etc.)
- Image category selection
- Review filtering (rating, date range)

**Files to Enhance:**
- `frontend/app/properties/page.tsx` (sorting/filtering)
- `frontend/app/components/ImageGallery.tsx` (category selection)
- `frontend/app/components/ReviewsSection.tsx` (filtering)

---

### 5. **Empty** ⭐⭐
**Current State:** Custom empty state implementations scattered throughout
**Why Add:**
- Standardized empty states
- Consistent messaging and visuals
- Better user experience

**Use Cases:**
- No properties found
- No images collected
- No reviews available
- No competitors found
- No social posts generated

**Files to Enhance:**
- `frontend/app/properties/page.tsx`
- `frontend/app/properties/[id]/page.tsx` (amenities, floor plans, etc.)
- `frontend/app/components/ReviewsSection.tsx`
- `frontend/app/components/CompetitorsSection.tsx`
- `frontend/app/components/SocialPostsSection.tsx`

---

## Medium Priority Components

### 6. **Breadcrumb** ⭐⭐
**Current State:** No navigation breadcrumbs
**Why Add:**
- Better navigation context
- Easier to navigate back
- Professional UI polish

**Use Cases:**
- Property detail page: `Home > Properties > [Property Name]`
- Onboarding progress page navigation

**Files to Enhance:**
- `frontend/app/properties/[id]/page.tsx`
- `frontend/app/properties/onboard/[session_id]/page.tsx`

---

### 7. **Popover** ⭐⭐
**Current State:** Using Dialog for some interactions (may be overkill)
**Why Add:**
- Lightweight alternative to Dialog for quick actions
- Better for contextual menus
- Less intrusive than full dialogs

**Use Cases:**
- Quick image info preview
- Competitor quick actions
- Quick filters/options
- Inline editing

**Files to Enhance:**
- `frontend/app/components/ImageGallery.tsx`
- `frontend/app/components/CompetitorsSection.tsx`

---

### 8. **Separator** ⭐
**Current State:** Using custom borders/divs for visual separation
**Why Add:**
- Semantic separation component
- Consistent styling
- Better accessibility

**Use Cases:**
- Section dividers in property detail page
- Separating content in cards
- Visual organization in forms

**Files to Enhance:**
- `frontend/app/properties/[id]/page.tsx`
- `frontend/app/components/AddPropertyForm.tsx`

---

### 9. **Aspect Ratio** ⭐
**Current State:** Manual aspect ratio handling for images
**Why Add:**
- Consistent image sizing
- Prevents layout shift
- Better responsive behavior

**Use Cases:**
- Property image thumbnails
- Social post mockups
- Floor plan images
- Competitor images

**Files to Enhance:**
- `frontend/app/properties/[id]/page.tsx` (image displays)
- `frontend/app/components/SocialPostsSection.tsx` (mockups)
- `frontend/app/properties/page.tsx` (property cards)

---

### 10. **Form** ⭐
**Current State:** Basic form handling with useState
**Why Add:**
- Better form validation
- Consistent error handling
- Integration with react-hook-form
- Better accessibility

**Use Cases:**
- `AddPropertyForm.tsx` - URL input with validation
- Future forms (property editing, filters, etc.)

**Files to Enhance:**
- `frontend/app/components/AddPropertyForm.tsx`

---

## Lower Priority (Nice to Have)

### 11. **Carousel** 
**Use Case:** Enhanced image gallery with swipe gestures
**Files:** `frontend/app/components/ImageGallery.tsx`

### 12. **Combobox**
**Use Case:** Searchable selects for filtering properties, selecting categories
**Files:** `frontend/app/properties/page.tsx`, `frontend/app/components/ImageGallery.tsx`

### 13. **Accordion**
**Use Case:** Collapsible sections for reviews, competitors (currently using custom expand/collapse)
**Files:** `frontend/app/components/ReviewsSection.tsx`, `frontend/app/components/CompetitorsSection.tsx`

---

## Implementation Priority

### Phase 1 (Immediate Value)
1. **Sonner** - Replace all Alert/error divs with toast notifications
2. **Tooltip** - Add helpful tooltips throughout
3. **Dropdown Menu** - Replace action buttons with dropdown menus

### Phase 2 (UX Improvements)
4. **Select** - Better form inputs
5. **Empty** - Standardize empty states
6. **Breadcrumb** - Navigation improvements

### Phase 3 (Polish)
7. **Popover** - Lightweight interactions
8. **Separator** - Visual organization
9. **Aspect Ratio** - Image consistency
10. **Form** - Better form handling

---

## Installation Commands

To add these components, use the shadcn CLI:

```bash
# High Priority
npx shadcn@latest add sonner
npx shadcn@latest add tooltip
npx shadcn@latest add dropdown-menu
npx shadcn@latest add select
npx shadcn@latest add empty

# Medium Priority
npx shadcn@latest add breadcrumb
npx shadcn@latest add popover
npx shadcn@latest add separator
npx shadcn@latest add aspect-ratio
npx shadcn@latest add form

# Lower Priority
npx shadcn@latest add carousel
npx shadcn@latest add combobox
npx shadcn@latest add accordion
```

---

## Notes

- All components are already configured in `components.json` with the `@shadcn` registry
- Components follow the "new-york" style already configured
- Components will be added to `frontend/app/components/ui/`
- Dependencies will be automatically installed via the CLI
