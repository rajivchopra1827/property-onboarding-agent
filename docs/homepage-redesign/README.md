# Homepage Redesign - Documentation Hub

**Welcome to the homepage redesign implementation guide!**

This folder contains everything needed to build the dual-view homepage with intelligence layer for FionaFast.

---

## 📁 What's in This Folder

### Core Documentation

| File | Purpose | Use When |
|------|---------|----------|
| **README.md** (this file) | Master guide for all phases | Starting any phase, context refresh |
| **HOMEPAGE_REDESIGN_SPEC.md** | Complete feature specification | Need full context, design decisions |
| **PHASE_1_IMPLEMENTATION.md** | Step-by-step Phase 1 guide | Building table view toggle |
| **TYPES_AND_UTILS.md** | TypeScript types and utilities | Implementing any phase |
| **CURSOR_QUICK_START.md** | Copy-paste prompts for Cursor | Quick reference for prompts |

---

## 🚀 How to Use This with Cursor

### Initial Setup (One Time)

1. **Point Cursor at this folder:**
   ```
   "Please read all documents in docs/homepage-redesign/
   to understand the Homepage Redesign feature we're building"
   ```

2. **Cursor will load:**
   - Complete feature spec
   - Current phase implementation guide
   - All types and utilities
   - Design system specifications

---

## 🎯 Phase-by-Phase Collaboration Guide

### Phase 1: Table View Toggle (Current Phase)

**Duration:** 4-6 hours
**Goal:** Add basic dual-view with card/table toggle

**Start by saying to Cursor:**
```
"I'm implementing Phase 1 of the Homepage Redesign.
Please read PHASE_1_IMPLEMENTATION.md and help me:

1. Add view mode state to properties page
2. Create view toggle button
3. Create PropertyTable component
4. Add column sorting
5. Conditional render based on view mode

Follow the 6-step guide in PHASE_1_IMPLEMENTATION.md exactly."
```

**Cursor will:**
- Guide you through each of the 6 steps
- Provide exact code snippets
- Help you test using the checklist
- Ensure design system compliance

**When Phase 1 is Complete:**
- [ ] All 6 steps implemented
- [ ] Testing checklist passed
- [ ] Commit: `git commit -m "feat: add table view toggle (Phase 1)"`
- [ ] **Proceed to Phase 2**

---

### Phase 2: Intelligence Layer in Table

**Duration:** 6-8 hours
**Goal:** Add smart insights and status to table

**Start by saying to Cursor:**
```
"Phase 1 is complete. Now I'm starting Phase 2: Intelligence Layer in Table.

Please reference:
- HOMEPAGE_REDESIGN_SPEC.md (Phase 2 section)
- TYPES_AND_UTILS.md (propertyHealth.ts utilities)

Help me:
1. Add expandable row functionality
2. Calculate property health status
3. Show status badges in table
4. Display insights in expanded rows
5. Add quick action buttons

Let's start with Step 1: expandable rows."
```

**Cursor will:**
- Reference Phase 2 section in spec
- Use pre-built health calculation utilities
- Help create expandable row logic
- Integrate status badges
- Wire up quick actions

**Key Files for Phase 2:**
```
frontend/app/
├── properties/page.tsx            # Update with health calculations
├── components/
│   └── PropertyTable.tsx          # Add expandable rows
└── utils/
    └── propertyHealth.ts          # NEW (copy from TYPES_AND_UTILS.md)
```

**When Phase 2 is Complete:**
- [ ] Expandable rows work
- [ ] Status badges appear
- [ ] Insights display correctly
- [ ] Quick actions functional
- [ ] Commit: `git commit -m "feat: add intelligence layer to table (Phase 2)"`
- [ ] **Proceed to Phase 3**

---

### Phase 3: Smart Categorization

**Duration:** 4-6 hours
**Goal:** Auto-group properties by health status

**Start by saying to Cursor:**
```
"Phase 2 is complete. Starting Phase 3: Smart Categorization.

Reference HOMEPAGE_REDESIGN_SPEC.md (Phase 3 section) and help me:

1. Implement property categorization logic
2. Create collapsible section headers
3. Render sections: Needs Attention, Partial, Up to Date, Recent
4. Set default expand/collapse states
5. Make it work in both card and table views

Use categorizeProperties() from TYPES_AND_UTILS.md.

Let's start with the categorization logic."
```

**Cursor will:**
- Implement categorization function
- Create section header components
- Add collapse/expand state
- Apply to both view modes

