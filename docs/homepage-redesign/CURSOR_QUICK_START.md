# Cursor Quick Start Guide - Homepage Redesign

**Copy-paste these prompts directly into Cursor to get started immediately.**

---

## 🚀 Initial Setup (First Time Only)

### Step 1: Load All Context

**Paste this into Cursor:**
```
Please read all files in the docs/homepage-redesign/ folder to understand the Homepage Redesign feature we're building. This includes:

1. HOMEPAGE_REDESIGN_SPEC.md - Complete feature specification
2. PHASE_1_IMPLEMENTATION.md - Step-by-step implementation guide
3. TYPES_AND_UTILS.md - All TypeScript types and utility functions
4. README.md - Master collaboration guide

After reading, confirm you understand the 6-phase implementation plan and are ready to help with Phase 1.
```

---

## 📋 Phase 1: Table View Toggle

### Step 2: Start Phase 1

**Paste this into Cursor:**
```
I'm ready to implement Phase 1 of the Homepage Redesign: Table View Toggle.

Please help me modify frontend/app/properties/page.tsx to add:
1. View mode state ('card' | 'table')
2. View toggle button (Card/Table icons)
3. PropertyTable component
4. Column sorting logic
5. Conditional rendering based on view mode

Follow the exact 6-step implementation guide in PHASE_1_IMPLEMENTATION.md.

Let's start with Step 1: adding the view mode state. Show me the exact code to add.
```

### Step 3: Implement Each Component

**After completing state, paste this:**
```
Step 1 complete. Now help me with Step 2: creating the view toggle button.
Show me the exact JSX code to add to the properties page.
```

**Then for each subsequent step:**
```
Step [N] complete. Now help me with Step [N+1]: [component name].
Reference PHASE_1_IMPLEMENTATION.md for the exact code.
```

### Step 4: Create PropertyTable Component

**Paste this:**
```
Now help me create the PropertyTable component at:
frontend/app/components/PropertyTable.tsx

This should:
1. Display properties in a table format
2. Have sortable columns (Property, Location)
3. Show website links
4. Include "View Details" actions
5. Match the design system from HOMEPAGE_REDESIGN_SPEC.md

Reference the complete component code in PHASE_1_IMPLEMENTATION.md Step 3.
```

### Step 5: Test Phase 1

**Paste this:**
```
Phase 1 implementation is complete. Please help me test using the
checklist in PHASE_1_IMPLEMENTATION.md:

1. Does the view toggle work?
2. Does the table display correctly?
3. Does column sorting work?
4. Does conditional rendering work?
5. Is the design system followed?

Walk me through testing each item.
```

---

## 📋 Phase 2: Intelligence Layer in Table

### Step 6: Start Phase 2

**Paste this:**
```
Phase 1 is complete and tested. Now starting Phase 2: Intelligence Layer in Table.

Reference:
- HOMEPAGE_REDESIGN_SPEC.md (Phase 2 section)
- TYPES_AND_UTILS.md (propertyHealth.ts)

Help me:
1. Create propertyHealth.ts utility file
2. Add expandable row functionality to PropertyTable
3. Calculate health status for each property
4. Show status badges in Status column
5. Display insights in expanded rows
6. Add quick action buttons

Let's start by creating the propertyHealth.ts file. Show me where to put it and the complete code from TYPES_AND_UTILS.md.
```

### Step 7: Enhance Properties

**Paste this:**
```
propertyHealth.ts is created. Now help me enhance properties with health data in frontend/app/properties/page.tsx.

I need to:
1. Fetch related data counts (floor plans, reviews, etc.)
2. Use enhancePropertyWithHealth() to add health fields
3. Pass enhanced properties to both Card and Table views

Show me how to modify the data fetching logic. Reference the example in TYPES_AND_UTILS.md.
```

---

## 📋 Phase 3: Smart Categorization

### Step 8: Start Phase 3

**Paste this:**
```
Phase 2 is complete. Starting Phase 3: Smart Categorization.

Help me implement automatic property grouping:
1. Create propertyCategorization.ts utility
2. Create PropertySection component
3. Create SectionHeader component
4. Categorize properties into: Needs Attention, Partial, Up to Date, Recently Added
5. Make sections collapsible
6. Apply to both card and table views

Reference HOMEPAGE_REDESIGN_SPEC.md Phase 3 section and use categorizeProperties() from TYPES_AND_UTILS.md.

Let's start with the categorization utility. Show me the complete code.
```

