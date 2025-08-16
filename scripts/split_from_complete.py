#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import sys
import time
from pathlib import Path


CHAPTER_RE = re.compile(r"^##\s+Chapter\s+(\d+)\s*:\s*(.+?)\s*$")
INTRO_RE = re.compile(r"^##\s+Introduction\s*:\s*(.+?)\s*$")
PART_RE = re.compile(r"^##\s+Part\s+([IVX]+)\s*:\s*(.+?)\s*$")


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


def split_complete_manuscript(src_path: Path, manuscript_dir: Path) -> int:
    with src_path.open("r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.splitlines(keepends=True)
    
    # Find all sections
    sections = []
    for idx, line in enumerate(lines):
        # Introduction
        intro_match = INTRO_RE.match(line)
        if intro_match:
            sections.append((idx, 'intro', intro_match.group(1)))
            continue
            
        # Parts
        part_match = PART_RE.match(line)
        if part_match:
            sections.append((idx, 'part', part_match.group(1), part_match.group(2)))
            continue
            
        # Chapters
        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            sections.append((idx, 'chapter', int(chapter_match.group(1)), chapter_match.group(2)))
    
    if not sections:
        raise SystemExit("No sections found. Expected Introduction, Parts, and Chapters.")
    
    # Ensure manuscript directory exists
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup existing directories
    backup_dirs = []
    for subdir in ['frontmatter', 'part1_case_files', 'part2_patterns', 'part3_fallout', 'part4_apologetics', 'part5_exit_routes']:
        dir_path = manuscript_dir / subdir
        if dir_path.exists():
            backup = backup_directory(dir_path)
            if backup:
                backup_dirs.append(backup)
    
    # Create directory structure
    (manuscript_dir / 'frontmatter').mkdir(exist_ok=True)
    (manuscript_dir / 'part1_case_files').mkdir(exist_ok=True) 
    (manuscript_dir / 'part2_patterns').mkdir(exist_ok=True)
    (manuscript_dir / 'part3_fallout').mkdir(exist_ok=True)
    (manuscript_dir / 'part4_apologetics').mkdir(exist_ok=True)
    (manuscript_dir / 'part5_exit_routes').mkdir(exist_ok=True)
    
    # Clear existing chapter files (keep overview files)
    for subdir in ['part1_case_files', 'part2_patterns', 'part3_fallout']:
        subdir_path = manuscript_dir / subdir
        if subdir_path.exists():
            for f in subdir_path.glob('[0-9][0-9]-*.md'):
                f.unlink()
    
    written = 0
    
    # Process each section
    for i, section in enumerate(sections):
        start_idx = section[0]
        end_idx = sections[i + 1][0] if i + 1 < len(sections) else len(lines)
        segment = "".join(lines[start_idx:end_idx]).rstrip() + "\n"
        
        if section[1] == 'intro':
            # Write introduction
            out_path = manuscript_dir / 'frontmatter' / 'introduction.md'
            with out_path.open("w", encoding="utf-8") as f:
                f.write(segment)
            written += 1
            
        elif section[1] == 'chapter':
            chap_num = section[2]
            title = section[3]
            filename = f"{chap_num:02d}-{slugify(title)}.md"
            
            # Determine which part this chapter belongs to (matching TOC structure)
            if 1 <= chap_num <= 28:  # Part I: The Receipts (Biblical Case Files)
                out_path = manuscript_dir / 'part1_case_files' / filename
            elif 29 <= chap_num <= 38:  # Part II: Pattern Recognition (How the Villain Operates)
                out_path = manuscript_dir / 'part2_patterns' / filename
            elif 39 <= chap_num <= 42:  # Part III: Aftermath (Empire, Church, Power)
                out_path = manuscript_dir / 'part3_fallout' / filename
            elif 43 <= chap_num <= 50:  # Future expansion
                out_path = manuscript_dir / 'part4_apologetics' / filename
            else:  # Future expansion
                out_path = manuscript_dir / 'part5_exit_routes' / filename
                
            with out_path.open("w", encoding="utf-8") as f:
                f.write(segment)
            written += 1
    
    # Report
    if backup_dirs:
        print(f"Backed up previous files to: {', '.join(str(b) for b in backup_dirs)}")
    print(f"Split {written} sections from {src_path} into {manuscript_dir}")
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description="Split a combined manuscript into per-chapter files.")
    parser.add_argument("src", nargs="?", default="villain-verse-complete.md", help="Path to combined manuscript (default: villain-verse-complete.md)")
    parser.add_argument("--dest", default="manuscript", help="Destination directory for manuscript files")
    args = parser.parse_args(argv)

    src_path = Path(args.src).resolve()
    manuscript_dir = Path(args.dest).resolve()

    if not src_path.exists():
        print(f"Source file not found: {src_path}", file=sys.stderr)
        return 1

    split_complete_manuscript(src_path, manuscript_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


