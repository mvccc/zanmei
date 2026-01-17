# SKILLS.md

This document describes the key skills/functionalities provided by this repository.

## Slide Generation

Generate complete Sunday service PowerPoint presentations from a configuration file.

**Usage:**
```bash
# Generate slides for next Sunday
make slides

# Generate for specific date
make slides SUNDAY=2024-03-24
```

**Requirements:**
- Service configuration file at `services/{YYYY-MM-DD}.flags`
- Hymn files in `processed/mvccc/` directory (Markdown `.md` format preferred, PPTX also supported)
- Master template (`mvccc_master_modern_dark.pptx` or specified via `--master_pptx`)

**Output:** `{YYYY-MM-DD}.pptx` with complete service flow including:
- Opening messages and call to worship
- Hymns (congregation, choir, response, offering)
- Scripture reading slides
- Memory verse of the week
- Sermon title slide
- Section dividers (prayer, offering, welcome, announcements, benediction)

---

## Scripture Lookup

Retrieve Bible verses by Chinese citation with support for verse ranges and multiple passages.

**Usage:**
```bash
# Single verse
make scripture VERSES="約翰福音3:16"

# Verse range
make scripture VERSES="羅馬書12:1-2"

# Multiple passages (semicolon-separated)
make scripture VERSES="約翰福音3:16;14:6"

# Compare translations
make scripture_compare VERSES="約翰福音3:16"
```

**Supported citation formats:**
- Single verse: `約翰福音3:16`
- Verse range: `馬太福音25:14-30`
- Cross-chapter range: `詩篇23:1-24:10`
- Multiple in same book: `羅馬書12:1-2,9-13`
- Multiple books: `約翰福音3:16;羅馬書8:28`

**Bible sources:**
- `bible.cloud` (default) - CMNUNV.epub
- `ibibles.net` - Alternative source

---

## Hymn Resource Download

Download hymn lyrics and sheet music from Chinese Christian hymnal websites.

**Usage:**
```bash
# Download from all sources
make download

# Download from specific sources
make zanmei      # izanmei.cc - Primary source for "Hymns for God's People"
make hoc5        # hoc5.net
make mvccc       # mvccc.org church resources
```

**Output locations:**
- `download/zanmei/` - PNG images of hymn sheets
- `download/hoc5/` - Hymn resources
- `download/mvccc/` - Church-specific resources

**Note:** Downloaded resources are converted to Markdown format (`.md`) and placed in `processed/mvccc/` for use in slide generation. Markdown is the preferred format as it allows easier editing and version control.

---

## Text Extraction

Extract text content from existing PowerPoint files for review or reuse.

**Usage:**
```bash
make pptx_to_text PPTX=processed/mvccc/聖哉聖哉聖哉.pptx
```

**Output:** Prints slide-by-slide text content showing:
- Slide number
- Text from each shape/placeholder
- Paragraph structure

---

## Hymn Search

Search for hymn files by keyword with fuzzy matching for Chinese character variants. Searches Markdown files (`.md`) in `processed/mvccc/` directory.

**Programmatic usage:**
```python
from mvccc.slides import search_hymn_md

# Returns list of Hymn objects with lyrics
hymns = search_hymn_md("主曾離寳座")
```

**Fuzzy matching handles:**
- 你/祢/袮 (you - honorific variants)
- 寶/寳 (treasure)
- 他/祂 (he - divine form)
- 于/於 (at/in)
- 牆/墻 (wall)

---

## Service Configuration

Create service configuration files for slide generation.

**File location:** `services/{YYYY-MM-DD}.flags`

**Available flags:**
```
--choir=hymn_name           # Choir hymn (format: number_name or just name)
--hymns=hymn_name           # Congregation hymn (repeatable)
--response=hymn_name        # Response hymn after sermon
--offering=hymn_name        # Offering hymn
--scripture=citation        # Main scripture reading
--memorize=citation         # Memory verse of the week
--message=title             # Sermon title
--messager=speaker          # Speaker name
--communion                 # Include communion section (optional)
--master_pptx=template.pptx # Custom template (optional)
```

**Hymn specification formats:**
- Number + name: `114_主曾離寳座`
- Name only: `坐在寶座上聖潔羔羊`
- Number only: `114`

**Hymn title display:**
- Hymns with numbers display as: `教會聖詩 #114` (40pt) followed by `《主曾離寳座》` (80pt bold)
- Hymns without numbers display title only in 80pt bold

---

## Web Interface

Interactive web UI for slide generation using Streamlit.

**Usage:**
```bash
make streamlit-slides
# Opens at http://localhost:8501/slides
```

**Features:**
- Visual hymn selection
- Scripture preview
- Real-time slide preview
- Direct PPTX download

---

## Hymn Statistics

Analyze downloaded hymn resources and usage patterns.

**Usage:**
```bash
make stats
```

**Output:** Statistics on:
- Downloaded hymns by source
- Missing hymns
- Duplicate entries
