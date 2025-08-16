#!/usr/bin/env python3
"""
Word count and progress tracking script for The Villain in the Verse manuscript.
Provides detailed statistics and progress visualization.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

def count_words_in_text(text: str) -> Dict[str, int]:
    """Count various text statistics."""
    # Remove code blocks and inline code
    text_no_code = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text_no_code = re.sub(r'`[^`]+`', '', text_no_code)
    
    # Remove markdown formatting
    text_clean = re.sub(r'[#*_`\[\](){}]', '', text_no_code)
    text_clean = re.sub(r'^\s*[-+*]\s+', '', text_clean, flags=re.MULTILINE)  # List items
    text_clean = re.sub(r'^\s*\d+\.\s+', '', text_clean, flags=re.MULTILINE)  # Numbered lists
    text_clean = re.sub(r'---+', '', text_clean)  # Horizontal rules
    
    # Count statistics
    words = len(text_clean.split())
    chars = len(text_clean)
    chars_no_spaces = len(text_clean.replace(' ', ''))
    
    # Count sentences (rough estimate)
    sentences = len(re.findall(r'[.!?]+', text_clean))
    
    # Count paragraphs (non-empty lines that aren't headers)
    lines = text.split('\n')
    paragraphs = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
    
    return {
        'words': words,
        'characters': chars,
        'characters_no_spaces': chars_no_spaces,
        'sentences': sentences,
        'paragraphs': paragraphs
    }

def analyze_file(file_path: Path) -> Dict:
    """Analyze a single markdown file."""
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return {"error": f"Could not read file as UTF-8: {file_path}"}
    
    # Extract title from first heading
    title_match = re.search(r'^#+\s*(.+?)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else file_path.stem
    
    stats = count_words_in_text(content)
    stats.update({
        'file': str(file_path.relative_to(Path.cwd())),
        'title': title,
        'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
    })
    
    return stats

def calculate_reading_time(word_count: int, wpm: int = 200) -> str:
    """Calculate estimated reading time."""
    minutes = word_count / wpm
    if minutes < 1:
        return "< 1 min"
    elif minutes < 60:
        return f"{int(minutes)} min"
    else:
        hours = minutes / 60
        return f"{hours:.1f} hours"

def print_file_stats(stats: Dict, show_details: bool = False):
    """Print statistics for a single file."""
    if "error" in stats:
        print(f"❌ {stats['error']}")
        return
    
    title = stats['title']
    words = stats['words']
    reading_time = calculate_reading_time(words)
    
    print(f"📄 {title}")
    print(f"   📊 {words:,} words • {stats['characters']:,} chars • {stats['sentences']} sentences")
    print(f"   ⏱️  ~{reading_time} read time")
    
    if show_details:
        print(f"   📁 {stats['file']}")
        print(f"   📅 Modified: {stats['last_modified'][:10]}")
        print(f"   📝 {stats['paragraphs']} paragraphs")

def print_summary_stats(all_stats: List[Dict], target_words: int = None):
    """Print overall summary statistics."""
    valid_stats = [s for s in all_stats if "error" not in s]
    
    if not valid_stats:
        print("❌ No valid files found")
        return
    
    total_words = sum(s['words'] for s in valid_stats)
    total_chars = sum(s['characters'] for s in valid_stats)
    total_sentences = sum(s['sentences'] for s in valid_stats)
    total_paragraphs = sum(s['paragraphs'] for s in valid_stats)
    
    avg_words = total_words / len(valid_stats)
    reading_time = calculate_reading_time(total_words)
    
    print(f"\n📊 SUMMARY STATISTICS")
    print("=" * 50)
    print(f"📚 Files analyzed: {len(valid_stats)}")
    print(f"📝 Total words: {total_words:,}")
    print(f"📄 Total characters: {total_chars:,}")
    print(f"🔤 Total sentences: {total_sentences:,}")
    print(f"📋 Total paragraphs: {total_paragraphs:,}")
    print(f"📈 Average words per file: {avg_words:.0f}")
    print(f"⏱️  Total reading time: ~{reading_time}")
    
    if target_words:
        progress = (total_words / target_words) * 100
        remaining = max(0, target_words - total_words)
        print(f"\n🎯 PROGRESS TO TARGET ({target_words:,} words)")
        print(f"✅ Progress: {progress:.1f}% complete")
        if remaining > 0:
            print(f"📝 Remaining: {remaining:,} words")
            print(f"📖 Remaining chapters: ~{remaining // avg_words:.0f} (at current average)")
        else:
            print("🎉 Target achieved!")
    
    # Top 5 longest chapters
    sorted_stats = sorted(valid_stats, key=lambda x: x['words'], reverse=True)
    print(f"\n📏 TOP 5 LONGEST CHAPTERS")
    for i, stats in enumerate(sorted_stats[:5], 1):
        print(f"{i}. {stats['title']}: {stats['words']:,} words")

def create_progress_chart(all_stats: List[Dict], width: int = 50):
    """Create a simple ASCII progress chart."""
    valid_stats = [s for s in all_stats if "error" not in s]
    if not valid_stats:
        return
    
    print(f"\n📊 WORD COUNT DISTRIBUTION")
    print("=" * (width + 10))
    
    max_words = max(s['words'] for s in valid_stats)
    
    for stats in sorted(valid_stats, key=lambda x: x['words'], reverse=True)[:10]:
        title = stats['title'][:25] + "..." if len(stats['title']) > 25 else stats['title']
        words = stats['words']
        bar_length = int((words / max_words) * width)
        bar = "█" * bar_length + "░" * (width - bar_length)
        print(f"{title:<28} │{bar}│ {words:,}")

def save_progress_data(all_stats: List[Dict], output_file: Path):
    """Save progress data to JSON file for tracking over time."""
    valid_stats = [s for s in all_stats if "error" not in s]
    
    progress_data = {
        'timestamp': datetime.now().isoformat(),
        'total_words': sum(s['words'] for s in valid_stats),
        'file_count': len(valid_stats),
        'files': valid_stats
    }
    
    # Load existing data if available
    history = []
    if output_file.exists():
        try:
            with open(output_file, 'r') as f:
                history = json.load(f)
        except (json.JSONDecodeError, KeyError):
            history = []
    
    history.append(progress_data)
    
    # Keep only last 30 entries
    history = history[-30:]
    
    with open(output_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"💾 Progress data saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Analyze word count and progress for manuscript")
    parser.add_argument("files", nargs="*", help="Files to analyze (default: all .md files)")
    parser.add_argument("--target", "-t", type=int, help="Target word count for progress tracking")
    parser.add_argument("--details", "-d", action="store_true", help="Show detailed file information")
    parser.add_argument("--chart", "-c", action="store_true", help="Show word count distribution chart")
    parser.add_argument("--save", "-s", help="Save progress data to JSON file")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()
    
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        # Default to all markdown files in manuscript/
        manuscript_dir = Path(__file__).parent.parent / "manuscript"
        files = []
        
        # Add master file if it exists
        master_file = Path(__file__).parent.parent / "villain-verse-complete.md"
        if master_file.exists():
            files.append(master_file)
        else:
            # Otherwise add individual chapter files
            files.extend(list(manuscript_dir.rglob("*.md")))
            # Exclude backup directories
            files = [f for f in files if "__backup__" not in str(f)]
    
    all_stats = []
    
    for file_path in files:
        stats = analyze_file(file_path)
        all_stats.append(stats)
        
        if not args.json and args.details:
            print_file_stats(stats, show_details=True)
            print()
    
    if args.json:
        print(json.dumps(all_stats, indent=2))
    else:
        print_summary_stats(all_stats, args.target)
        
        if args.chart:
            create_progress_chart(all_stats)
        
        if args.save:
            save_progress_data(all_stats, Path(args.save))

if __name__ == "__main__":
    main()
