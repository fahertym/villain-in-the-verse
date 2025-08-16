#!/usr/bin/env python3
"""
Comprehensive quality check script for The Villain in the Verse manuscript.
Runs all quality checks and provides a summary report.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def run_command(cmd: List[str], cwd: Path = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=cwd,
            timeout=300  # 5 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def check_lint() -> Dict:
    """Run linting checks."""
    print("🔍 Running linting checks...")
    
    script_dir = Path(__file__).parent
    exit_code, stdout, stderr = run_command([
        "python3", str(script_dir / "lint_manuscript.py"), "--json"
    ])
    
    if exit_code == 0:
        try:
            results = json.loads(stdout)
            total_issues = sum(
                len(r.get("markdownlint", [])) + 
                len(r.get("spelling_style", [])) + 
                len(r.get("content_quality", []))
                for r in results if "error" not in r
            )
            return {
                "status": "success",
                "issues": total_issues,
                "details": results
            }
        except json.JSONDecodeError:
            return {"status": "error", "message": "Failed to parse lint results"}
    else:
        return {"status": "error", "message": stderr or "Linting failed"}

def check_build() -> Dict:
    """Test that all formats build successfully."""
    print("🔨 Testing build process...")
    
    build_dir = Path(__file__).parent.parent / "build"
    
    # Test PDF build
    exit_code, stdout, stderr = run_command(
        ["make", "clean", "book-pdf"], 
        cwd=build_dir
    )
    
    if exit_code != 0:
        return {
            "status": "error", 
            "message": f"PDF build failed: {stderr}"
        }
    
    # Test EPUB build
    exit_code, stdout, stderr = run_command(
        ["make", "book-epub"], 
        cwd=build_dir
    )
    
    if exit_code != 0:
        return {
            "status": "error", 
            "message": f"EPUB build failed: {stderr}"
        }
    
    # Test DOCX build
    exit_code, stdout, stderr = run_command(
        ["make", "book-docx"], 
        cwd=build_dir
    )
    
    if exit_code != 0:
        return {
            "status": "error", 
            "message": f"DOCX build failed: {stderr}"
        }
    
    return {"status": "success", "message": "All formats built successfully"}

def check_word_count() -> Dict:
    """Check word count and progress."""
    print("📊 Checking word count and progress...")
    
    script_dir = Path(__file__).parent
    exit_code, stdout, stderr = run_command([
        "python3", str(script_dir / "word_count.py"), "--json"
    ])
    
    if exit_code == 0:
        try:
            results = json.loads(stdout)
            valid_files = [r for r in results if "error" not in r]
            total_words = sum(r.get("words", 0) for r in valid_files)
            
            return {
                "status": "success",
                "total_words": total_words,
                "file_count": len(valid_files),
                "details": results
            }
        except json.JSONDecodeError:
            return {"status": "error", "message": "Failed to parse word count results"}
    else:
        return {"status": "error", "message": stderr or "Word count check failed"}

def check_file_structure() -> Dict:
    """Check that required files and directories exist."""
    print("📁 Checking file structure...")
    
    root_dir = Path(__file__).parent.parent
    required_files = [
        "villain-verse-complete.md",
        "build/Makefile", 
        "build/pandoc.yaml",
        "manuscript/frontmatter/titlepage.md",
        "manuscript/frontmatter/introduction.md"
    ]
    
    required_dirs = [
        "manuscript/part1_case_files",
        "manuscript/part2_patterns", 
        "manuscript/frontmatter",
        "build",
        "scripts"
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file_path in required_files:
        if not (root_dir / file_path).exists():
            missing_files.append(file_path)
    
    for dir_path in required_dirs:
        if not (root_dir / dir_path).is_dir():
            missing_dirs.append(dir_path)
    
    if missing_files or missing_dirs:
        return {
            "status": "error",
            "missing_files": missing_files,
            "missing_dirs": missing_dirs
        }
    
    return {"status": "success", "message": "All required files and directories present"}

def check_split_consistency() -> Dict:
    """Check that individual chapters match the master file."""
    print("🔄 Checking split consistency...")
    
    root_dir = Path(__file__).parent.parent
    master_file = root_dir / "villain-verse-complete.md"
    
    if not master_file.exists():
        return {"status": "error", "message": "Master file not found"}
    
    # Test split operation
    script_dir = Path(__file__).parent
    exit_code, stdout, stderr = run_command([
        "python3", str(script_dir / "split_from_complete.py"), 
        str(master_file), "--dest", "manuscript"
    ], cwd=root_dir)
    
    if exit_code != 0:
        return {
            "status": "error", 
            "message": f"Split operation failed: {stderr}"
        }
    
    return {"status": "success", "message": "Split operation successful"}

def generate_report(checks: Dict) -> str:
    """Generate a comprehensive quality report."""
    report = []
    report.append("📋 QUALITY CHECK REPORT")
    report.append("=" * 50)
    report.append("")
    
    total_checks = len(checks)
    passed_checks = sum(1 for check in checks.values() if check.get("status") == "success")
    
    # Overall status
    if passed_checks == total_checks:
        report.append("✅ OVERALL STATUS: PASSED")
        overall_status = "PASSED"
    else:
        report.append("❌ OVERALL STATUS: FAILED")
        overall_status = "FAILED"
    
    report.append(f"📊 {passed_checks}/{total_checks} checks passed")
    report.append("")
    
    # Individual check results
    for check_name, result in checks.items():
        status_icon = "✅" if result.get("status") == "success" else "❌"
        report.append(f"{status_icon} {check_name.replace('_', ' ').title()}")
        
        if result.get("status") == "success":
            if "message" in result:
                report.append(f"   {result['message']}")
            if "total_words" in result:
                report.append(f"   Total words: {result['total_words']:,}")
            if "issues" in result:
                report.append(f"   Issues found: {result['issues']}")
        else:
            report.append(f"   Error: {result.get('message', 'Unknown error')}")
            if "missing_files" in result:
                report.append(f"   Missing files: {', '.join(result['missing_files'])}")
            if "missing_dirs" in result:
                report.append(f"   Missing directories: {', '.join(result['missing_dirs'])}")
        
        report.append("")
    
    # Recommendations
    if overall_status == "FAILED":
        report.append("💡 RECOMMENDATIONS:")
        report.append("- Fix any build errors before proceeding")
        report.append("- Address linting issues for better quality") 
        report.append("- Ensure all required files are present")
        report.append("- Run 'make lint-fix' to auto-fix some issues")
        report.append("")
    
    return "\n".join(report)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive quality checks")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--no-build", action="store_true", help="Skip build tests (faster)")
    parser.add_argument("--save", help="Save report to file")
    args = parser.parse_args()
    
    print("🔍 Running comprehensive quality checks...")
    print()
    
    # Run all checks
    checks = {}
    
    checks["file_structure"] = check_file_structure()
    checks["split_consistency"] = check_split_consistency()
    checks["word_count"] = check_word_count()
    checks["linting"] = check_lint()
    
    if not args.no_build:
        checks["build"] = check_build()
    
    # Generate report
    if args.json:
        print(json.dumps(checks, indent=2))
    else:
        report = generate_report(checks)
        print(report)
        
        if args.save:
            Path(args.save).write_text(report)
            print(f"💾 Report saved to {args.save}")
    
    # Exit with error code if any checks failed
    failed_checks = [name for name, result in checks.items() 
                    if result.get("status") != "success"]
    
    if failed_checks:
        print(f"\n❌ {len(failed_checks)} checks failed: {', '.join(failed_checks)}")
        return 1
    else:
        print("\n✅ All quality checks passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
