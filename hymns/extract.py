#!/usr/bin/env python3

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import ollama
from absl import app, flags, logging as log

FLAGS = flags.FLAGS

# OCR configuration
OCR_MODEL = "deepseek-ocr:latest"  # Vision model for OCR
OCR_TIMEOUT = 300  # 5 minutes


# OCR prompts - keep simple to avoid prompt leakage in output
PROMPT_PURE = "Read all text in this image."

PROMPT_MARKDOWN = "Read all text in this image and format as markdown."

PROMPT_JSON = "Read all text in this image and return as JSON."


@dataclass
class OcrLine:
    text: str
    confidence: float | None = None


@dataclass
class HymnText:
    number: int
    filename: str
    title: str
    lines: list[OcrLine] = field(default_factory=list)
    full_text: str = ""
    language: str = "unknown"  # "chinese", "english", "both"
    structured_data: dict | None = None  # For JSON-mode parsing


def detect_language(text: str) -> str:
    """Detect if text is Chinese, English, or mixed."""
    has_chinese = any("\u4e00" <= c <= "\u9fff" for c in text)
    has_english = any(ord(c) < 128 and c.isalpha() for c in text)

    if has_chinese and has_english:
        return "both"
    elif has_chinese:
        return "chinese"
    elif has_english:
        return "english"
    else:
        return "unknown"


