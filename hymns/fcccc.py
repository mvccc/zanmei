#!/usr/bin/env python3
"""Scraper for FCCCC hymn lyrics.

Downloads hymn lyrics from https://fcccc.net/hymns/ and saves them as markdown files.

Usage:
    # Download all missing hymns (compared to processed/mvccc/)
    uv run python -m hymns.fcccc

    # Download specific hymn by number
    uv run python -m hymns.fcccc --hymn_number=75

    # Download to custom directory
    uv run python -m hymns.fcccc --output_dir=download/fcccc

    # List missing hymns without downloading
    uv run python -m hymns.fcccc --list_missing
"""

import asyncio
import re
from pathlib import Path

import attr
from absl import app, flags, logging as log
from aiohttp import ClientSession
from bs4 import BeautifulSoup, NavigableString
from opencc import OpenCC

from hymns import fetch

# Initialize OpenCC converter (Simplified to Traditional, Taiwan standard)
_cc = OpenCC("s2twp")

FLAGS = flags.FLAGS

# FCCCC hymn index page
FCCCC_INDEX_URL = "https://fcccc.net/hymns/ChineseWorship_HymnsForChurch.htm"
FCCCC_BASE_URL = "https://fcccc.net/hymns"


@attr.s
class Hymn:
    no: str = attr.ib()  # e.g., "001", "281-1"
    name: str = attr.ib()
    lyrics_url: str = attr.ib()


def _normalize_number(no: str) -> str:
    """Normalize hymn number to 3-digit padded format."""
    # Handle special cases like "281-1", "488-1"
    if "-" in no:
        parts = no.split("-")
        return f"{int(parts[0]):03d}-{parts[1]}"
    return f"{int(no):03d}"


def _to_traditional(text: str) -> str:
    """Convert to traditional Chinese using OpenCC."""
    return _cc.convert(text.strip())


def _clean_title(title: str) -> str:
    """Clean hymn title, convert to traditional Chinese."""
    return _to_traditional(title)


def _md_path(hymn: Hymn, output_dir: Path) -> Path:
    """Get the markdown file path for a hymn."""
    return output_dir / f"{hymn.no}_{hymn.name}.md"


async def fetch_index(session: ClientSession, cache_dir: Path | None = None) -> list[Hymn]:
    """Fetch the hymn index and return list of Hymn objects."""
    cache_path = cache_dir / "ChineseWorship_HymnsForChurch.htm" if cache_dir else None

    if cache_path and cache_path.exists():
        log.info(f"Using cached index: {cache_path}")
        content = cache_path.read_bytes()
    else:
        status, content = await fetch(session, FCCCC_INDEX_URL)
        if status != 200:
            raise RuntimeError(f"Failed to fetch index: status={status}")
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(content)

    soup = BeautifulSoup(content.decode("utf-8", errors="replace"), "html.parser")
    hymns = []

    # Find all table rows - the index is a table with hymn info
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        # First column: hymn number
        no_text = tds[0].get_text(strip=True)
        if not no_text or not re.match(r"^\d+(-\d+)?$", no_text):
            continue

        # Second column: Chinese title with link
        title_td = tds[1]
        link = title_td.find("a")
        if not link:
            continue

        href = link.get("href", "")
        if not href or not href.endswith(".htm"):
            continue

        title = link.get_text(strip=True)
        if not title:
            continue

        no = _normalize_number(no_text)
        name = _clean_title(title)

        # Build full URL for lyrics
        lyrics_url = f"{FCCCC_BASE_URL}/{href}"

        hymn = Hymn(no=no, name=name, lyrics_url=lyrics_url)
        hymns.append(hymn)
        log.debug(f"Found hymn: {no} - {name}")

    log.info(f"Found {len(hymns)} hymns in index")
    return hymns


def _has_yellow_color(tag) -> bool:
    """Check if a tag or its parents have yellow color style (indicating chorus)."""
    style = tag.get("style", "") if hasattr(tag, "get") else ""
    if "color:yellow" in style or "color: yellow" in style:
        return True
    # Check parent
    if tag.parent and hasattr(tag.parent, "get"):
        parent_style = tag.parent.get("style", "")
        if "color:yellow" in parent_style or "color: yellow" in parent_style:
            return True
    return False


def _extract_text_with_color(element) -> list[tuple[str, bool]]:
    """Extract text segments with their color info (is_chorus).

    Returns list of (text, is_chorus) tuples.
    """
    segments = []

    for child in element.descendants:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text and text != "\xa0":  # Skip empty and nbsp
                # Check if this text is in a yellow-colored context
                parent = child.parent
                is_chorus = False
                while parent:
                    style = parent.get("style", "") if hasattr(parent, "get") else ""
                    if "color:yellow" in style or "color: yellow" in style:
                        is_chorus = True
                        break
                    parent = getattr(parent, "parent", None)
                segments.append((text, is_chorus))

    return segments


