# Cursor Quick Start Guide - Property Comparison Dashboard

**Copy-paste these prompts directly into Cursor to get started immediately.**

---

## 🚀 Initial Setup (First Time Only)

### Step 1: Load All Context

**Paste this into Cursor:**
```
Please read all files in the docs/comparison-dashboard/ folder to understand the Property Comparison Dashboard feature we're building. This includes:

1. COMPARISON_DASHBOARD_SPEC.md - Complete feature specification
2. PHASE_1_IMPLEMENTATION.md - Step-by-step implementation guide
3. COMPARISON_TYPES_AND_UTILS.md - All TypeScript types and utility functions
4. README.md - Master collaboration guide

After reading, confirm you understand the 4-phase implementation plan and are ready to help with Phase 1.
```

---

## 📋 Phase 1: Selection UI

### Step 2: Start Phase 1

**Paste this into Cursor:**
```
I'm ready to implement Phase 1 of the Property Comparison Dashboard.

Please help me modify frontend/app/properties/page.tsx to add:
1. Compare mode toggle
2. Checkboxes on property cards (only when compare mode enabled)
3. Selection state management
4. Floating action button (shows when 2+ properties selected)

Follow the exact 7-step implementation guide in PHASE_1_IMPLEMENTATION.md.

Let's start with Step 1: adding the state management. Show me the exact code to add.
```

### Step 3: Implement Each Component

**After completing state, paste this:**
```
Step 1 complete. Now help me with Step 2: creating the compare mode toggle.
Show me the exact JSX code to add above the properties grid.
```

**Then for each subsequent step:**
```
Step [N] complete. Now help me with Step [N+1]: [component name].
Reference PHASE_1_IMPLEMENTATION.md for the exact code.
```

### Step 4: Create Comparison Page Skeleton

**Paste this:**
```
Now help me create the comparison page skeleton at:
frontend/app/properties/compare/page.tsx

This should:
1. Extract property IDs from query params
2. Fetch properties from Supabase
3. Display property names as placeholders
4. Include Back and Export PDF buttons

Reference the skeleton code in PHASE_1_IMPLEMENTATION.md Step 7.
```

### Step 5: Test Phase 1

**Paste this:**
```
Phase 1 implementation is complete. Please help me test using the
checklist in PHASE_1_IMPLEMENTATION.md:

1. Does the compare mode toggle work?
2. Do checkboxes appear/disappear correctly?
3. Does selection state update properly?
4. Does the floating button appear at 2+ selections?
5. Does navigation to /properties/compare work?

Walk me through testing each item.
```

---

## 📋 Phase 2: Comparison Grid Foundation

### Step 6: Start Phase 2

**Paste this:**
```
Phase 1 is complete and tested. Now starting Phase 2: Comparison Grid Foundation.

Reference:
- COMPARISON_DASHBOARD_SPEC.md (Phase 2 section)
- COMPARISON_TYPES_AND_UTILS.md (useComparisonData hook)

Help me create these files in order:
1. frontend/app/properties/compare/hooks/useComparisonData.ts
2. frontend/app/properties/compare/components/ComparisonHeader.tsx
3. frontend/app/properties/compare/components/QuickMetricsTable.tsx

Let's start with the data fetching hook. Show me the exact code from COMPARISON_TYPES_AND_UTILS.md that I should use.
```

### Step 7: Create Components

**For each component:**
```
[Previous component] is complete. Now help me create [next component].

Reference:
- COMPARISON_DASHBOARD_SPEC.md (Component Specifications section)
- Design system requirements from COMPARISON_DASHBOARD_SPEC.md

Show me the complete component code with:
- Proper TypeScript types
- Tailwind CSS styling matching the design system
- Responsive layout
```

---

## 📋 Phase 3: Rich Comparison Features

### Step 8: Start Phase 3

**Paste this:**
```
Phase 2 is complete. Starting Phase 3: Rich Comparison Features.

Help me create these components with full highlighting logic:
1. FloorPlansComparison - with price/sqft calculations
2. AmenitiesMatrix - with checkmark grid
3. ReviewsComparison - with sentiment display
4. SpecialOffersGrid - with offer details

For calculations, use these functions from COMPARISON_TYPES_AND_UTILS.md:
- calculatePricePerSqft()
- enhanceFloorPlansWithMetrics()
- getCellHighlight()
- createAmenityMatrix()

Let's start with FloorPlansComparison. Show me the implementation.
```

### Step 9: Add Highlighting

**Paste this:**
```
Help me implement the best/worst value highlighting system.

Requirements from COMPARISON_DASHBOARD_SPEC.md:
- Green background for best values
- Red background for worst values (only if 3+ properties)
- Crown icon (🏆) for best in category

Use getCellHighlight() from COMPARISON_TYPES_AND_UTILS.md to determine highlight type.

Show me how to apply this to the Floor Plans pricing.
```