---

## 📋 Phase 4: Multi-Select & Bulk Actions

### Step 9: Start Phase 4

**Paste this:**
```
Phase 3 is complete. Starting Phase 4: Multi-Select & Bulk Actions.

Help me add bulk operations to table view:
1. Add checkbox column to PropertyTable
2. Track selected property IDs in state
3. Create BulkActionBar component
4. Implement "Compare Selected" (navigate to /properties/compare)
5. Implement "Refresh All Selected"
6. Show bulk action bar when items selected

Reference HOMEPAGE_REDESIGN_SPEC.md Phase 4 section.

Let's start by adding checkboxes to the table. Show me the modifications needed.
```

---

## 📋 Phase 5: Enhanced Filtering & Search

### Step 10: Start Phase 5

**Paste this:**
```
Phase 4 is complete. Starting Phase 5: Enhanced Filtering & Search.

Help me create the complete filter bar:
1. Search input (filter by property name)
2. City multi-select dropdown
3. Rating range slider
4. Data health radio buttons (All/Complete/Partial/Stale)
5. Has Units checkbox
6. Has Offers checkbox
7. URL params synchronization

Reference HOMEPAGE_REDESIGN_SPEC.md Phase 5 section and use filterProperties() from TYPES_AND_UTILS.md.

Let's start with creating the FilterBar component. Show me the structure.
```

---

## 📋 Phase 6: Polish & UX Enhancements

### Step 11: Start Phase 6

**Paste this:**
```
Phase 5 is complete. Final phase: Polish & UX Enhancements.

Help me add:
1. Smooth view toggle animation (CSS transition)
2. Save view preference to localStorage
3. Empty states for filtered results
4. Loading skeleton states
5. Keyboard shortcuts (arrow keys in table)
6. Performance optimization if needed

Reference HOMEPAGE_REDESIGN_SPEC.md Phase 6 section.

Let's start with the view toggle animation. Show me the CSS/Tailwind classes to add.
```

---

## 🔄 Maintenance & Updates

### Context Refresh

**If Cursor loses context:**
```
Please re-read all files in docs/homepage-redesign/ to refresh
your understanding of the Homepage Redesign feature.

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

Please reference TYPES_AND_UTILS.md to:
1. Check if the type is defined correctly
2. Help me import it properly
3. Fix the error

Show me the corrected code.
```

### Design System Check

**If styling doesn't look right:**
```
This [component/element] doesn't match the design system.

Please reference the Design System section in HOMEPAGE_REDESIGN_SPEC.md and show me:
1. The correct colors to use
2. The correct spacing (Tailwind classes)
3. The correct typography

Then show me the corrected code.
```

---

## 🎯 Checkpoint Commands

### After Each Phase

**Paste this:**
```
Phase [N] is complete. Please:
1. Review what we built against the acceptance criteria in HOMEPAGE_REDESIGN_SPEC.md
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
1. Review the relevant section in HOMEPAGE_REDESIGN_SPEC.md
2. Check if there's a utility function in TYPES_AND_UTILS.md
3. Look at the phase implementation guide
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
1. Show me the exact spec from HOMEPAGE_REDESIGN_SPEC.md
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
"Reference HOMEPAGE_REDESIGN_SPEC.md section [X] and help me..."
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
HOMEPAGE_REDESIGN_SPEC.md. Did we miss anything?"
```

### 4. Use Examples

When unclear:
```
"Show me an example of how to use [utility function] from
TYPES_AND_UTILS.md with real property data"
```

---

## ✅ Complete Workflow Example

Here's a complete workflow for Phase 1:

```
1. "Please read all files in docs/homepage-redesign/"
2. "I'm starting Phase 1. Help me with Step 1: view mode state"
3. [Implement state]
4. "Step 1 complete. Help me with Step 2: view toggle button"
5. [Implement toggle]
6. "Step 2 complete. Help me with Step 3: PropertyTable component"
7. [Continue through all 6 steps]
8. "Phase 1 implementation complete. Help me test using the checklist"
9. "Everything works! Review the code and suggest a commit message"
10. "Phase 1 complete. Help me transition to Phase 2"
```

---

**Copy these prompts and paste them directly into Cursor to get started!**
