#!/usr/bin/env python3
"""
Chapter Manager for The Villain in the Verse manuscript.
Handles creating, renaming, moving, and managing chapters.
"""

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Part configuration
PARTS_CONFIG = {
    "part1_case_files": {
        "name": "Part I — Case Files",
        "range": (1, 28),
        "description": "Biblical stories analyzed as crimes"
    },
    "part2_patterns": {
        "name": "Part II — Pattern Recognition", 
        "range": (29, 32),
        "description": "Behavioral patterns and psychological analysis"
    },
    "part3_fallout": {
        "name": "Part III — Fallout",
        "range": (33, 40),
        "description": "Real-world consequences and impacts"
    },
    "part4_apologetics": {
        "name": "Part IV — Apologetics Field Guide",
        "range": (41, 50),
        "description": "Common defenses and counter-arguments"
    },
    "part5_exit_routes": {
        "name": "Part V — Exit Routes",
        "range": (51, 60),
        "description": "Moving beyond harmful beliefs"
    }
}


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = re.sub(r"[\u2018\u2019\u201C\u201D]", "'", text)  # normalize curly quotes
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text.strip().lower())
    text = re.sub(r"-+", "-", text)
    return text or "untitled"


def load_chapter_template() -> str:
    """Load the chapter template."""
    script_dir = Path(__file__).parent
    template_path = script_dir.parent / "manuscript" / "CHAPTER_TEMPLATE.md"
    
    if template_path.exists():
        return template_path.read_text(encoding='utf-8')
    
    # Fallback template if file doesn't exist
    return """# <Chapter Title>

## The Setup

## The Crime

## The Cover-Up

## If a Human Did This

## Apology Box

*Receipts:* <verses>

**One-liner:** <tweet-length punchline>
"""


def get_next_chapter_number(part_dir: str, manuscript_dir: Path) -> int:
    """Get the next available chapter number for a part."""
    if part_dir not in PARTS_CONFIG:
        raise ValueError(f"Unknown part: {part_dir}")
    
    part_path = manuscript_dir / part_dir
    if not part_path.exists():
        part_path.mkdir(parents=True)
    
    # Find existing chapter numbers
    existing_numbers = set()
    for file_path in part_path.glob("*.md"):
        match = re.match(r"^(\d+)-", file_path.name)
        if match:
            existing_numbers.add(int(match.group(1)))
    
    # Find next number in range
    start, end = PARTS_CONFIG[part_dir]["range"]
    for num in range(start, end + 1):
        if num not in existing_numbers:
            return num
    
    raise ValueError(f"No available chapter numbers in {part_dir} (range {start}-{end})")


