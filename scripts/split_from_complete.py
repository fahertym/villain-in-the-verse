#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import sys
import time
from pathlib import Path


CHAPTER_RE = re.compile(r"^##\s+Chapter\s+(\d+)\s*:\s*(.+?)\s*$")


def slugify(text: str) -> str:
    text = re.sub(r"[\u2018\u2019\u201C\u201D]", "'", text)  # normalize curly quotes
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text.strip().lower())
    text = re.sub(r"-+", "-", text)
    return text or "untitled"


def backup_directory(dir_path: Path) -> Path:
    if not dir_path.exists():
        return None
    ts = time.strftime("%Y%m%d-%H%M%S")
    backup = dir_path.parent / f"{dir_path.name}__backup__{ts}"
    backup.mkdir(parents=True, exist_ok=True)
    for item in dir_path.iterdir():
        if item.is_file():
            shutil.copy2(item, backup / item.name)
    return backup


def split_chapters(src_path: Path, dest_dir: Path) -> int:
    with src_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find chapter headings
    chapter_indices = []  # list of (line_index, chapter_num, title)
    for idx, line in enumerate(lines):
        m = CHAPTER_RE.match(line)
        if m:
            chapter_indices.append((idx, int(m.group(1)), m.group(2)))

    if not chapter_indices:
        raise SystemExit("No chapter headings found with pattern '## Chapter N: Title'.")

    # Ensure destination exists and back it up
    dest_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_directory(dest_dir)

    # Clear existing numbered chapter files to avoid stale content (keep backups we just created)
    for fpath in dest_dir.glob("*.md"):
        fpath.unlink()

    # Write each chapter
    written = 0
    for i, (start_idx, chap_num, title) in enumerate(chapter_indices):
        end_idx = chapter_indices[i + 1][0] if i + 1 < len(chapter_indices) else len(lines)
        segment = "".join(lines[start_idx:end_idx]).rstrip() + "\n"
        filename = f"{chap_num:02d}-{slugify(title)}.md"
        out_path = dest_dir / filename
        with out_path.open("w", encoding="utf-8") as out:
            out.write(segment)
        written += 1

    # Report
    if backup:
        print(f"Backed up previous files to: {backup}")
    print(f"Wrote {written} chapter files to {dest_dir}")
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description="Split a combined manuscript into per-chapter files.")
    parser.add_argument("src", nargs="?", default="villain-verse-complete.md", help="Path to combined manuscript (default: villain-verse-complete.md)")
    parser.add_argument("--dest", default="manuscript/part1_case_files", help="Destination directory for chapter files")
    args = parser.parse_args(argv)

    src_path = Path(args.src).resolve()
    dest_dir = Path(args.dest).resolve()

    if not src_path.exists():
        print(f"Source file not found: {src_path}", file=sys.stderr)
        return 1

    split_chapters(src_path, dest_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


