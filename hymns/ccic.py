#!/usr/bin/env python3
"""Scraper for CCIC-SJ hymn PPT files.

Downloads hymn PPT files from https://ccic-sj-mandarin.s3-us-west-2.amazonaws.com/Hymns/ppt/

Usage:
    # Download all missing hymns (compared to processed/mvccc/)
    uv run python -m hymns.ccic

    # Download specific hymn by number
    uv run python -m hymns.ccic --hymn_number=19

    # List missing hymns without downloading
    uv run python -m hymns.ccic --list_missing
"""

import asyncio
import re
from pathlib import Path

import attr
from absl import app, flags, logging as log
from aiohttp import ClientSession

from hymns import fetch

FLAGS = flags.FLAGS

# CCIC hymn index page
CCIC_INDEX_URL = "https://ccic-sj-mandarin.s3-us-west-2.amazonaws.com/Hymns/ppt/index.html"
CCIC_BASE_URL = "https://ccic-sj-mandarin.s3-us-west-2.amazonaws.com/Hymns/ppt"


@attr.s
class Hymn:
    no: str = attr.ib()  # e.g., "001", "019"
    name: str = attr.ib()  # English name from filename
    ppt_filename: str = attr.ib()  # Original filename


def _normalize_number(no: str) -> str:
    """Normalize hymn number to 3-digit padded format."""
    if "-" in no:
        parts = no.split("-")
        return f"{int(parts[0]):03d}-{parts[1]}"
    return f"{int(no):03d}"


def _ppt_path(hymn: Hymn, output_dir: Path) -> Path:
    """Get the PPT file path for a hymn."""
    return output_dir / hymn.ppt_filename


async def fetch_index(session: ClientSession, cache_dir: Path | None = None) -> list[Hymn]:
    """Fetch the hymn index and return list of Hymn objects."""
    cache_path = cache_dir / "ccic_index.html" if cache_dir else None

    if cache_path and cache_path.exists():
        log.info(f"Using cached index: {cache_path}")
        content = cache_path.read_bytes()
    else:
        status, content = await fetch(session, CCIC_INDEX_URL)
        if status != 200:
            raise RuntimeError(f"Failed to fetch index: status={status}")
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(content)

    html_content = content.decode("utf-8", errors="replace")

    # Extract all PPT links: href="001_GreatGodWeSingYourMightyHand.ppt"
    pattern = r'href="(\d+_[^"]+\.ppt)"'
    matches = re.findall(pattern, html_content)

    hymns = {}
    for filename in matches:
        # Parse: 001_GreatGodWeSingYourMightyHand.ppt
        match = re.match(r"^(\d+)_(.+)\.ppt$", filename)
        if match:
            num = int(match.group(1))
            name = match.group(2)
            no = f"{num:03d}"

            if no not in hymns:  # Avoid duplicates
                hymns[no] = Hymn(no=no, name=name, ppt_filename=filename)

    result = sorted(hymns.values(), key=lambda h: h.no)
    log.info(f"Found {len(result)} hymns in index")
    return result


async def fetch_ppt(session: ClientSession, hymn: Hymn) -> bytes | None:
    """Fetch PPT file for a hymn."""
    url = f"{CCIC_BASE_URL}/{hymn.ppt_filename}"
    log.info(f"Fetching PPT for {hymn.no} - {hymn.name}")

    try:
        status, content = await fetch(session, url)
        if status != 200:
            log.warning(f"Failed to fetch {url}: status={status}")
            return None
        return content
    except Exception as e:
        log.exception(f"Error fetching PPT for {hymn.no}: {e}")
        return None


def get_existing_hymn_numbers(directory: Path) -> set[str]:
    """Get set of hymn numbers already in directory."""
    numbers = set()
    for path in directory.glob("*.pptx"):
        match = re.match(r"^(\d{3}(?:-\d+)?)", path.stem)
        if match:
            numbers.add(match.group(1))
    for path in directory.glob("*.ppt"):
        match = re.match(r"^(\d{3}(?:-\d+)?)", path.stem)
        if match:
            numbers.add(match.group(1))
    for path in directory.glob("*.md"):
        match = re.match(r"^(\d{3}(?:-\d+)?)", path.stem)
        if match:
            numbers.add(match.group(1))
    return numbers


async def download_missing(
    existing_dir: Path,
    output_dir: Path,
    cache_dir: Path | None = None,
    specific_number: str | None = None,
) -> list[Path]:
    """Download missing hymns and save as PPT files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    async with ClientSession() as session:
        # Fetch index
        hymns = await fetch_index(session, cache_dir)

        if specific_number:
            # Download specific hymn
            hymns = [h for h in hymns if h.no == specific_number]
            if not hymns:
                log.warning(f"Hymn {specific_number} not found in index")
                return []
        else:
            # Filter to missing hymns
            existing = get_existing_hymn_numbers(existing_dir)
            hymns = [h for h in hymns if h.no not in existing]
            log.info(f"Found {len(hymns)} missing hymns")

        # Download PPT files
        saved = []
        for hymn in hymns:
            content = await fetch_ppt(session, hymn)
            if content:
                ppt_path = _ppt_path(hymn, output_dir)
                ppt_path.write_bytes(content)
                log.info(f"Saved: {ppt_path}")
                saved.append(ppt_path)

            # Be polite to the server
            await asyncio.sleep(0.3)

        return saved


async def list_missing(existing_dir: Path, cache_dir: Path | None = None) -> list[Hymn]:
    """List hymns that are missing from existing directory."""
    async with ClientSession() as session:
        hymns = await fetch_index(session, cache_dir)
        existing = get_existing_hymn_numbers(existing_dir)
        missing = [h for h in hymns if h.no not in existing]
        return missing


def main(_):
    from base import initialize_logging

    initialize_logging()

    existing_dir = Path(FLAGS.existing_dir)
    output_dir = Path(FLAGS.output_dir)
    cache_dir = Path(FLAGS.cache_dir) if FLAGS.cache_dir else None

    if FLAGS.list_missing:
        missing = asyncio.run(list_missing(existing_dir, cache_dir))
        print(f"Missing {len(missing)} hymns:")  # noqa: T201
        for hymn in missing:
            print(f"  {hymn.no}: {hymn.name}")  # noqa: T201
    else:
        specific = _normalize_number(FLAGS.hymn_number) if FLAGS.hymn_number else None
        saved = asyncio.run(download_missing(existing_dir, output_dir, cache_dir, specific))
        print(f"Saved {len(saved)} hymn PPT files")  # noqa: T201


if __name__ == "__main__":
    flags.DEFINE_string("existing_dir", "processed/mvccc", "Directory with existing hymn files")
    flags.DEFINE_string("output_dir", "processed/mvccc", "Output directory for PPT files")
    flags.DEFINE_string("cache_dir", "download/ccic", "Cache directory for downloaded HTML")
    flags.DEFINE_string("hymn_number", None, "Download specific hymn number only")
    flags.DEFINE_bool("list_missing", False, "List missing hymns without downloading")

    app.run(main)