def clean_ocr_text(text: str) -> str:
    """Clean common OCR artifacts."""
    # Remove common artifacts
    replacements = [
        (r"\s+", " "),  # Multiple spaces to single
        (r"\n\s*\n", "\n\n"),  # Multiple newlines to double
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    return text.strip()


def extract_chinese(text: str) -> str:
    """Extract only Chinese characters from text, preserving line structure.

    The OCR outputs each character on its own line with verse numbers (1, 2, 3, 4).
    This function extracts Chinese characters and groups them by verse.
    """
    lines = text.split("\n")
    result_lines = []
    current_chars = []

    for line in lines:
        line = line.strip()
        # Check if line is a verse number (standalone digit)
        if re.match(r"^\d+$", line):
            # Save accumulated chars and start new group
            if current_chars:
                result_lines.append("".join(current_chars))
                current_chars = []
        else:
            # Extract Chinese characters from this line
            chinese = re.findall(r"[\u4e00-\u9fff]", line)
            current_chars.extend(chinese)

    # Don't forget last group
    if current_chars:
        result_lines.append("".join(current_chars))

    return "\n".join(result_lines)


def ollama_ocr(image_path: Path, prompt: str = PROMPT_PURE) -> str | None:
    """Perform OCR using Ollama library."""

    try:
        client = ollama.Client(host="http://localhost:11434")
    except Exception as e:
        log.error(f"Failed to connect to Ollama: {e}")
        return None

    try:
        # Perform OCR with vision model
        # IMPORTANT: temperature=0.0 is critical to prevent hallucination.
        # Without it, the model generates plausible but invented text instead
        # of actually reading the image content.
        response = client.chat(
            model=OCR_MODEL,
            messages=[{"role": "user", "content": prompt, "images": [str(image_path)]}],
            options={"temperature": 0.0, "num_predict": 2048},
            stream=False,
        )

        # Extract content from response
        if response:
            # Handle both dict and object-style responses
            if hasattr(response, "message"):
                content = response.message.content if hasattr(response.message, "content") else ""
            elif isinstance(response, dict) and response.get("message"):
                content = response["message"].get("content", "")
            else:
                log.warning(f"Unexpected response format: {type(response)}")
                content = ""

            if content:
                return content
            else:
                log.warning(f"Empty content in response for {image_path.name}")
                return None
        log.warning(f"No response from model for {image_path.name}")
        return None

    except Exception as e:
        log.error(f"Ollama OCR failed for {image_path.name}: {e}")
        return None


def extract_from_image(image_path: Path, output_format: str = "pure") -> HymnText | None:
    """Extract text from a hymn image using Ollama vision model."""

    log.info(f"Processing {image_path.name}")

    # Extract hymn number from filename
    match = re.match(r"^(\d+)", image_path.stem)
    if not match:
        log.warning(f"Cannot extract hymn number from {image_path.name}")
        return None
    hymn_number = int(match.group(1))

    # Select prompt based on output format
    # Note: "chinese" uses PROMPT_PURE then post-processes to extract Chinese only
    if output_format == "markdown":
        prompt = PROMPT_MARKDOWN
    elif output_format == "json":
        prompt = PROMPT_JSON
    else:
        prompt = PROMPT_PURE

    # Perform OCR using Ollama
    text = ollama_ocr(image_path, prompt)
    if not text:
        log.warning(f"No text extracted from {image_path.name}")
        return None

    # For "chinese" format, extract Chinese from raw text (before cleaning collapses lines)
    full_text = extract_chinese(text) if output_format == "chinese" else clean_ocr_text(text)

    # Parse based on format
    structured_data = None

    if output_format == "json":
        # Try to parse JSON response
        try:
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                structured_data = json.loads(json_str)
                title = structured_data.get("title", "")
                language = structured_data.get("language", detect_language(full_text))
                lines_text = full_text
            else:
                title = [line.strip() for line in full_text.split("\n") if line.strip()][0] if full_text else ""
                language = detect_language(full_text)
                lines_text = full_text
        except json.JSONDecodeError as e:
            log.warning(f"Failed to parse JSON response: {e}, falling back to plain text")
            lines = [line.strip() for line in full_text.split("\n") if line.strip()]
            title = lines[0] if lines else ""
            language = detect_language(full_text)
            lines_text = full_text
    else:
        # Extract title (first non-empty line)
        lines = [line.strip() for line in full_text.split("\n") if line.strip()]
        title = lines[0] if lines else ""
        language = detect_language(full_text)
        lines_text = full_text

    # Create OCR lines (without confidence since vision models don't provide it)
    ocr_lines = [OcrLine(text=line.strip()) for line in lines_text.split("\n") if line.strip()]

    return HymnText(
        number=hymn_number,
        filename=image_path.name,
        title=title,
        lines=ocr_lines,
        full_text=full_text,
        language=language,
        structured_data=structured_data,
    )


def main(_):
    # Check Ollama API
    try:
        client = ollama.Client(host="http://localhost:11434")
        list_result = client.list()
        models = list_result.models if hasattr(list_result, "models") else []
        available = [m.model for m in models]
        log.info(f"Ollama API is running. Available models: {len(available)}")
        if OCR_MODEL not in available:
            available_vision = [
                m for m in available if "vision" in m.lower() or "llava" in m.lower() or "deepseek" in m.lower()
            ]
            log.warning(f"Model '{OCR_MODEL}' not found. Available: {available}")
            if available_vision:
                log.info(f"Consider using a vision model: {available_vision}")
    except Exception as e:
        log.error(f"Cannot connect to Ollama API: {e}")
        log.error("Make sure Ollama is running with: ollama serve")
        return

    download_dir = Path(FLAGS.download_dir)
    output_dir = Path(FLAGS.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all PNG files
    image_files = sorted(download_dir.glob("*.png"))

    # Filter by hymn numbers if specified
    if FLAGS.hymns:
        requested_numbers = set()
        for item in FLAGS.hymns.split(","):
            item = item.strip()
            # Handle ranges like "100-105"
            if "-" in item:
                try:
                    start, end = map(int, item.split("-"))
                    requested_numbers.update(range(start, end + 1))
                except ValueError:
                    log.warning(f"Invalid range: {item}")
            else:
                try:
                    requested_numbers.add(int(item))
                except ValueError:
                    log.warning(f"Invalid hymn number: {item}")

        log.info(f"Requested numbers: {sorted(requested_numbers)}")

        # Filter files
        image_files_filtered = []
        for f in image_files:
            match = re.match(r"^(\d+)", f.stem)
            if match and int(match.group(1)) in requested_numbers:
                image_files_filtered.append(f)
        image_files = image_files_filtered
        log.info(f"Filtered to {len(image_files)} hymns from selection: {sorted(requested_numbers)}")

    log.info(f"Processing {len(image_files)} hymn images (format: {FLAGS.format})")

    # Extract text from each image
    results = []
    for image_path in image_files:
        hymn_text = extract_from_image(image_path, FLAGS.format)
        if hymn_text:
            # Save individual JSON
            output_path = output_dir / f"{hymn_text.number:03d}_text.json"
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(asdict(hymn_text), f, ensure_ascii=False, indent=2)

            # Save plain text version too
            txt_path = output_dir / f"{hymn_text.number:03d}_text.txt"
            with txt_path.open("w", encoding="utf-8") as f:
                f.write(hymn_text.full_text)

            # Save structured data if available
            if hymn_text.structured_data:
                struct_path = output_dir / f"{hymn_text.number:03d}_structured.json"
                with struct_path.open("w", encoding="utf-8") as f:
                    json.dump(hymn_text.structured_data, f, ensure_ascii=False, indent=2)

            results.append(
                {
                    "number": hymn_text.number,
                    "filename": hymn_text.filename,
                    "title": hymn_text.title,
                    "language": hymn_text.language,
                    "text_preview": hymn_text.full_text[:200] + "..."
                    if len(hymn_text.full_text) > 200
                    else hymn_text.full_text,
                    "has_structured": hymn_text.structured_data is not None,
                }
            )

            log.info(f"Saved {hymn_text.number:03d}: {hymn_text.language}")

    # Save summary
    summary_path = output_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    log.info(f"Processed {len(results)} hymns")
    log.info(f"Summary saved to {summary_path}")

    # Print statistics
    by_language = {}
    structured_count = 0
    for r in results:
        lang = r["language"]
        by_language[lang] = by_language.get(lang, 0) + 1
        if r.get("has_structured"):
            structured_count += 1

    log.info(f"Language breakdown: {by_language}")
    log.info(f"Structured output: {structured_count}/{len(results)}")


if __name__ == "__main__":
    flags.DEFINE_string("download_dir", "download/zanmei", "Directory containing hymn images")
    flags.DEFINE_string("output_dir", "processed/lyrics", "Directory to save extracted text")
    flags.DEFINE_string("hymns", None, "Comma-separated hymn numbers to extract (e.g., '1,2,3' or '100-105')")
    flags.DEFINE_enum(
        "format", "pure", ["pure", "markdown", "json", "chinese"], "Output format: pure, markdown, json, or chinese"
    )

    app.run(main)