def get_chapter_info(file_path: Path) -> Dict:
    """Extract chapter information from a file."""
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return {"error": f"Could not read file: {e}"}
    
    # Extract title
    title_match = re.search(r'^#+\s*(.+?)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else file_path.stem
    
    # Extract chapter number from filename
    match = re.match(r"^(\d+)-", file_path.name)
    chapter_num = int(match.group(1)) if match else None
    
    # Count words (basic count)
    words = len(content.split())
    
    # Check completeness (rough heuristic)
    has_setup = "## The Setup" in content
    has_crime = "## The Crime" in content  
    has_coverup = "## The Cover-Up" in content
    has_human = "## If a Human Did This" in content
    has_apology = "## Apology Box" in content
    has_receipts = "*Receipts:*" in content and not "<verses>" in content
    has_oneliner = "**One-liner:**" in content and not "<tweet-length punchline>" in content
    
    sections_complete = sum([has_setup, has_crime, has_coverup, has_human, has_apology])
    
    # Estimate completion percentage
    completion = 0
    if words > 100:  # Has some content
        completion += 20
    if sections_complete >= 3:  # Most sections present
        completion += 30
    if has_receipts:  # Has biblical references
        completion += 25
    if has_oneliner:  # Has conclusion
        completion += 25
    
    completion = min(100, completion)
    
    return {
        "file": file_path,
        "title": title,
        "chapter_num": chapter_num,
        "words": words,
        "completion": completion,
        "sections": {
            "setup": has_setup,
            "crime": has_crime, 
            "coverup": has_coverup,
            "human": has_human,
            "apology": has_apology,
            "receipts": has_receipts,
            "oneliner": has_oneliner
        }
    }


def list_chapters(manuscript_dir: Path, part_filter: str = None) -> Dict[str, List[Dict]]:
    """List all chapters organized by part."""
    chapters_by_part = {}
    
    for part_dir, config in PARTS_CONFIG.items():
        if part_filter and part_filter != part_dir:
            continue
            
        part_path = manuscript_dir / part_dir
        chapters = []
        
        if part_path.exists():
            for file_path in sorted(part_path.glob("*.md")):
                # Skip overview files
                if "overview" in file_path.name.lower():
                    continue
                    
                chapter_info = get_chapter_info(file_path)
                if "error" not in chapter_info:
                    chapters.append(chapter_info)
        
        chapters.sort(key=lambda x: x["chapter_num"] or 0)
        chapters_by_part[part_dir] = chapters
    
    return chapters_by_part


def create_chapter(manuscript_dir: Path, title: str, part: str = None) -> Path:
    """Create a new chapter from template."""
    if not title:
        title = input("Chapter title: ").strip()
        if not title:
            raise ValueError("Chapter title is required")
    
    # Determine part
    if not part:
        print("\nAvailable parts:")
        for part_dir, config in PARTS_CONFIG.items():
            start, end = config["range"]
            print(f"  {part_dir}: {config['name']} (chapters {start}-{end})")
            print(f"    {config['description']}")
        
        part = input("\nPart (e.g., part1_case_files): ").strip()
        if part not in PARTS_CONFIG:
            raise ValueError(f"Invalid part: {part}")
    
    # Get next chapter number
    chapter_num = get_next_chapter_number(part, manuscript_dir)
    
    # Create filename
    slug = slugify(title)
    filename = f"{chapter_num:02d}-{slug}.md"
    
    # Create file path
    part_path = manuscript_dir / part
    part_path.mkdir(parents=True, exist_ok=True)
    file_path = part_path / filename
    
    if file_path.exists():
        raise ValueError(f"Chapter file already exists: {file_path}")
    
    # Create content from template
    template = load_chapter_template()
    content = template.replace("<Chapter Title>", title)
    
    # Write file
    file_path.write_text(content, encoding='utf-8')
    
    print(f"✅ Created chapter {chapter_num}: {title}")
    print(f"📁 File: {file_path.relative_to(manuscript_dir.parent)}")
    
    return file_path


def rename_chapter(manuscript_dir: Path, old_identifier: str, new_title: str) -> Path:
    """Rename a chapter (changes title and filename)."""
    # Find the chapter file
    chapter_file = find_chapter_file(manuscript_dir, old_identifier)
    if not chapter_file:
        raise ValueError(f"Chapter not found: {old_identifier}")
    
    # Extract chapter number
    match = re.match(r"^(\d+)-", chapter_file.name)
    if not match:
        raise ValueError(f"Cannot extract chapter number from: {chapter_file.name}")
    
    chapter_num = int(match.group(1))
    
    # Create new filename
    slug = slugify(new_title)
    new_filename = f"{chapter_num:02d}-{slug}.md"
    new_file_path = chapter_file.parent / new_filename
    
    # Update content
    content = chapter_file.read_text(encoding='utf-8')
    
    # Update title in content
    content = re.sub(
        r'^#+\s*(.+?)$', 
        f"# {new_title}", 
        content, 
        count=1, 
        flags=re.MULTILINE
    )
    
    # Write to new file
    new_file_path.write_text(content, encoding='utf-8')
    
    # Remove old file if different
    if new_file_path != chapter_file:
        chapter_file.unlink()
    
    print(f"✅ Renamed chapter {chapter_num} to: {new_title}")
    print(f"📁 File: {new_file_path.relative_to(manuscript_dir.parent)}")
    
    return new_file_path


def move_chapter(manuscript_dir: Path, chapter_identifier: str, target_part: str) -> Path:
    """Move a chapter to a different part."""
    # Find the chapter file
    chapter_file = find_chapter_file(manuscript_dir, chapter_identifier)
    if not chapter_file:
        raise ValueError(f"Chapter not found: {chapter_identifier}")
    
    if target_part not in PARTS_CONFIG:
        raise ValueError(f"Invalid target part: {target_part}")
    
    # Get new chapter number
    new_chapter_num = get_next_chapter_number(target_part, manuscript_dir)
    
    # Extract title from content
    content = chapter_file.read_text(encoding='utf-8')
    title_match = re.search(r'^#+\s*(.+?)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "Untitled"
    
    # Create new file path
    slug = slugify(title)
    new_filename = f"{new_chapter_num:02d}-{slug}.md"
    target_dir = manuscript_dir / target_part
    target_dir.mkdir(parents=True, exist_ok=True)
    new_file_path = target_dir / new_filename
    
    # Update chapter number in content
    content = re.sub(
        r'^(#+\s*)(.+?)$',
        f"\\1{title}",
        content,
        count=1,
        flags=re.MULTILINE
    )
    
    # Write to new location
    new_file_path.write_text(content, encoding='utf-8')
    
    # Remove old file
    chapter_file.unlink()
    
    print(f"✅ Moved chapter to {target_part} as chapter {new_chapter_num}")
    print(f"📁 New file: {new_file_path.relative_to(manuscript_dir.parent)}")
    
    return new_file_path


def find_chapter_file(manuscript_dir: Path, identifier: str) -> Optional[Path]:
    """Find a chapter file by number, title, or filename."""
    # Try to parse as chapter number
    try:
        chapter_num = int(identifier)
        for part_dir in PARTS_CONFIG:
            part_path = manuscript_dir / part_dir
            if part_path.exists():
                for file_path in part_path.glob(f"{chapter_num:02d}-*.md"):
                    return file_path
    except ValueError:
        pass
    
    # Try to find by title or filename
    identifier_lower = identifier.lower()
    for part_dir in PARTS_CONFIG:
        part_path = manuscript_dir / part_dir
        if part_path.exists():
            for file_path in part_path.glob("*.md"):
                # Check filename
                if identifier_lower in file_path.stem.lower():
                    return file_path
                
                # Check title in content
                try:
                    content = file_path.read_text(encoding='utf-8')
                    title_match = re.search(r'^#+\s*(.+?)$', content, re.MULTILINE)
                    if title_match and identifier_lower in title_match.group(1).lower():
                        return file_path
                except Exception:
                    continue
    
    return None


def show_status(manuscript_dir: Path, summary: bool = False, part_filter: str = None):
    """Show chapter status overview."""
    chapters_by_part = list_chapters(manuscript_dir, part_filter)
    
    if summary:
        # Summary view
        total_chapters = 0
        total_words = 0
        total_complete = 0
        
        for part_dir, chapters in chapters_by_part.items():
            if not chapters:
                continue
                
            total_chapters += len(chapters)
            total_words += sum(c["words"] for c in chapters)
            total_complete += sum(1 for c in chapters if c["completion"] >= 80)
        
        completion_rate = (total_complete / total_chapters * 100) if total_chapters > 0 else 0
        
        print(f"📊 MANUSCRIPT SUMMARY")
        print("=" * 30)
        print(f"📚 Total chapters: {total_chapters}")
        print(f"📝 Total words: {total_words:,}")
        print(f"✅ Complete (≥80%): {total_complete}")
        print(f"📈 Completion rate: {completion_rate:.1f}%")
        
        return
    
    # Detailed view
    print("📋 CHAPTER STATUS OVERVIEW")
    print("=" * 80)
    
    for part_dir, chapters in chapters_by_part.items():
        config = PARTS_CONFIG[part_dir]
        print(f"\n{config['name']}")
        print("-" * len(config['name']))
        
        if not chapters:
            print("   (No chapters yet)")
            continue
        
        for chapter in chapters:
            completion = chapter["completion"]
            status_icon = "✅" if completion >= 80 else "🚧" if completion >= 40 else "📝"
            
            title = chapter["title"][:50] + "..." if len(chapter["title"]) > 50 else chapter["title"]
            
            chapter_num_str = f"{chapter['chapter_num']:2d}" if chapter['chapter_num'] else "??"
            print(f"   {status_icon} Ch.{chapter_num_str}: {title}")
            print(f"       📊 {completion:3d}% • 📝 {chapter['words']:,} words")
            
            # Show missing sections
            missing = []
            sections = chapter["sections"]
            if not sections["receipts"]:
                missing.append("receipts")
            if not sections["oneliner"]:
                missing.append("one-liner")
            if not all([sections["setup"], sections["crime"], sections["coverup"]]):
                missing.append("core sections")
            
            if missing:
                print(f"       ⚠️  Missing: {', '.join(missing)}")


def main():
    parser = argparse.ArgumentParser(description="Manage chapters for The Villain in the Verse")
    parser.add_argument("--manuscript", default="../manuscript",
                       help="Path to manuscript directory (default: ../manuscript)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new chapter")
    create_parser.add_argument("--title", help="Chapter title")
    create_parser.add_argument("--part", choices=list(PARTS_CONFIG.keys()),
                              help="Part to create chapter in")
    
    # Rename command  
    rename_parser = subparsers.add_parser("rename", help="Rename chapter")
    rename_parser.add_argument("identifier", help="Chapter number, title, or filename")
    rename_parser.add_argument("--title", help="New title")
    
    # Move command
    move_parser = subparsers.add_parser("move", help="Move chapter to different part")
    move_parser.add_argument("identifier", help="Chapter number, title, or filename")
    move_parser.add_argument("--part", choices=list(PARTS_CONFIG.keys()),
                            help="Target part")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show chapter status")
    status_parser.add_argument("--summary", action="store_true",
                              help="Show summary view only")
    status_parser.add_argument("--part", choices=list(PARTS_CONFIG.keys()),
                              help="Filter by part")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    script_dir = Path(__file__).parent
    manuscript_dir = (script_dir / args.manuscript).resolve()
    
    try:
        if args.command == "create":
            create_chapter(manuscript_dir, args.title, args.part)
            
        elif args.command == "rename":
            new_title = args.title
            if not new_title:
                new_title = input("New title: ").strip()
                if not new_title:
                    raise ValueError("New title is required")
            rename_chapter(manuscript_dir, args.identifier, new_title)
            
        elif args.command == "move":
            target_part = args.part
            if not target_part:
                print("\nAvailable parts:")
                for part_dir, config in PARTS_CONFIG.items():
                    print(f"  {part_dir}: {config['name']}")
                target_part = input("\nTarget part: ").strip()
                if target_part not in PARTS_CONFIG:
                    raise ValueError(f"Invalid part: {target_part}")
            move_chapter(manuscript_dir, args.identifier, target_part)
            
        elif args.command == "status":
            show_status(manuscript_dir, args.summary, args.part)
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