---

## 📋 Phase 4: Export & Polish

### Step 10: PDF Export

**Paste this:**
```
Phase 3 complete. Starting Phase 4: Export & Polish.

First decision: PDF library selection.
Options: react-pdf, jsPDF, html2pdf

Based on:
- Landscape layout requirement
- Need to preserve table structure
- Green/red highlighting must show

Which do you recommend and why? Then help me implement it.
```

### Step 11: Mobile Layout

**Paste this:**
```
PDF export is working. Now help me create mobile responsive layout.

Requirements from COMPARISON_DASHBOARD_SPEC.md:
- Desktop (1280px+): Side-by-side columns
- Tablet (768-1279px): Horizontal scroll
- Mobile (<768px): Card-based layout, compare 2 at a time

Show me the mobile-specific component implementation.
```

---

## 🔄 Maintenance & Updates

### Context Refresh

**If Cursor loses context:**
```
Please re-read all files in docs/comparison-dashboard/ to refresh
your understanding of the Property Comparison Dashboard feature.

Specifically review:
- Current phase requirements
- Design system specifications
- Available utility functions

Confirm when ready to continue.
```

### Fix Type Errors

**If you get TypeScript errors:**
```
I'm getting this type error: [paste error]

Please reference COMPARISON_TYPES_AND_UTILS.md to:
1. Check if the type is defined correctly
2. Help me import it properly
3. Fix the error

Show me the corrected code.
```

### Design System Check

**If styling doesn't look right:**
```
This [component/element] doesn't match the design system.

Please reference the Design System section in COMPARISON_DASHBOARD_SPEC.md and show me:
1. The correct color to use
2. The correct spacing (8px grid)
3. The correct typography scale

Then show me the corrected Tailwind classes.
```

---

## 🎯 Checkpoint Commands

### After Each Phase

**Paste this:**
```
Phase [N] is complete. Please:
1. Review what we built against the acceptance criteria in COMPARISON_DASHBOARD_SPEC.md
2. Identify any gaps or issues
3. Suggest what to test before moving to Phase [N+1]
4. Summarize the files we created/modified

Then help me transition to Phase [N+1].
```

### Before Committing

**Paste this:**
```
Before I commit Phase [N], please:
1. Review all code changes
2. Check for any TODOs or incomplete sections
3. Verify design system compliance
4. Suggest a good commit message

Then show me a checklist of what's included in this commit.
```

---

## 🆘 Emergency Commands

### "I'm Stuck"

```
I'm stuck on [specific problem].

Please:
1. Review the relevant section in COMPARISON_DASHBOARD_SPEC.md
2. Check if there's a utility function in COMPARISON_TYPES_AND_UTILS.md
3. Look at similar implementations in the existing codebase
4. Suggest 2-3 approaches with pros/cons

Help me choose the best approach and implement it.
```

### "This Isn't Working"

```
[Component/Feature] isn't working as expected.

Current behavior: [describe]
Expected behavior: [describe]

Please:
1. Help me debug this step by step
2. Check the implementation against the spec
3. Verify all required data is available
4. Suggest fixes

Show me the corrected code.
```

### "Need to Start Over"

```
I need to restart [component/feature] from scratch.

Please:
1. Show me the exact spec from COMPARISON_DASHBOARD_SPEC.md
2. Provide the complete, correct implementation
3. Explain each section
4. Include all necessary imports and types

Let's rebuild this correctly.
```

---

## 💡 Pro Tips

### 1. Always Reference Docs

When asking Cursor for help, always point it to the specific document:
```
"Reference COMPARISON_DASHBOARD_SPEC.md section [X] and help me..."
```

### 2. Ask for Explanations

Don't just copy code - understand it:
```
"Explain how this code works and why we're using this approach
instead of [alternative]"
```

### 3. Validate Against Spec

After each implementation:
```
"Compare what we just built against the requirements in
COMPARISON_DASHBOARD_SPEC.md. Did we miss anything?"
```

### 4. Use Examples

When unclear:
```
"Show me an example of how to use [utility function] from
COMPARISON_TYPES_AND_UTILS.md with real property data"
```

---

## ✅ Complete Workflow Example

Here's a complete workflow for Phase 1:

```
1. "Please read all files in docs/comparison-dashboard/"
2. "I'm starting Phase 1. Help me with Step 1: state management"
3. [Implement state]
4. "Step 1 complete. Help me with Step 2: compare mode toggle"
5. [Implement toggle]
6. "Step 2 complete. Help me with Step 3: property card checkboxes"
7. [Continue through all 7 steps]
8. "Phase 1 implementation complete. Help me test using the checklist"
9. "Everything works! Review the code and suggest a commit message"
10. "Phase 1 complete. Help me transition to Phase 2"
```

---

**Copy these prompts and paste them directly into Cursor to get started!**
