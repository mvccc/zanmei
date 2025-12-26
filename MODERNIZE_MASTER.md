# Modernizing the Master Slide Template

## Overview
This guide explains how to create a modern master slide template for the church service presentations.

## Design Specifications

### Color Palette
- **Background**: `#F5F7FA` (Light grayish-blue) - RGB(245, 247, 250)
- **Primary (Titles)**: `#2962FF` (Modern blue) - RGB(41, 98, 255)
- **Text**: `#1E293B` (Dark slate) - RGB(30, 41, 59)
- **Secondary**: `#64748B` (Slate gray) - RGB(100, 116, 139)
- **Accent**: `#8B5CF6` (Purple) - RGB(139, 92, 246)

### Typography
- **Primary Font**: PingFang TC (macOS) or Microsoft YaHei (Windows)
- **Fallback**: Heiti TC, STHeiti, or Arial Unicode MS
- **Title Size**: 48-72pt (depending on layout)
- **Body Size**: 32-36pt
- **Line Spacing**: 1.5 for scripture, 1.3 for hymns

### Layout Requirements
The master template needs these 8 layouts (matching mvccc_master.pptx):

1. **Layout 0: prelude** - Opening message
2. **Layout 1: message** - General messages
3. **Layout 2: hymn** - Hymn lyrics with title
4. **Layout 3: verse** - Scripture readings
5. **Layout 4: memorize** - Weekly memory verse
6. **Layout 5: teaching** - Sermon title and speaker
7. **Layout 6: section** - Service section dividers
8. **Layout 7: Blank** - Blank slide

## Steps to Create modern_master.pptx

### Option 1: Using Microsoft PowerPoint (Recommended)

1. **Open the template**
   ```bash
   open mvccc_master.pptx
   ```

2. **Enter Master Slide View**
   - Go to `View` → `Slide Master`
   - You'll see the master slide and all 8 layouts

3. **Update Master Slide (affects all layouts)**
   - Select the top master slide
   - Right-click → `Format Background`
   - Choose `Solid Fill` → enter color `#F5F7FA`
   - Select all text → Change font to `Microsoft YaHei` or `PingFang TC`

4. **Update Each Layout**
   For each of the 8 layouts:

   **Title placeholders:**
   - Font: PingFang TC (or Microsoft YaHei)
   - Size: 48-72pt (larger for section slides, smaller for content)
   - Color: `#2962FF` (blue)
   - Bold: Yes
   - Alignment: Center for sections, left for content slides

   **Body placeholders:**
   - Font: PingFang TC (or Microsoft YaHei)
   - Size: 32-36pt
   - Color: `#1E293B` (dark slate)
   - Line spacing: 1.5
   - Alignment: Center for hymns/verses, left for messages

5. **Save**
   - `File` → `Save As` → name it `modern_master.pptx`
   - Close Master Slide View

### Option 2: Using Keynote (macOS)

1. **Convert to Keynote**
   ```bash
   open mvccc_master.pptx
   # Save as Keynote format
   ```

2. **Edit Master Slides**
   - `View` → `Edit Master Slides`
   - Update colors and fonts as described above

3. **Export to PowerPoint**
   - `File` → `Export To` → `PowerPoint...`
   - Save as `modern_master.pptx`

## Reference File
A sample presentation `modern_design_samples.pptx` has been created with 3 slides showing the modern design applied:
- Slide 1: Section slide (大字標題)
- Slide 2: Hymn slide with title and lyrics
- Slide 3: Scripture slide with citation

Use these samples as visual reference when updating the master template.

## Testing the New Template

After creating `modern_master.pptx`:

1. **Update slides.py** to use the new template:
   ```python
   flags.DEFINE_string("master_pptx", "modern_master.pptx", "The template pptx")
   ```

2. **Generate a test presentation**:
   ```bash
   make pptx SUNDAY=2025-12-28
   ```

3. **Verify** the output looks modern with:
   - Light blue-gray background
   - Blue titles
   - Clean Chinese typography
   - Good contrast and readability

## Why Manual Editing is Needed

PowerPoint and Keynote use proprietary XML structures for master slides that python-pptx cannot modify. The library can:
- ✅ Create slides using master layouts
- ✅ Modify content on slides
- ❌ Modify master slide layouts themselves
- ❌ Change theme colors
- ❌ Update master fonts

Therefore, manual editing in PowerPoint or Keynote is required for master template updates.