**Key Files for Phase 3:**
```
frontend/app/
├── properties/page.tsx               # Use categorization
├── components/
│   ├── PropertySection.tsx           # NEW
│   └── SectionHeader.tsx             # NEW
└── utils/
    └── propertyCategorization.ts     # NEW (from TYPES_AND_UTILS.md)
```

**When Phase 3 is Complete:**
- [ ] Properties auto-categorize
- [ ] Sections collapsible
- [ ] Default states correct
- [ ] Works in both views
- [ ] Commit: `git commit -m "feat: add smart categorization (Phase 3)"`
- [ ] **Proceed to Phase 4**

---

### Phase 4: Multi-Select & Bulk Actions

**Duration:** 4-6 hours
**Goal:** Enable bulk operations in table view

**Start by saying to Cursor:**
```
"Phase 3 is complete. Starting Phase 4: Multi-Select & Bulk Actions.

This phase adds:
1. Checkboxes in table rows
2. Selection state management
3. Bulk action bar
4. Compare Selected action
5. Refresh All Selected action

Reference HOMEPAGE_REDESIGN_SPEC.md Phase 4 section.

Let's start with adding checkboxes to the table."
```

**Cursor will:**
- Add checkbox column to table
- Track selected IDs in state
- Create bulk action bar component
- Wire up compare action (navigate to comparison page)
- Implement refresh all action

**Key Files for Phase 4:**
```
frontend/app/
├── properties/page.tsx               # Selection state
├── components/
│   ├── PropertyTable.tsx             # Add checkboxes
│   └── BulkActionBar.tsx             # NEW
```

**When Phase 4 is Complete:**
- [ ] Checkboxes work
- [ ] Bulk action bar appears
- [ ] Compare Selected works
- [ ] Refresh All works
- [ ] Commit: `git commit -m "feat: add bulk actions (Phase 4)"`
- [ ] **Proceed to Phase 5**

---

### Phase 5: Enhanced Filtering & Search

**Duration:** 6-8 hours
**Goal:** Rich filtering across both views

**Start by saying to Cursor:**
```
"Phase 4 is complete. Starting Phase 5: Enhanced Filtering & Search.

Help me create the filter bar with:
1. Search input (filter by property name)
2. City multi-select dropdown
3. Rating range slider
4. Data health radio buttons
5. Availability checkbox
6. Special offers checkbox
7. URL params for filter state

Reference HOMEPAGE_REDESIGN_SPEC.md Phase 5 section and
use filterProperties() from TYPES_AND_UTILS.md.

Let's start with the search input."
```

**Cursor will:**
- Create FilterBar component
- Implement each filter control
- Wire up filter state
- Add URL param synchronization
- Apply filters to both views

**Key Files for Phase 5:**
```
frontend/app/
├── properties/page.tsx               # Filter state
├── components/
│   ├── FilterBar.tsx                 # NEW
│   ├── CityFilter.tsx                # NEW
│   └── RatingSlider.tsx              # NEW
```

**When Phase 5 is Complete:**
- [ ] All filters work
- [ ] Filters combine correctly
- [ ] URL params update
- [ ] Filters restore from URL
- [ ] Commit: `git commit -m "feat: add enhanced filtering (Phase 5)"`
- [ ] **Proceed to Phase 6**

---

### Phase 6: Polish & UX Enhancements

**Duration:** 4-6 hours
**Goal:** Smooth experience with preferences

**Start by saying to Cursor:**
```
"Phase 5 is complete. Final phase: Polish & UX Enhancements.

Help me add:
1. Smooth view toggle animation
2. Save view preference to localStorage
3. Empty states
4. Loading skeleton states
5. Keyboard shortcuts
6. Performance optimization

Reference HOMEPAGE_REDESIGN_SPEC.md Phase 6 section.

Let's start with the view toggle animation."
```

**Cursor will:**
- Add CSS transitions
- Implement localStorage persistence
- Create empty state components
- Add loading skeletons
- Wire up keyboard shortcuts
- Optimize performance if needed

**When Phase 6 is Complete:**
- [ ] Animations smooth
- [ ] Preferences save
- [ ] Empty states work
- [ ] Loading states work
- [ ] Keyboard shortcuts functional
- [ ] Commit: `git commit -m "feat: add polish and UX enhancements (Phase 6)"`
- [ ] **Feature Complete! 🎉**

---

## 💡 Continuous Collaboration Tips

### Context Refresh
If Cursor loses context mid-phase:
```
"Please re-read docs/homepage-redesign/README.md and
HOMEPAGE_REDESIGN_SPEC.md to refresh context on the
Homepage Redesign feature."
```

