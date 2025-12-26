# Fixing mvccc_master_modern.pptx Placeholder Issues

## Problem
The mvccc_master_modern.pptx template has incorrect placeholder types in some layouts, causing slide generation to fail.

## Issues Found

### 1. Prelude Layout (layout 0)
**Current:** Has BODY placeholder
**Needs:** TITLE or CENTER_TITLE placeholder
**Why:** The code expects to set title text, not body text

**Fix in PowerPoint/Keynote:**
1. Open mvccc_master_modern.pptx
2. View → Edit Master Slides
3. Select "prelude" layout
4. Delete the current BODY text placeholder
5. Insert → Placeholder → Title
6. Position it where you want the message to appear
7. Keep the PICTURE placeholder as is

### 2. Section Layout (layout 6)
**Current:** Has BODY placeholder
**Needs:** TITLE or CENTER_TITLE placeholder
**Why:** Section slides display large centered titles like "宣  召", "頌  讚"

**Fix in PowerPoint/Keynote:**
1. Select "section" layout
2. Delete the current BODY text placeholder
3. Insert → Placeholder → Title (or Center Title if available)
4. Center it on the slide
5. Make it large (72pt font recommended)

### 3. Teaching Layout (layout 5)
**Current:** Has only TITLE placeholder
**Needs:** Both TITLE and BODY placeholders
**Why:** Shows "信息" as title, message + messenger in body

**Fix in PowerPoint/Keynote:**
1. Select "teaching" layout
2. Keep the existing TITLE placeholder
3. Insert → Placeholder → Content (or Body)
4. Position body placeholder below the title
5. Body should display: message title + messenger name

## Verification

After making these changes, save the file and run this verification script:

```bash
uv run python3 -c "
from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

ppt = Presentation('mvccc_master_modern.pptx')

# Check each layout
issues = []

# Prelude should have TITLE and PICTURE
prelude = ppt.slide_layouts[0]
types = [ph.placeholder_format.type for ph in prelude.placeholders]
if PP_PLACEHOLDER.TITLE not in types and PP_PLACEHOLDER.CENTER_TITLE not in types:
    issues.append('Prelude: Missing TITLE placeholder')
if PP_PLACEHOLDER.PICTURE not in types:
    issues.append('Prelude: Missing PICTURE placeholder')

# Section should have TITLE or CENTER_TITLE
section = ppt.slide_layouts[6]
types = [ph.placeholder_format.type for ph in section.placeholders]
if PP_PLACEHOLDER.TITLE not in types and PP_PLACEHOLDER.CENTER_TITLE not in types:
    issues.append('Section: Missing TITLE/CENTER_TITLE placeholder')

# Teaching should have TITLE and BODY
teaching = ppt.slide_layouts[5]
types = [ph.placeholder_format.type for ph in teaching.placeholders]
if PP_PLACEHOLDER.TITLE not in types and PP_PLACEHOLDER.CENTER_TITLE not in types:
    issues.append('Teaching: Missing TITLE placeholder')
if PP_PLACEHOLDER.BODY not in types:
    issues.append('Teaching: Missing BODY placeholder')

if issues:
    print('Issues found:')
    for issue in issues:
        print(f'  ❌ {issue}')
else:
    print('✅ All layouts are correct!')
"
```

## Alternative: Start from mvccc_master.pptx

If fixing the placeholders is difficult, you can:

1. Start with the original mvccc_master.pptx (which has correct placeholders)
2. Apply the modern styling (colors, fonts) to it
3. Save as mvccc_master_modern.pptx

The original mvccc_master.pptx has all the correct placeholder types:
- Layout 0 (prelude): TITLE + PICTURE
- Layout 1 (message): BODY
- Layout 2 (hymn): TITLE + BODY
- Layout 3 (verse): TITLE + BODY
- Layout 4 (memorize): TITLE + BODY
- Layout 5 (teaching): TITLE + BODY
- Layout 6 (section): TITLE
- Layout 7 (Blank): (no placeholders)
