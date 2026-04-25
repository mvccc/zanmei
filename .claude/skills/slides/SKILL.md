---
name: slides
description: "Generate MVCCC Sunday service PowerPoint and Keynote slides from a worship program PDF. Parses the PDF to extract hymns, scripture, message info, creates a .flags file, runs make slides, and converts to .key."
when_to_use: "When the user provides a Sunday worship program PDF and wants slides generated."
argument-hint: "<path-to-pdf>"
arguments: [pdf_path]
allowed-tools:
  - Bash(make slides *)
  - Bash(osascript *)
  - Bash(ls *)
  - Read
  - Write
  - Glob
---

# Generate MVCCC Sunday Service Slides

Given a worship program PDF at `$pdf_path`, generate the Sunday service slides (PPTX + Keynote).

## Steps

1. **Read the PDF** to extract the worship program details.

2. **Determine the Sunday date** from the PDF content (look for a date like `主後 2026 年 X 月 X 日` or `MM/DD/YY` in the service schedule).

3. **Check for an existing flags file** at `services/{YYYY-MM-DD}.flags`. If one exists, confirm with the user before overwriting.

4. **Create the flags file** at `services/{YYYY-MM-DD}.flags` by extracting:
   - `--call_scripture=` from the 宣召 line (scripture citation)
   - `--hymns=` for each hymn in the 頌讚 section (use format `{number}_{title}`, e.g. `2_祢真偉大`)
   - `--scripture=` from the 讀經 line
   - `--memorize=` from the 金句 line
   - `--choir=` from the 獻詩 line (format `{number}_{title}`)
   - `--response=` from the 回應 line(s) (one per hymn)
   - `--message=` from the 信息 line
   - `--messager=` from the speaker name
   - `--communion` if communion is part of the service
   - Add a comment header: `# MVCCC 主日敬拜 {YYYY-MM-DD}`
   - Add a comment with message/speaker: `# 信息: {title} - {speaker}`

   Look at a recent flags file in `services/` for formatting reference.

   **Hymn number mapping**: The PDF shows hymn numbers like `#2`, `#213`. Map these to the flag format `{number}_{title}` (e.g., `--hymns=2_祢真偉大`). If no number is shown, use just the title.

   **Response hymn verses**: If the PDF specifies particular verses like `為主而活(1, 3)`, note this but include all verses in the flag (the slide generator handles full hymns). Mention to the user which verses were specified.

5. **Generate the PPTX**:
   ```
   make slides SUNDAY={YYYY-MM-DD}
   ```

6. **Convert to Keynote** using AppleScript:
   ```
   osascript -e '
   tell application "Keynote"
       set theFile to POSIX file "/Users/dfu/gitroot/mvccc/zanmei/{YYYY-MM-DD}.pptx"
       open theFile
       delay 3
       set theDoc to front document
       set outputPath to POSIX file "/Users/dfu/gitroot/mvccc/zanmei/{YYYY-MM-DD}.key"
       save theDoc in outputPath
       close theDoc
   end tell
   '
   ```

7. **Report** the generated files and any notes (e.g., specific verse selections for response hymns).
