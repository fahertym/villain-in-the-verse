#!/usr/bin/env python3
"""
Sync checker for The Villain in the Verse manuscript.
Verifies that the master file and split chapters are synchronized.
"""

import argparse
import hashlib
import re
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple


def get_file_hash(file_path: Path) -> str:
    """Get MD5 hash of file content."""
    if not file_path.exists():
        return ""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""


def extract_chapters_from_master(master_file: Path) -> Dict[str, str]:
    """Extract chapter content from master file."""
    if not master_file.exists():
        return {}
    
    try:
        with open(master_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return {}
    
    chapters = {}
    lines = content.splitlines(keepends=True)
    
    # Find chapter boundaries
    chapter_re = re.compile(r"^##\s+Chapter\s+(\d+)\s*:\s*(.+?)\s*$")
    intro_re = re.compile(r"^##\s+Introduction\s*:\s*(.+?)\s*$")
    
    current_chapter = None
    current_content = []
    
    for line in lines:
        # Check for new chapter
        chapter_match = chapter_re.match(line)
        intro_match = intro_re.match(line)
        
        if chapter_match or intro_match:
            # Save previous chapter if exists
            if current_chapter:
                chapters[current_chapter] = "".join(current_content).rstrip() + "\n"
            
            # Start new chapter
            if chapter_match:
                chap_num = int(chapter_match.group(1))
                title = chapter_match.group(2)
                current_chapter = f"{chap_num:02d}-{slugify(title)}"
            elif intro_match:
                current_chapter = "introduction"
            
            current_content = [line]
        else:
            # Add to current chapter
            if current_chapter:
                current_content.append(line)
    
    # Don't forget the last chapter
    if current_chapter and current_content:
        chapters[current_chapter] = "".join(current_content).rstrip() + "\n"
    
    return chapters


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = re.sub(r"[\u2018\u2019\u201C\u201D]", "'", text)  # normalize curly quotes
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text.strip().lower())
    text = re.sub(r"-+", "-", text)
    return text or "untitled"


def find_chapter_files(manuscript_dir: Path) -> Dict[str, Path]:
    """Find all chapter files in manuscript directory."""
    chapter_files = {}
    
    # Introduction
    intro_file = manuscript_dir / "frontmatter" / "introduction.md"
    if intro_file.exists():
        chapter_files["introduction"] = intro_file
    
    # Chapter files in all parts
    for part_dir in manuscript_dir.glob("part*_*"):
        if part_dir.is_dir():
            for chapter_file in part_dir.glob("*.md"):
                # Extract chapter identifier from filename
                name = chapter_file.stem
                if re.match(r"^\d+-", name):  # Numbered chapters
                    chapter_files[name] = chapter_file
    
    return chapter_files


def compare_content(master_content: str, file_content: str) -> Tuple[bool, str]:
    """Compare content between master and individual file."""
    # Normalize whitespace for comparison
    master_normalized = re.sub(r'\s+', ' ', master_content.strip())
    file_normalized = re.sub(r'\s+', ' ', file_content.strip())
    
    if master_normalized == file_normalized:
        return True, "Content matches"
    
    # Calculate similarity
    common_lines = 0
    master_lines = set(master_content.splitlines())
    file_lines = set(file_content.splitlines())
    
    if master_lines and file_lines:
        common_lines = len(master_lines & file_lines)
        total_lines = len(master_lines | file_lines)
        similarity = (common_lines / total_lines) * 100 if total_lines > 0 else 0
        
        return False, f"Content differs (similarity: {similarity:.1f}%)"
    
    return False, "Content differs significantly"