### When Stuck
```
"I'm stuck on [specific problem].

Please:
1. Review the relevant section in HOMEPAGE_REDESIGN_SPEC.md
2. Check if there's a utility function in TYPES_AND_UTILS.md
3. Look at the phase implementation guide
4. Suggest approaches with pros/cons

Help me resolve this."
```

### Design System Questions
```
"What styling should I use for [element]? Please reference the
Design System section in HOMEPAGE_REDESIGN_SPEC.md."
```

### Type/Utility Questions
```
"What utility function should I use for [calculation]?
Please reference TYPES_AND_UTILS.md."
```

---

## 📋 Phase Completion Checklist

Use this to track progress:

```
Phase 1: Table View Toggle
├── [ ] View mode state added
├── [ ] View toggle button created
├── [ ] PropertyTable component built
├── [ ] Column sorting works
├── [ ] Conditional rendering works
└── [ ] All Phase 1 tests passed

Phase 2: Intelligence Layer in Table
├── [ ] Expandable rows functional
├── [ ] Property health calculated
├── [ ] Status badges display
├── [ ] Insights show in expanded rows
├── [ ] Quick actions work
└── [ ] All Phase 2 tests passed

Phase 3: Smart Categorization
├── [ ] Categorization logic implemented
├── [ ] Section headers created
├── [ ] Sections collapsible
├── [ ] Default states correct
├── [ ] Works in both views
└── [ ] All Phase 3 tests passed

Phase 4: Multi-Select & Bulk Actions
├── [ ] Checkboxes in table
├── [ ] Selection state managed
├── [ ] Bulk action bar appears
├── [ ] Compare Selected works
├── [ ] Refresh All works
└── [ ] All Phase 4 tests passed

Phase 5: Enhanced Filtering
├── [ ] Search input works
├── [ ] City filter works
├── [ ] Rating slider works
├── [ ] Data health filter works
├── [ ] All filters combine correctly
├── [ ] URL params sync
└── [ ] All Phase 5 tests passed

Phase 6: Polish & UX
├── [ ] View toggle animation smooth
├── [ ] Preferences save to localStorage
├── [ ] Empty states display
├── [ ] Loading states work
├── [ ] Keyboard shortcuts functional
└── [ ] All Phase 6 tests passed
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
- docs/homepage-redesign/HOMEPAGE_REDESIGN_SPEC.md
- docs/homepage-redesign/TYPES_AND_UTILS.md
- docs/homepage-redesign/PHASE_1_IMPLEMENTATION.md"
```

### Need to See Full Spec
```
"Show me the [Component/Section] specification from
HOMEPAGE_REDESIGN_SPEC.md"
```

### Type Errors
```
"I'm getting a type error. Please reference TYPES_AND_UTILS.md
and help me fix the type definitions."
```

### Styling Issues
```
"This doesn't match the design system. Please reference the
Design System section in HOMEPAGE_REDESIGN_SPEC.md and
help me fix the styling."
```

---

## 📊 Progress Tracking

**Current Phase:** Phase 1
**Status:** Ready to Start
**Last Updated:** 2026-01-30

**Completed Phases:**
- [ ] Phase 1: Table View Toggle
- [ ] Phase 2: Intelligence Layer in Table
- [ ] Phase 3: Smart Categorization
- [ ] Phase 4: Multi-Select & Bulk Actions
- [ ] Phase 5: Enhanced Filtering & Search
- [ ] Phase 6: Polish & UX Enhancements

**Estimated Total Time:** 28-42 hours across all phases

---

## 🎯 Success Criteria

The feature is complete when:
- [ ] Users can toggle between card and table views seamlessly
- [ ] Properties auto-categorize by health status
- [ ] Status badges and insights appear in both views
- [ ] Table view enables multi-select and bulk actions
- [ ] Comprehensive filtering works across both views
- [ ] User preferences persist (view mode, filters)
- [ ] All tests pass
- [ ] Performance is acceptable (100+ properties)

---

## 📝 Notes for Future You

### Key Design Decisions
- **Dual views:** Card for browsing, Table for analysis
- **Intelligence layer:** Auto-categorization by health status
- **Unified controls:** Same filters/sorting work for both views
- **Progressive enhancement:** Each phase adds value independently

### Technical Choices
- **State management:** React useState (no Redux needed)
- **Data enhancement:** Calculate health client-side
- **Persistence:** localStorage for preferences, URL params for filters
- **Styling:** Tailwind CSS with custom status colors

### Lessons Learned
(Update as you build)

---

**Ready to build!** Point Cursor at this folder and start with Phase 1.
