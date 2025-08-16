#!/usr/bin/env python3
"""
Comprehensive linting script for The Villain in the Verse manuscript.
Checks markdown formatting, spell checking, and content quality.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Common typos and preferred spellings
SPELLING_CORRECTIONS = {
    "recieve": "receive",
    "occured": "occurred", 
    "seperate": "separate",
    "definately": "definitely",
    "alot": "a lot",
    "dont": "don't",
    "wont": "won't",
    "cant": "can't",
    "youre": "you're",
    "its": "it's",  # When possessive vs. "it is"
    "theres": "there's",
    "heres": "here's",
    "wheres": "where's"
}

# Style guide preferences
STYLE_CHECKS = {
    "biblical": "Biblical",  # Capitalize when referring to the Bible
    "christian": "Christian",  # Capitalize religion names
    "god": "God",  # Capitalize when referring to the deity
    "bible": "Bible",  # Capitalize book name
    # Common contractions for consistency
    "do not": "don't",
    "will not": "won't", 
    "cannot": "can't",
    "should not": "shouldn't",
    "would not": "wouldn't"
}

def run_markdownlint(file_path: Path) -> List[Dict]:
    """Run markdownlint on a file and return issues."""
    try:
        result = subprocess.run([
            "markdownlint", 
            "--json",
            "--config", str(Path(__file__).parent.parent / "build" / ".markdownlint.yaml"),
            str(file_path)
        ], capture_output=True, text=True, check=False)
        
        if result.stdout:
            return json.loads(result.stdout)
        return []
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        print(f"Warning: markdownlint not available or failed for {file_path}")
        return []

def check_spelling_and_style(content: str, file_path: Path) -> List[Tuple[int, str, str]]:
    """Check for common spelling errors and style issues."""
    issues = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Skip code blocks and inline code
        if line.strip().startswith('```') or '`' in line:
            continue
            
        # Check spelling
        for typo, correction in SPELLING_CORRECTIONS.items():
            if re.search(r'\b' + re.escape(typo) + r'\b', line, re.IGNORECASE):
                issues.append((line_num, f"Spelling: '{typo}' -> '{correction}'", line.strip()))
        
        # Check style
        for incorrect, correct in STYLE_CHECKS.items():
            if re.search(r'\b' + re.escape(incorrect) + r'\b', line):
                issues.append((line_num, f"Style: '{incorrect}' -> '{correct}'", line.strip()))
    
    return issues

def check_content_quality(content: str, file_path: Path) -> List[Tuple[int, str, str]]:
    """Check for content quality issues."""
    issues = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Check for very long sentences (potential readability issue)
        if len(line) > 200 and '. ' not in line[-50:]:  # Long line without recent period
            issues.append((line_num, "Long sentence: Consider breaking into shorter sentences", line[:50] + "..."))
        
        # Check for repeated words
        words = line.lower().split()
        for i in range(len(words) - 1):
            if words[i] == words[i + 1] and len(words[i]) > 3:
                issues.append((line_num, f"Repeated word: '{words[i]}'", line.strip()))
        
        # Check for inconsistent quotation marks
        if '"' in line and '"' in line and '"' in line:
            issues.append((line_num, "Mixed quotation mark styles", line.strip()))
    
    return issues

def lint_file(file_path: Path) -> Dict:
    """Lint a single markdown file."""
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return {"error": f"Could not read file as UTF-8: {file_path}"}
    
    results = {
        "file": str(file_path),
        "markdownlint": run_markdownlint(file_path),
        "spelling_style": check_spelling_and_style(content, file_path),
        "content_quality": check_content_quality(content, file_path)
    }
    
    return results

def print_results(results: Dict, verbose: bool = False):
    """Print linting results in a readable format."""
    file_path = results["file"]
    print(f"\n📄 {file_path}")
    print("=" * (len(file_path) + 3))
    
    total_issues = 0
    
    # Markdownlint issues
    if results["markdownlint"]:
        print(f"\n🔍 Markdown Linting ({len(results['markdownlint'])} issues):")
        for issue in results["markdownlint"]:
            print(f"  Line {issue.get('lineNumber', '?')}: {issue.get('ruleDescription', 'Unknown issue')}")
            if verbose and 'errorDetail' in issue:
                print(f"    Detail: {issue['errorDetail']}")
        total_issues += len(results["markdownlint"])
    
    # Spelling and style issues
    if results["spelling_style"]:
        print(f"\n📝 Spelling & Style ({len(results['spelling_style'])} issues):")
        for line_num, message, context in results["spelling_style"]:
            print(f"  Line {line_num}: {message}")
            if verbose:
                print(f"    Context: {context}")
        total_issues += len(results["spelling_style"])
    
    # Content quality issues
    if results["content_quality"]:
        print(f"\n✨ Content Quality ({len(results['content_quality'])} issues):")
        for line_num, message, context in results["content_quality"]:
            print(f"  Line {line_num}: {message}")
            if verbose:
                print(f"    Context: {context}")
        total_issues += len(results["content_quality"])
    
    if total_issues == 0:
        print("\n✅ No issues found!")
    else:
        print(f"\n📊 Total: {total_issues} issues")

def main():
    parser = argparse.ArgumentParser(description="Lint manuscript files for quality and consistency")
    parser.add_argument("files", nargs="*", help="Files to lint (default: all .md files)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()
    
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        # Default to all markdown files in manuscript/
        manuscript_dir = Path(__file__).parent.parent / "manuscript"
        files = list(manuscript_dir.rglob("*.md"))
        # Also check the master file
        master_file = Path(__file__).parent.parent / "villain-verse-complete.md"
        if master_file.exists():
            files.append(master_file)
    
    all_results = []
    total_issues = 0
    
    for file_path in files:
        results = lint_file(file_path)
        all_results.append(results)
        
        if args.json:
            continue  # Save output for end
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            continue
        
        print_results(results, args.verbose)
        
        # Count total issues
        file_issues = (
            len(results.get("markdownlint", [])) +
            len(results.get("spelling_style", [])) + 
            len(results.get("content_quality", []))
        )
        total_issues += file_issues
    
    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        print(f"\n🎯 Summary: {total_issues} total issues across {len(files)} files")
        
        if total_issues > 0:
            print("\n💡 To auto-fix some issues, consider:")
            print("   - Running markdownlint --fix on files")
            print("   - Using a spell checker")
            print("   - Breaking long sentences into shorter ones")
    
    return 1 if total_issues > 0 else 0

if __name__ == "__main__":
    sys.exit(main())