def _parse_lyrics_html(html_content: str) -> tuple[str, list[tuple[str, list[str]]]]:
    """Parse lyrics HTML and return (title, [(verse_marker, [lines]), ...]).

    The HTML is Word-exported with a table structure:
    - First column: verse numbers (1, 2, 3...)
    - Second column: lyrics (verse in white, chorus in yellow)
    """
    soup = BeautifulSoup(html_content, "html.parser")

    title = ""
    verses = []

    # Find the main table
    table = soup.find("table")
    if not table:
        log.warning("No table found in HTML")
        return title, verses

    rows = table.find_all("tr")

    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 2:
            continue

        first_col = tds[0].get_text(strip=True)
        second_col = tds[1]

        # Check if this is the title row (has title in large text, no verse number)
        if not first_col or first_col == "\xa0":
            # Could be title or empty row
            text = second_col.get_text(strip=True)
            if text and not title and len(text) < 20:
                # Likely the title
                title = _to_traditional(text)
            continue

        # Check if first column is a verse number
        if re.match(r"^\d+$", first_col):
            verse_num = first_col

            # Extract text segments with color info
            segments = _extract_text_with_color(second_col)

            if not segments:
                continue

            # Group segments into verse and chorus
            verse_lines = []
            chorus_lines = []

            for text, is_chorus in segments:
                # Clean up the text - remove extra spaces, normalize punctuation
                text = re.sub(r"\s+", "", text)  # Remove all whitespace for Chinese
                if not text:
                    continue

                # Split on Chinese punctuation to get individual lines
                # Lines typically end with ，。；！？
                lines = re.split(r"([，。；！？])", text)

                # Recombine punctuation with preceding text
                combined = []
                current = ""
                for part in lines:
                    if re.match(r"^[，。；！？]$", part):
                        current += part
                        if current:
                            combined.append(current)
                            current = ""
                    else:
                        if current:
                            combined.append(current)
                        current = part
                if current:
                    combined.append(current)

                for line in combined:
                    if line:
                        if is_chorus:
                            chorus_lines.append(line)
                        else:
                            verse_lines.append(line)

            # Add verse section
            if verse_lines:
                verses.append((f"({verse_num})", [_to_traditional(ln) for ln in verse_lines]))

            # Add chorus section with same number
            if chorus_lines:
                verses.append((f"({verse_num})", [_to_traditional(ln) for ln in chorus_lines]))

    return title, verses


async def fetch_lyrics(session: ClientSession, hymn: Hymn) -> str | None:
    """Fetch lyrics for a hymn and return as markdown string."""
    log.info(f"Fetching lyrics for {hymn.no} - {hymn.name}")

    try:
        status, content = await fetch(session, hymn.lyrics_url)
        if status != 200:
            log.warning(f"Failed to fetch {hymn.lyrics_url}: status={status}")
            return None

        html_content = content.decode("utf-8", errors="replace")
        title, verses = _parse_lyrics_html(html_content)

        if not verses:
            log.warning(f"No verses found for {hymn.no} - {hymn.name}")
            return None

        # Use hymn name as title (already converted to traditional)
        md_lines = [f"# {hymn.name}", ""]

        for verse_marker, lines in verses:
            md_lines.append(f"## {verse_marker}")
            for line in lines:
                md_lines.append(f"{line}  ")
            md_lines.append("")

        return "\n".join(md_lines).rstrip() + "\n"

    except Exception as e:
        log.exception(f"Error fetching lyrics for {hymn.no}: {e}")
        return None


def get_existing_hymn_numbers(directory: Path) -> set[str]:
    """Get set of hymn numbers already in directory."""
    numbers = set()
    for path in directory.glob("*.pptx"):
        match = re.match(r"^(\d{3}(?:-\d+)?)", path.stem)
        if match:
            numbers.add(match.group(1))
    for path in directory.glob("*.md"):
        match = re.match(r"^(\d{3}(?:-\d+)?)", path.stem)
        if match:
            numbers.add(match.group(1))
    return numbers


def get_fcccc_hymn_numbers(directory: Path) -> set[str]:
    """Get set of hymn numbers that came from FCCCC (md files without matching pptx)."""
    pptx_numbers = set()
    for path in directory.glob("*.pptx"):
        match = re.match(r"^(\d{3}(?:-\d+)?)", path.stem)
        if match:
            pptx_numbers.add(match.group(1))

    fcccc_numbers = set()
    for path in directory.glob("*.md"):
        match = re.match(r"^(\d{3}(?:-\d+)?)", path.stem)
        if match:
            num = match.group(1)
            if num not in pptx_numbers:
                fcccc_numbers.add(num)
    return fcccc_numbers


async def download_missing(
    existing_dir: Path,
    output_dir: Path,
    cache_dir: Path | None = None,
    specific_number: str | None = None,
    force: bool = False,
) -> list[Path]:
    """Download missing hymns and save as markdown files."""
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
        elif force:
            # Re-download FCCCC hymns (md files without pptx)
            fcccc_nums = get_fcccc_hymn_numbers(existing_dir)
            hymns = [h for h in hymns if h.no in fcccc_nums]
            log.info(f"Force re-downloading {len(hymns)} FCCCC hymns")
        else:
            # Filter to missing hymns
            existing = get_existing_hymn_numbers(existing_dir)
            hymns = [h for h in hymns if h.no not in existing]
            log.info(f"Found {len(hymns)} missing hymns")

        # Download lyrics
        saved = []
        for hymn in hymns:
            md_content = await fetch_lyrics(session, hymn)
            if md_content:
                md_path = _md_path(hymn, output_dir)
                md_path.write_text(md_content, encoding="utf-8")
                log.info(f"Saved: {md_path}")
                saved.append(md_path)

            # Be polite to the server
            await asyncio.sleep(0.5)

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
        saved = asyncio.run(download_missing(existing_dir, output_dir, cache_dir, specific, FLAGS.force))
        print(f"Saved {len(saved)} hymn lyrics")  # noqa: T201


if __name__ == "__main__":
    flags.DEFINE_string("existing_dir", "processed/mvccc", "Directory with existing hymn files")
    flags.DEFINE_string("output_dir", "processed/mvccc", "Output directory for markdown files")
    flags.DEFINE_string("cache_dir", "download/fcccc", "Cache directory for downloaded HTML")
    flags.DEFINE_string("hymn_number", None, "Download specific hymn number only")
    flags.DEFINE_bool("list_missing", False, "List missing hymns without downloading")
    flags.DEFINE_bool("force", False, "Re-download FCCCC hymns (overwrite existing)")

    app.run(main)
