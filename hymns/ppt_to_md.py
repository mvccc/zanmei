#!/usr/bin/env python3
"""Convert PPT files to markdown format.

Extracts text from PowerPoint 97-2003 (.ppt) files and converts to markdown.

Usage:
    uv run python -m hymns.ppt_to_md processed/mvccc/019_OneDay.ppt
    uv run python -m hymns.ppt_to_md --all  # Convert all .ppt files
"""

import re
import struct
from pathlib import Path

import olefile
from absl import app, flags, logging as log

FLAGS = flags.FLAGS


def extract_ppt_text(filepath: Path) -> list[str]:
    """Extract text from PowerPoint 97-2003 (.ppt) file."""
    ole = olefile.OleFileIO(str(filepath))
    ppt_stream = ole.openstream("PowerPoint Document").read()
    ole.close()

    texts = []
    i = 0
    while i < len(ppt_stream) - 8:
        # Record header: type (2 bytes), instance/version (2 bytes), length (4 bytes)
        rec_type = struct.unpack_from("<H", ppt_stream, i + 2)[0]
        rec_len = struct.unpack_from("<I", ppt_stream, i + 4)[0]

        # TextCharsAtom = 0x0FA0 (4000) - UTF-16LE encoded text
        if rec_type == 0x0FA0 and rec_len > 0 and rec_len < 100000:
            text_data = ppt_stream[i + 8 : i + 8 + rec_len]
            try:
                text = text_data.decode("utf-16le", errors="ignore").strip()
                if text and len(text) > 1:
                    texts.append(text)
            except Exception:
                pass

        i += 1

    return texts


def parse_hymn_texts(texts: list[str]) -> tuple[str, str, list[tuple[str, list[str]]]]:
    """Parse extracted texts into hymn structure.

    Returns: (number, title, [(verse_marker, [lines]), ...])
    """
    title = ""
    number = ""
    verses = []

    for text in texts:
        # Skip template text
        if "Click to edit" in text:
            continue

        # Look for hymn number (e.g., "聖詩 19")
        num_match = re.match(r"聖詩\s*(\d+)", text)
        if num_match:
            number = num_match.group(1)
            continue

        # Look for title line - Chinese title followed by author/English info
        # e.g., "一日\rJ.W. Chapman                    One Day                          C.H. Marsh"
        title_match = re.match(r"^([\u4e00-\u9fff，。、！？\s]+?)[\r\n]", text)
        if title_match and not title:
            potential_title = title_match.group(1).strip()
            if 1 < len(potential_title) < 15:
                title = potential_title
                continue

        # Look for standalone Chinese title line (short line with hymn name)
        if not title and re.match(r"^[\u4e00-\u9fff]+$", text.strip()) and len(text.strip()) < 10:
            title = text.strip()
            continue

        # Look for verse content (has verse number like "1." or "2.")
        verse_match = re.match(r"^(\d+)\.\s*(.+)", text, re.DOTALL)
        if verse_match:
            verse_num = verse_match.group(1)
            content = verse_match.group(2)

            # Split into verse and chorus
            parts = re.split(r"\(副歌\)", content)

            verse_lines = []
            chorus_lines = []

            if len(parts) >= 1:
                # Verse part
                verse_text = parts[0].strip()
                # Split by line breaks and clean
                for line in re.split(r"[\r\n\x0b]+", verse_text):
                    line = line.strip().strip("\u3000").strip()
                    if line and not re.match(r"^[\s\u3000]*$", line):
                        verse_lines.append(line)

            if len(parts) >= 2:
                # Chorus part
                chorus_text = parts[1].strip()
                for line in re.split(r"[\r\n\x0b]+", chorus_text):
                    line = line.strip().strip("\u3000").strip()
                    if line and not re.match(r"^[\s\u3000]*$", line):
                        chorus_lines.append(line)

            if verse_lines:
                verses.append((f"({verse_num})", verse_lines))
            if chorus_lines:
                verses.append((f"({verse_num})", chorus_lines))

    return number, title, verses


def convert_to_markdown(number: str, title: str, verses: list[tuple[str, list[str]]]) -> str:
    """Convert parsed hymn to markdown format."""
    lines = [f"# {title}", ""]

    for verse_marker, verse_lines in verses:
        lines.append(f"## {verse_marker}")
        for line in verse_lines:
            lines.append(f"{line}  ")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def convert_ppt_to_md(ppt_path: Path, output_dir: Path | None = None) -> Path | None:
    """Convert a single PPT file to markdown."""
    log.info(f"Converting {ppt_path}")

    texts = extract_ppt_text(ppt_path)
    if not texts:
        log.warning(f"No text found in {ppt_path}")
        return None

    number, title, verses = parse_hymn_texts(texts)

    if not verses:
        log.warning(f"No verses parsed from {ppt_path}")
        return None

    if not title:
        # Try to get title from filename
        match = re.match(r"^\d+_(.+)\.ppt$", ppt_path.name)
        if match:
            title = match.group(1)
        else:
            title = "Unknown"

    if not number:
        # Get number from filename
        match = re.match(r"^(\d+)_", ppt_path.name)
        if match:
            number = match.group(1)

    md_content = convert_to_markdown(number, title, verses)

    # Determine output path
    if output_dir is None:
        output_dir = ppt_path.parent

    # Create Chinese filename
    md_filename = f"{int(number):03d}_{title}.md"
    md_path = output_dir / md_filename

    md_path.write_text(md_content, encoding="utf-8")
    log.info(f"Saved: {md_path}")

    return md_path


def main(argv):
    from base import initialize_logging

    initialize_logging()

    if FLAGS.all:
        # Convert all .ppt files in processed/mvccc
        ppt_dir = Path(FLAGS.ppt_dir)
        output_dir = Path(FLAGS.output_dir) if FLAGS.output_dir else None

        ppt_files = list(ppt_dir.glob("*.ppt"))
        log.info(f"Found {len(ppt_files)} PPT files")

        converted = 0
        for ppt_path in ppt_files:
            result = convert_ppt_to_md(ppt_path, output_dir)
            if result:
                converted += 1

        print(f"Converted {converted} of {len(ppt_files)} PPT files")  # noqa: T201
    else:
        # Convert specific file(s)
        if len(argv) < 2:
            print("Usage: python -m hymns.ppt_to_md <file.ppt> [file2.ppt ...]")  # noqa: T201
            print("       python -m hymns.ppt_to_md --all")  # noqa: T201
            return

        output_dir = Path(FLAGS.output_dir) if FLAGS.output_dir else None

        for ppt_file in argv[1:]:
            convert_ppt_to_md(Path(ppt_file), output_dir)


if __name__ == "__main__":
    flags.DEFINE_bool("all", False, "Convert all PPT files in ppt_dir")
    flags.DEFINE_string("ppt_dir", "processed/mvccc", "Directory with PPT files")
    flags.DEFINE_string("output_dir", None, "Output directory (default: same as input)")

    app.run(main)
