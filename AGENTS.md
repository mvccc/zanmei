# AGENTS.md

## Project Overview

**zanmei** is a Python toolkit for creating church service PowerPoint presentations for Mountain View Chinese Christian Church (MVCCC). The project includes:

- **Hymn management**: Downloads hymn lyrics and resources from multiple Chinese Christian hymnal websites
- **Bible scripture lookup**: Parses and fetches scripture passages by citation (e.g., "約翰福音3:16")
- **Slide generation**: Creates professionally formatted service presentations from templates

**Tech Stack:**
- Python 3.12+
- `uv` for dependency management (modern, fast Python package manager)
- `python-pptx` for PowerPoint manipulation
- `absl-py` for CLI flags

---

## Development Environment Setup

### Initial Setup

```bash
make init
```

This command will:
1. Install `uv` (if not already installed)
2. Sync all dependencies from `uv.lock`
3. Download external resources (hymns, Bible texts)

### Platform-Specific Requirements

**macOS:** Requires GNU coreutils for date operations
```bash
brew install coreutils
```

**Virtual Environment:** Automatically managed by `uv`. The Makefile detects if you're in a virtual environment and uses `uv run` accordingly.

---

## Project Structure

```
zanmei/
├── bible/           # Scripture parsing and lookup modules
│   ├── index.py     # Citation parsing (e.g., "John 3:16-18")
│   └── scripture.py # Bible verse fetching from multiple sources
├── hymns/           # Hymn downloading modules
│   ├── zanmei.py    # zanmei.cc scraper
│   ├── hoc5.py      # hoc5.net scraper
│   ├── mvccc.py     # mvccc.org scraper
│   └── stats.py     # Hymn usage statistics
├── mvccc/           # PowerPoint slide generation
│   ├── slides.py    # Core slide generation logic
│   └── slidesapp.py # Streamlit web UI for slide generation
├── services/        # Service configuration files (.flags format)
│   └── YYYY-MM-DD.flags  # Flag files defining service content
├── tests/           # pytest test suite
│   └── bible/       # Bible module tests
└── pyproject.toml   # All project configuration and dependencies
```

---

## Common Development Tasks

### Creating Service Slides

Generate a PowerPoint presentation for a service:

```bash
# For next Sunday (automatic)
make pptx

# For specific date
make pptx SUNDAY=2025-01-12

# Output: YYYY-MM-DD.pptx
```

**Flag File Format** (`services/YYYY-MM-DD.flags`):
```
--choir=236_大哉聖哉耶穌尊名2
--hymns=坐在寶座上聖潔羔羊
--hymns=114_主曾離寳座
--response=298_為主而活
--offering=488-1_獻上感恩的心
--scripture=馬太福音25:14-30
--memorize=馬太福音25:23
--message=今日教會所需要的人才
--messager=姜武城牧師
```

### Looking Up Scripture

```bash
# Single verse
make scripture VERSES="約翰福音3:16"

# Verse range
make scripture VERSES="羅馬書12:1-2"

# Compare translations
make scripture_compare VERSES="約翰福音3:16"
```

### Downloading Hymn Resources

usually it's already done. don't need to download again.

```bash
# Download from all sources
make download

# Download from specific source
make zanmei
make hoc5
make mvccc
```

### Extracting Text from PowerPoint

```bash
make pptx_to_text PPTX=path/to/file.pptx
```

---

## Code Style & Quality

### Formatter & Linter: Ruff

The project uses **Ruff** (an extremely fast Python linter and formatter) for all code quality checks. Ruff replaces Black, isort, and flake8.

**Configuration:** See `[tool.ruff]` in `pyproject.toml`

- Line length: 128 characters
- Target: Python 3.12+
- Black-compatible formatting
- Enabled linting rules: E, W, F, I, N, UP, B, C4, SIM, A, T20, ERA

### Commands

```bash
# Format code (auto-fix)
make format

# Check for linting issues
make lint

# Auto-fix linting issues where possible
make fix

# Run both linting and tests
make check
```

**Before Committing:** Always run `make format` and `make check` to ensure code quality.

---

## Testing Instructions

### Framework: pytest

```bash
# Run all tests (with linting)
make test

# Run specific test file
make tests/bible/test_scripture.py
make tests/bible/test_index.py

# Run pytest directly with options
uv run pytest --capture=no --verbose -k test_name
```

### Test Coverage Expectations

