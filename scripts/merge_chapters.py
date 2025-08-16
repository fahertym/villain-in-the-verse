#!/usr/bin/env python3
"""
Merge individual chapter files back into a master manuscript file.
Reverse operation of split_from_complete.py
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def load_frontmatter(manuscript_dir: Path) -> str:
    """Load frontmatter content."""
    frontmatter = []
    
    # Title page
    title_file = manuscript_dir / "frontmatter" / "titlepage.md"
    if title_file.exists():
        frontmatter.append(title_file.read_text(encoding='utf-8').rstrip())
    
    # Introduction
    intro_file = manuscript_dir / "frontmatter" / "introduction.md"
    if intro_file.exists():
        content = intro_file.read_text(encoding='utf-8').rstrip()
        # Ensure introduction has proper heading
        if not content.startswith("## Introduction"):
            content = "## Introduction: Setting the Scene\n\n" + content
        frontmatter.append(content)
    
    return "\n\n".join(frontmatter)


def extract_chapter_info(file_path: Path) -> Tuple[int, str, str]:
    """Extract chapter number, title, and content from a chapter file."""
    # Extract chapter number from filename
    match = re.match(r"^(\d+)-(.+)\.md$", file_path.name)
    if not match:
        raise ValueError(f"Cannot parse chapter number from filename: {file_path.name}")
    
    chapter_num = int(match.group(1))
    
    # Read content
    content = file_path.read_text(encoding='utf-8').rstrip()
    
    # Extract title from first heading
    title_match = re.search(r'^#+\s*(.+?)$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        # Remove the heading from content since we'll add our own
        content = re.sub(r'^#+\s*.+?$', '', content, count=1, flags=re.MULTILINE).lstrip()
    else:
        # Use filename as fallback
        title = match.group(2).replace('-', ' ').title()
    
    return chapter_num, title, content


def load_chapters_from_part(part_dir: Path) -> List[Tuple[int, str, str]]:
    """Load all chapters from a part directory."""
    chapters = []
    
    if not part_dir.exists():
        return chapters
    
    for file_path in part_dir.glob("*.md"):
        # Skip overview files
        if "overview" in file_path.name.lower():
            continue
            
        try:
            chapter_info = extract_chapter_info(file_path)
            chapters.append(chapter_info)
        except Exception as e:
            print(f"Warning: Skipping {file_path}: {e}", file=sys.stderr)
    
    # Sort by chapter number
    chapters.sort(key=lambda x: x[0])
    return chapters


def create_part_sections(manuscript_dir: Path) -> List[str]:
    """Create content for all parts."""
    sections = []
    
    # Part definitions
    parts = [
        ("part1_case_files", "Part I: Case Files"),
        ("part2_patterns", "Part II: Pattern Recognition"), 
        ("part3_fallout", "Part III: Fallout"),
        ("part4_apologetics", "Part IV: Apologetics Field Guide"),
        ("part5_exit_routes", "Part V: Exit Routes")
    ]
    
    for part_dir_name, part_title in parts:
        part_dir = manuscript_dir / part_dir_name
        chapters = load_chapters_from_part(part_dir)
        
        if not chapters:
            continue
            
        # Add part header
        sections.append(f"## {part_title}")
        sections.append("")  # Empty line after part header
        
        # Add chapters
        for chapter_num, title, content in chapters:
            # Add chapter header
            sections.append(f"## Chapter {chapter_num}: {title}")
            sections.append("")  # Empty line after chapter header
            
            # Add chapter content
            sections.append(content)
            sections.append("")  # Empty line after chapter
    
    return sections


def load_backmatter(manuscript_dir: Path) -> str:
    """Load backmatter content."""
    backmatter = []
    
    # Acknowledgments
    ack_file = manuscript_dir / "frontmatter" / "acknowledgments.md"
    if ack_file.exists():
        content = ack_file.read_text(encoding='utf-8').rstrip()
        # Ensure proper heading
        if not content.startswith("#"):
            content = "## Acknowledgments\n\n" + content
        backmatter.append(content)
    
    return "\n\n".join(backmatter)


def merge_manuscript(manuscript_dir: Path, output_file: Path):
    """Merge individual chapter files into a master manuscript."""
    sections = []
    
    # Load frontmatter
    print("📖 Loading frontmatter...")
    frontmatter = load_frontmatter(manuscript_dir)
    if frontmatter:
        sections.append(frontmatter)
    
    # Load main content
    print("📚 Loading chapters...")
    main_sections = create_part_sections(manuscript_dir)
    sections.extend(main_sections)
    
    # Load backmatter  
    print("📋 Loading backmatter...")
    backmatter = load_backmatter(manuscript_dir)
    if backmatter:
        sections.append(backmatter)
    
    # Combine all sections
    full_content = "\n\n".join(sections)
    
    # Normalize line endings
    full_content = full_content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Clean up excessive whitespace
    full_content = re.sub(r'\n{3,}', '\n\n', full_content)
    
    # Ensure file ends with single newline
    full_content = full_content.rstrip() + '\n'
    
    # Write to output file
    output_file.write_text(full_content, encoding='utf-8')
    
    # Report statistics
    chapter_count = len(re.findall(r'^## Chapter \d+:', full_content, re.MULTILINE))
    word_count = len(full_content.split())
    
    print(f"✅ Merged {chapter_count} chapters into master file")
    print(f"📊 Total words: {word_count:,}")
    print(f"📁 Output: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Merge individual chapter files into master manuscript")
    parser.add_argument("--manuscript", default="../manuscript",
                       help="Path to manuscript directory (default: ../manuscript)")
    parser.add_argument("--output", default="../villain-verse-complete.md",
                       help="Output file path (default: ../villain-verse-complete.md)")
    parser.add_argument("--backup", action="store_true",
                       help="Create backup of existing output file")
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    manuscript_dir = (script_dir / args.manuscript).resolve()
    output_file = (script_dir / args.output).resolve()
    
    if not manuscript_dir.exists():
        print(f"❌ Manuscript directory not found: {manuscript_dir}", file=sys.stderr)
        return 1
    
    # Create backup if requested and file exists
    if args.backup and output_file.exists():
        backup_file = output_file.with_suffix(f".backup-{output_file.stat().st_mtime:.0f}.md")
        backup_file.write_bytes(output_file.read_bytes())
        print(f"📋 Created backup: {backup_file}")
    
    try:
        merge_manuscript(manuscript_dir, output_file)
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
