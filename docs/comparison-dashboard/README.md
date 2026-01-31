# Property Comparison Dashboard - Documentation Hub

**Welcome to the comparison dashboard implementation guide!**

This folder contains everything needed to build the Property Comparison Dashboard feature for FionaFast, designed for seamless collaboration with Cursor AI throughout the entire development process.

---

## 📁 What's in This Folder

### Core Documentation

| File | Purpose | Use When |
|------|---------|----------|
| **README.md** (this file) | Master guide for Cursor collaboration | Starting any phase, context refresh |
| **COMPARISON_DASHBOARD_SPEC.md** | Complete feature specification | Need full context, architecture decisions |
| **PHASE_1_IMPLEMENTATION.md** | Step-by-step Phase 1 guide | Building selection UI |
| **COMPARISON_TYPES_AND_UTILS.md** | TypeScript types and utilities | Implementing any phase, need utility functions |

### Future Phase Guides (To Be Created)

- `PHASE_2_IMPLEMENTATION.md` - Comparison Grid Foundation (create after Phase 1)
- `PHASE_3_IMPLEMENTATION.md` - Rich Comparison Features (create after Phase 2)
- `PHASE_4_IMPLEMENTATION.md` - Export & Polish (create after Phase 3)

---

## 🚀 How to Use This with Cursor

### Initial Setup (One Time)

1. **Point Cursor at this folder:**
   ```
   "Please read all documents in docs/comparison-dashboard/
   to understand the Property Comparison Dashboard feature"
   ```

2. **Cursor will load:**
   - Complete feature spec
   - Current phase implementation guide
   - All types and utilities
   - Design system specifications

---

## 🎯 Phase-by-Phase Collaboration Guide

### Phase 1: Selection UI (Current Phase)

**Duration:** 4-6 hours
**Goal:** Add comparison mode to properties list with multi-select and navigation

**Start by saying to Cursor:**
```
"I'm implementing Phase 1 of the Property Comparison Dashboard.
Please read PHASE_1_IMPLEMENTATION.md and help me:

1. Add compare mode toggle to frontend/app/properties/page.tsx
2. Add checkboxes to property cards
3. Add floating action button
4. Create comparison page skeleton

Follow the 7-step guide in PHASE_1_IMPLEMENTATION.md exactly."
```

**Cursor will:**
- Guide you through each of the 7 steps
- Provide exact code snippets
- Help you test using the checklist
- Ensure design system compliance

**When Phase 1 is Complete:**
- [ ] All 7 steps implemented
- [ ] Testing checklist passed
- [ ] Commit: `git commit -m "feat: add property comparison selection UI (Phase 1)"`
- [ ] **Proceed to Phase 2**

---

### Phase 2: Comparison Grid Foundation

**Duration:** 6-8 hours
**Goal:** Build basic comparison layout with data fetching

**Start by saying to Cursor:**
```
"Phase 1 is complete. Now I'm starting Phase 2: Comparison Grid Foundation.

Please reference:
- COMPARISON_DASHBOARD_SPEC.md (Phase 2 section)
- COMPARISON_TYPES_AND_UTILS.md (useComparisonData hook)

Help me:
1. Implement the useComparisonData hook
2. Create ComparisonHeader component (sticky)
3. Create QuickMetricsTable component
4. Set up responsive grid layout
5. Add loading and error states

Let's start with Step 1: the data fetching hook."
```

**Cursor will:**
- Reference the Phase 2 section in the spec
- Use the pre-built `useComparisonData` hook from COMPARISON_TYPES_AND_UTILS.md
- Help you create the sticky header component
- Build the Quick Metrics table with proper styling
- Set up the responsive grid (Tailwind)

**Key Files for Phase 2:**
```
frontend/app/properties/compare/
├── page.tsx                          # Update with grid layout
├── components/
│   ├── ComparisonHeader.tsx          # NEW
│   └── QuickMetricsTable.tsx         # NEW
└── hooks/
    └── useComparisonData.ts          # NEW (copy from COMPARISON_TYPES_AND_UTILS.md)
```

**When Phase 2 is Complete:**
- [ ] All components created
- [ ] Data fetching works in parallel
- [ ] Sticky headers work on scroll
- [ ] Quick Metrics display correctly
- [ ] Responsive layout works
- [ ] Commit: `git commit -m "feat: add comparison grid foundation (Phase 2)"`
- [ ] **Proceed to Phase 3**

