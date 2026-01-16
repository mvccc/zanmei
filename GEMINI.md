# GEMINI Project Analysis

## Project Overview

This is a Python project designed to automate the creation of PowerPoint slides for church services at MVCCC (presumably, based on the `mvccc` module name). The project streamlines the process of assembling weekly service presentations, including hymns, scripture readings, sermon titles, and other liturgical elements.

The key functionalities are:
*   Generating a complete PowerPoint presentation from a set of flags that define the service's content for a specific date.
*   Extracting text content from existing PowerPoint files.
*   Searching and retrieving scripture verses from the Bible.
*   Managing and downloading a collection of hymns from various online sources.

The project is structured into several Python modules:
*   `mvccc`: Handles the core slide generation logic, using a master template (`mvccc_master_modern_dark.pptx`) and the `python-pptx` library.
*   `bible`: Contains functionality for parsing and looking up Bible verses.
*   `hymns`: Includes scripts for downloading hymn lyrics and metadata from different websites (`zanmei.cc`, `hoc5.net`, `mvcccit.org`).
*   `services`: This directory contains `.flags` files for each Sunday service, which specify the content for the slides.

The project uses `uv` for managing the Python environment and dependencies, and `ruff` for code formatting and linting.

## Building and Running

The project uses a `Makefile` to simplify common tasks.

### Initialization

To set up the development environment and download necessary data, run:
```bash
make init
```
This command will install `uv`, sync the Python environment, and download hymn and bible data.

### Generating Slides

To generate the PowerPoint slides for a specific Sunday service:

1.  Create a `.flags` file in the `services/` directory (e.g., `services/2026-01-11.flags`). This file defines the content for the slides, such as the hymns, scripture readings, and sermon title.

    Example `services/2026-01-11.flags`:
    ```
    --choir=Hymn Title for Choir
    --hymns=Hymn Title 1
    --hymns=Hymn Title 2
    --scripture=John 3:16
    --memorize=John 3:16
    --message=Sermon Title
    --messager=Pastor's Name
    ```

2.  Run the `make slides` command, specifying the date:
    ```bash
    make slides SUNDAY=2026-01-11
    ```
    This will generate a `2026-01-11.pptx` file in the root directory.

### Other Key Commands

*   **Run tests:**
    ```bash
    make test
    ```
*   **Lint the code:**
    ```bash
    make lint
    ```
*   **Format the code:**
    ```bash
    make format
    ```
*   **Fetch scripture verses:**
    ```bash
    make scripture VERSES="Romans 12:1-2"
    ```

## Development Conventions

*   **Dependency Management:** The project uses `uv` to manage dependencies, which are defined in `pyproject.toml`.
*   **Code Style:** The project uses `ruff` for code formatting and linting, with rules configured in `pyproject.toml`. This ensures a consistent code style.
*   **Command-line Interface:** The scripts use the `absl-py` library to define and parse command-line flags.
*   **Testing:** Tests are located in the `tests/` directory and are run using `pytest`.
*   **Modularity:** The project is organized into distinct modules for different functionalities (bible, hymns, mvccc), which promotes separation of concerns.