- All new features should include tests
- Bible citation parsing must handle edge cases (ranges, multiple books, etc.)
- Hymn scrapers should validate downloaded content structure

---

## Working with Service Flag Files

### Flag File Location

`services/YYYY-MM-DD.flags`

### Required Flags

- `--scripture`: Main scripture reading (e.g., "馬太福音25:14-30")
- `--message`: Sermon title
- `--messager`: Speaker name

### Optional Flags

- `--choir`: Opening choir hymn (format: `number_name`)
- `--hymns`: Congregation hymns (can be specified multiple times)
- `--response`: Response hymn after sermon
- `--offering`: Offering hymn
- `--memorize`: Memory verse of the week
- `--communion`: Whether to include communion (true/false)

### Hymn Specification Format

Hymns can be specified as:

1. **Number only**: `114` → Looks up hymn #114
2. **Number + Name**: `114_主曾離寳座` → Uses this exact name
3. **Name only**: `坐在寶座上聖潔羔羊` → Searches by name

---

## Important Constraints & Limitations

### PowerPoint Master Templates

**python-pptx limitations:** The python-pptx library cannot modify master slide templates (layout definitions, theme colors, fonts). It can only:

- ✅ Create slides using existing master layouts
- ✅ Modify content on individual slides
- ❌ Modify master slide layouts
- ❌ Change theme colors or master fonts

**Workaround — Direct XML Editing:** PPTX files are ZIP archives containing XML files. To modify master templates programmatically:

1. **Unzip** the `.pptx` file to a temporary directory
2. **Edit** the XML files directly (e.g., `ppt/slideMasters/slideMaster1.xml`, `ppt/slideLayouts/*.xml`, `ppt/theme/theme1.xml`)
3. **Rezip** the contents back into a `.pptx` file

This approach allows full control over master slides, themes, colors, and fonts without manual PowerPoint editing.

**Reference Files:**

- `mvccc_master.pptx` - Current template
- `mvccc_master_modern.pptx` - Modern design template (in progress)

### External Dependencies

The project relies on external websites for hymn data:

- **zanmei.cc** (`https://www.izanmei.cc`) - Primary hymn source
- **hoc5.net** - Hymn audio/resources
- **mvccc.org** - Church-specific resources

**Note:** If these websites change structure, the scrapers (`hymns/*.py`) may need updates.

### Chinese Character Handling

- Uses `hanziconv` library for traditional/simplified Chinese conversion
- Scripture citations must use traditional Chinese book names (e.g., "約翰福音" not "约翰福音")
- Hymn lyrics are stored as downloaded (usually traditional Chinese)

---

## Advanced Usage

### Streamlit Web UI

Launch interactive slide generator:

```bash
make streamlit-slides
# Opens at http://localhost:8501/slides
```

### Jupyter Notebooks

```bash
# One-time setup
make ipykernel

# Launch Jupyter
make jupyter
```

### Direct Python Module Usage

```bash
# Scripture lookup
uv run python -m bible.scripture --bible_citations "約翰福音3:16"

# Hymn downloading
uv run python -m hymns.zanmei -v 1

# Slide generation
uv run python mvccc/slides.py --pptx=output.pptx --flagfile=services/2025-01-12.flags
```

---

## Troubleshooting

### Slides Don't Generate

1. **Check flag file exists:** `services/YYYY-MM-DD.flags`
2. **Verify hymn resources downloaded:** `make download`
    - if processed/mvccc/ is not empty, don't `make download`
    - if the hymn index in processed/mvccc/ available, but with slight different title, use the name in processed/mvccc/.
    - if the hymn is not available in processed/mvccc/, the image copy maybe available in download/zanmei, create the slide for the hymn and put in processed/mvccc/
3. **Check template exists:** `mvccc_master.pptx` or configured template

### Scripture Not Found

1. **Verify Bible data downloaded:** `make ibibles.net` or `make bible.cloud`
2. **Check citation format:** Use traditional Chinese book names
3. **Test with known verse:** `make scripture VERSES="約翰福音3:16"`

### Import Errors

1. **Sync dependencies:** `uv sync`
2. **Check Python version:** `python --version` (must be 3.8+)
3. **Verify virtual environment:** `uv run python` ensures correct environment

---

## Additional Resources

- **Flag File Examples:** Check `services/` directory for past service examples
- **Hymn Sources:** See `README.md` for links to online hymnal resources