---

### Phase 3: Rich Comparison Features

**Duration:** 8-10 hours
**Goal:** Add detailed comparison sections with highlighting

**Start by saying to Cursor:**
```
"Phase 2 is complete. Now starting Phase 3: Rich Comparison Features.

Reference COMPARISON_DASHBOARD_SPEC.md (Phase 3 section) and help me:

1. Create FloorPlansComparison component with price/sqft calculations
2. Create AmenitiesMatrix component with checkmark grid
3. Create ReviewsComparison component
4. Create SpecialOffersGrid component
5. Add best/worst value highlighting
6. Add collapsible section behavior

Use the utility functions from COMPARISON_TYPES_AND_UTILS.md for:
- calculatePricePerSqft()
- enhanceFloorPlansWithMetrics()
- getCellHighlight()
- createAmenityMatrix()

Let's start with the Floor Plans component."
```

**Cursor will:**
- Build each comparison component
- Integrate the pre-built utility functions
- Implement green highlighting for best values (crown icons)
- Add expand/collapse functionality
- Handle empty states

**Key Files for Phase 3:**
```
frontend/app/properties/compare/
├── components/
│   ├── FloorPlansComparison.tsx      # NEW
│   ├── AmenitiesMatrix.tsx           # NEW
│   ├── ReviewsComparison.tsx         # NEW
│   └── SpecialOffersGrid.tsx         # NEW
└── utils/
    ├── comparisonHelpers.ts          # NEW (copy from COMPARISON_TYPES_AND_UTILS.md)
    └── amenityHelpers.ts             # NEW (copy from COMPARISON_TYPES_AND_UTILS.md)
```

**When Phase 3 is Complete:**
- [ ] All 4 components created
- [ ] Highlighting works (green for best, red for worst)
- [ ] Calculations accurate (price/sqft, etc.)
- [ ] Collapsible sections work smoothly
- [ ] Empty states display correctly
- [ ] Commit: `git commit -m "feat: add rich comparison features (Phase 3)"`
- [ ] **Proceed to Phase 4**

---

### Phase 4: Export & Polish

**Duration:** 6-8 hours
**Goal:** Add PDF export and polish UX

**Start by saying to Cursor:**
```
"Phase 3 is complete. Final phase: Export & Polish.

Reference COMPARISON_DASHBOARD_SPEC.md (Phase 4 section) and help me:

1. Implement PDF export (choose: react-pdf, jsPDF, or html2pdf)
2. Add mobile responsive layout (card-based for <768px)
3. Add smooth animations (expand/collapse, hover)
4. Add keyboard navigation support
5. Polish styling and accessibility

Which PDF library do you recommend and why?"
```

**Cursor will:**
- Help you choose and implement PDF generation
- Create mobile-optimized layout
- Add smooth transitions and animations
- Implement keyboard navigation
- Ensure accessibility (ARIA labels, focus management)

**Key Files for Phase 4:**
```
frontend/app/properties/compare/
├── components/
│   ├── PDFExportButton.tsx           # NEW
│   └── MobileCompareView.tsx         # NEW
└── utils/
    └── pdfTemplate.ts                # NEW
```

**When Phase 4 is Complete:**
- [ ] PDF export works (generates correctly)
- [ ] Mobile layout functional (card-based)
- [ ] Animations smooth (200ms ease-out)
- [ ] Keyboard navigation works
- [ ] Accessibility audit passed
- [ ] Commit: `git commit -m "feat: add PDF export and polish (Phase 4)"`
- [ ] **Feature Complete! 🎉**

---

## 💡 Continuous Collaboration Tips

### Context Refresh
If Cursor loses context mid-phase:
```
"Please re-read docs/comparison-dashboard/README.md and
COMPARISON_DASHBOARD_SPEC.md to refresh context on the
Property Comparison Dashboard feature."
```

### When Stuck
```
"I'm stuck on [specific issue]. Please reference:
- COMPARISON_DASHBOARD_SPEC.md (Component Specifications section)
- COMPARISON_TYPES_AND_UTILS.md (for utility functions)

How should I approach this?"
```

