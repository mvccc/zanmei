# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python toolkit for generating church service PowerPoint presentations for MVCCC (Mountain View Chinese Christian Church). Downloads hymn resources from Chinese Christian hymn websites, retrieves Bible scripture passages, and assembles them into standardized slides.

## Key Technologies

- **Python 3.8+** with `uv` for dependency management
- **python-pptx**: PowerPoint generation
- **BeautifulSoup4** + **aiohttp**: Web scraping for hymns
- **pandas**: Bible verse lookup
- **absl-py**: CLI flag handling
- **Ruff**: Linting and formatting

## Common Commands

```bash
# Setup
make init                        # Install uv, sync deps, download resources

# Building slides
make slides SUNDAY=2024-03-24    # Generate for specific Sunday
make slides                      # Generate for next Sunday
make pptx_to_text PPTX=path.pptx # Extract text from PPTX

# Scripture lookup
make scripture VERSES="羅馬書12:1-2"
make scripture_compare           # Compare Bible sources

# Download hymn resources
make download                    # All sources
make zanmei / hoctoga / hoc5 / mvccc  # Individual sources

# Code quality
make format                      # Auto-format with Ruff
make lint                        # Check linting issues
make fix                         # Auto-fix linting issues
make check                       # Run lint + tests

# Testing
make test                        # Run all tests (includes lint)
make tests/bible/test_index.py   # Run specific test file
uv run pytest -k test_name       # Run by test name

# Development
make streamlit-slides            # Launch web UI at localhost:8501/slides
make jupyter                     # Launch Jupyter notebook
uv run python <script.py>        # Run script in environment
```

## Architecture

### Module Structure

**`mvccc/slides.py`**: Core slide generation
- `mvccc_slides()`: Orchestrates service slide creation
- `search_hymn_ppt()`: Finds hymn PPTX files with fuzzy matching for Chinese character variants (你/祢/袮, 寶/寳, 他/祂)
- Slide classes: `Prelude`, `Hymn`, `Section`, `Scripture`, `Memorize`, `Teaching`, `Blank`

**`bible/`**: Scripture handling
- `scripture.py`: Bible class with pandas DataFrame backend, supports `ibibles.net` and `bible.cloud` sources
- `index.py`: Parses Chinese citations like "馬太福音25:14-30" or "約翰福音3:16;14:6"

**`hymns/`**: Web scrapers for `zanmei.py`, `hoctoga.py`, `hoc5.py`, `mvccc.py`

### Service Configuration

Flag files at `services/{YYYY-MM-DD}.flags`:
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
--communion  # optional
```

### Data Flow

1. Hymns scraped from websites → stored as PPTX in `processed/{source}/`
2. Bible texts downloaded to `download/` → cached as CSV
3. `slides.py` reads `.flags` → searches hymns → retrieves verses → assembles PPTX from template

## Important Constraints

### python-pptx Limitations

Master slide templates (layouts, theme colors, fonts) **cannot be modified programmatically**. The library can only:
- ✅ Create slides using existing layouts
- ✅ Modify content on individual slides
- ❌ Modify master slide layouts or themes

Master templates must be edited manually in PowerPoint/Keynote.

### Chinese Character Handling

- Scripture citations require traditional Chinese book names (約翰福音, not 约翰福音)
- Bible sources differ in 神 vs 上帝 for "God" - handled via `--bible_word_god` flag
- `hanziconv` used for simplified→traditional conversion with manual corrections