def check_sync_status(master_file: Path, manuscript_dir: Path, verbose: bool = False) -> Dict:
    """Check synchronization status between master and split files."""
    results = {
        "status": "success",
        "master_exists": master_file.exists(),
        "chapters_found": 0,
        "chapters_synced": 0,
        "issues": [],
        "details": []
    }
    
    if not master_file.exists():
        results["status"] = "error"
        results["issues"].append(f"Master file not found: {master_file}")
        return results
    
    if not manuscript_dir.exists():
        results["status"] = "error"
        results["issues"].append(f"Manuscript directory not found: {manuscript_dir}")
        return results
    
    # Extract chapters from master
    print("📖 Extracting chapters from master file...")
    master_chapters = extract_chapters_from_master(master_file)
    
    # Find individual chapter files
    print("📁 Finding individual chapter files...")
    chapter_files = find_chapter_files(manuscript_dir)
    
    results["chapters_found"] = len(chapter_files)
    
    # Compare each chapter
    for chapter_id, chapter_file in chapter_files.items():
        detail = {
            "chapter": chapter_id,
            "file": str(chapter_file.relative_to(manuscript_dir.parent)),
            "status": "unknown"
        }
        
        if chapter_id not in master_chapters:
            detail["status"] = "missing_from_master"
            detail["message"] = "Chapter exists in files but not in master"
            results["issues"].append(f"Chapter {chapter_id} missing from master file")
        else:
            try:
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                master_content = master_chapters[chapter_id]
                is_synced, message = compare_content(master_content, file_content)
                
                detail["status"] = "synced" if is_synced else "diverged"
                detail["message"] = message
                
                if is_synced:
                    results["chapters_synced"] += 1
                else:
                    results["issues"].append(f"Chapter {chapter_id}: {message}")
                
                if verbose:
                    detail["file_size"] = len(file_content)
                    detail["master_size"] = len(master_content)
                    
            except Exception as e:
                detail["status"] = "error"
                detail["message"] = f"Error reading file: {e}"
                results["issues"].append(f"Chapter {chapter_id}: Error reading file - {e}")
        
        results["details"].append(detail)
    
    # Check for chapters in master but not in files
    for chapter_id in master_chapters:
        if chapter_id not in chapter_files:
            results["issues"].append(f"Chapter {chapter_id} exists in master but no corresponding file found")
            results["details"].append({
                "chapter": chapter_id,
                "file": "missing",
                "status": "missing_file",
                "message": "Chapter exists in master but no file found"
            })
    
    # Overall status
    if results["issues"]:
        results["status"] = "diverged" if results["chapters_synced"] > 0 else "error"
    
    return results


def print_sync_report(results: Dict, verbose: bool = False):
    """Print a human-readable sync report."""
    status_icons = {
        "success": "✅",
        "diverged": "⚠️",
        "error": "❌"
    }
    
    icon = status_icons.get(results["status"], "❓")
    print(f"\n{icon} SYNC STATUS: {results['status'].upper()}")
    print("=" * 50)
    
    if results["master_exists"]:
        print(f"📖 Master file: Found")
    else:
        print(f"❌ Master file: Not found")
        return
    
    print(f"📁 Chapters found: {results['chapters_found']}")
    print(f"✅ Chapters synced: {results['chapters_synced']}")
    
    if results["issues"]:
        print(f"\n⚠️  ISSUES FOUND ({len(results['issues'])}):")
        for issue in results["issues"]:
            print(f"   • {issue}")
    
    if verbose and results["details"]:
        print(f"\n📋 DETAILED BREAKDOWN:")
        for detail in results["details"]:
            status_icon = {
                "synced": "✅",
                "diverged": "⚠️",
                "missing_from_master": "❓",
                "missing_file": "❓",
                "error": "❌"
            }.get(detail["status"], "❓")
            
            print(f"   {status_icon} {detail['chapter']}")
            print(f"      File: {detail['file']}")
            print(f"      Status: {detail['message']}")
            
            if "file_size" in detail:
                print(f"      Size: File={detail['file_size']}, Master={detail['master_size']}")
            print()


def main():
    parser = argparse.ArgumentParser(description="Check sync status between master file and split chapters")
    parser.add_argument("--master", default="../villain-verse-complete.md", 
                       help="Path to master file (default: ../villain-verse-complete.md)")
    parser.add_argument("--manuscript", default="../manuscript",
                       help="Path to manuscript directory (default: ../manuscript)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed information")
    parser.add_argument("--json", action="store_true",
                       help="Output JSON format")
    parser.add_argument("--fix", action="store_true",
                       help="Attempt to fix sync issues by re-splitting master file")
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    master_file = (script_dir / args.master).resolve()
    manuscript_dir = (script_dir / args.manuscript).resolve()
    
    print("🔍 Checking sync status between master file and individual chapters...")
    
    results = check_sync_status(master_file, manuscript_dir, args.verbose)
    
    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print_sync_report(results, args.verbose)
        
        if args.fix and results["status"] != "success":
            print(f"\n🔧 Attempting to fix sync issues...")
            print(f"Re-splitting master file...")
            
            import subprocess
            try:
                subprocess.run([
                    "python3", str(script_dir / "split_from_complete.py"),
                    str(master_file), "--dest", str(manuscript_dir)
                ], check=True)
                print("✅ Re-split completed successfully")
                
                # Check again
                print("\n🔍 Verifying fix...")
                new_results = check_sync_status(master_file, manuscript_dir)
                print_sync_report(new_results)
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Fix failed: {e}")
                return 1
    
    # Exit with error code if not synced
    return 0 if results["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