### Design System Questions
```
"What color should I use for [element]? Please reference the
Design System section in COMPARISON_DASHBOARD_SPEC.md."
```

### Type/Utility Questions
```
"What utility function should I use for [calculation]?
Please reference COMPARISON_TYPES_AND_UTILS.md."
```

---

## 📋 Phase Completion Checklist

Use this to track progress:

```
Phase 1: Selection UI
├── [x] Compare mode toggle implemented
├── [x] Property cards show checkboxes
├── [x] Selection state managed correctly
├── [x] Floating action button works
├── [x] Navigation to comparison page works
├── [x] Comparison page skeleton created
└── [x] All Phase 1 tests passed

Phase 2: Comparison Grid Foundation
├── [ ] useComparisonData hook implemented
├── [ ] Data fetches in parallel
├── [ ] ComparisonHeader created (sticky)
├── [ ] QuickMetricsTable displays correctly
├── [ ] Responsive grid layout works
├── [ ] Loading states implemented
└── [ ] Error handling works

Phase 3: Rich Comparison Features
├── [ ] FloorPlansComparison created
├── [ ] Price/sqft calculations accurate
├── [ ] AmenitiesMatrix displays correctly
├── [ ] ReviewsComparison shows sentiment
├── [ ] SpecialOffersGrid works
├── [ ] Best/worst highlighting works
└── [ ] Collapsible sections work

Phase 4: Export & Polish
├── [ ] PDF export generates correctly
├── [ ] Mobile layout functional
├── [ ] Animations smooth
├── [ ] Keyboard navigation works
├── [ ] Accessibility requirements met
└── [ ] Full feature testing passed
```

---

## 🔄 After Each Phase

1. **Test thoroughly** using phase-specific checklist
2. **Commit your work** with descriptive message
3. **Update this README** (check off completed items)
4. **Ask Cursor to transition:**
   ```
   "Phase [N] is complete and committed. Please help me transition
   to Phase [N+1] by reviewing the requirements and creating a
   detailed implementation plan."
   ```

---

## 🆘 Troubleshooting

### Cursor Can't Find Files
```
"Please read the following files:
- docs/comparison-dashboard/COMPARISON_DASHBOARD_SPEC.md
- docs/comparison-dashboard/COMPARISON_TYPES_AND_UTILS.md
- docs/comparison-dashboard/PHASE_1_IMPLEMENTATION.md"
```

### Need to See Full Spec
```
"Show me the [Component/Section] specification from
COMPARISON_DASHBOARD_SPEC.md"
```

### Type Errors
```
"I'm getting a type error. Please reference COMPARISON_TYPES_AND_UTILS.md
and help me fix the type definitions."
```

### Styling Issues
```
"This doesn't match the design system. Please reference the
Design System section in COMPARISON_DASHBOARD_SPEC.md and
help me fix the styling."
```

---

## 📊 Progress Tracking

**Current Phase:** Phase 1
**Status:** Ready to Start
**Last Updated:** 2026-01-30

**Completed Phases:**
- [ ] Phase 1: Selection UI
- [ ] Phase 2: Comparison Grid Foundation
- [ ] Phase 3: Rich Comparison Features
- [ ] Phase 4: Export & Polish

**Estimated Total Time:** 24-32 hours across all phases

---

## 🎯 Success Criteria

The feature is complete when:
- [ ] Users can select 2-5 properties and compare
- [ ] Comparison view shows all key metrics
- [ ] Best/worst values are visually highlighted
- [ ] PDF export works correctly
- [ ] Mobile responsive layout works
- [ ] All accessibility requirements met
- [ ] Full test suite passes

---

## 📝 Notes for Future You

### Key Design Decisions
- **Color coding:** Green = best, Red = worst, Pink = unique
- **Layout:** Column-based for desktop, card-based for mobile
- **Calculations:** Price/sqft is primary value metric
- **Highlighting:** Crown emoji (🏆) for best in category

### Technical Choices
- **Data fetching:** Parallel queries using Promise.all
- **State management:** React useState (no Redux needed)
- **Styling:** Tailwind CSS with custom utility classes
- **PDF library:** TBD in Phase 4

### Lessons Learned
(Update as you build)

---

**Ready to build!** Point Cursor at this folder and start with Phase 1.
