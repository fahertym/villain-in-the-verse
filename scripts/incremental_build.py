#!/usr/bin/env python3
"""
Incremental build system for The Villain in the Verse manuscript.
Only rebuilds when source files have changed.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set


class BuildCache:
    """Manages build cache for incremental builds."""
    
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load existing cache or create new one."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return {
            "version": "1.0",
            "files": {},
            "targets": {},
            "last_build": None
        }
    
    def save_cache(self):
        """Save cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get hash of file content."""
        if not file_path.exists():
            return ""
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except IOError:
            return ""
    
    def has_file_changed(self, file_path: Path) -> bool:
        """Check if file has changed since last build."""
        current_hash = self.get_file_hash(file_path)
        cached_hash = self.cache["files"].get(str(file_path), "")
        return current_hash != cached_hash
    
    def update_file_hash(self, file_path: Path):
        """Update cached hash for file."""
        current_hash = self.get_file_hash(file_path)
        self.cache["files"][str(file_path)] = current_hash
    
    def has_target_changed(self, target: str, dependencies: List[Path]) -> bool:
        """Check if target needs rebuilding based on dependencies."""
        # Check if target file exists
        target_info = self.cache["targets"].get(target, {})
        target_file = Path(target_info.get("output_file", ""))
        
        if not target_file.exists():
            return True
        
        # Check if any dependencies changed
        for dep in dependencies:
            if self.has_file_changed(dep):
                return True
        
        # Check target modification time vs dependencies
        target_mtime = target_file.stat().st_mtime if target_file.exists() else 0
        for dep in dependencies:
            if dep.exists() and dep.stat().st_mtime > target_mtime:
                return True
        
        return False
    
    def update_target(self, target: str, output_file: Path, dependencies: List[Path]):
        """Update target information in cache."""
        self.cache["targets"][target] = {
            "output_file": str(output_file),
            "dependencies": [str(dep) for dep in dependencies],
            "built_at": time.time()
        }
        
        # Update file hashes for all dependencies
        for dep in dependencies:
            self.update_file_hash(dep)


class IncrementalBuilder:
    """Handles incremental building of manuscript formats."""
    
    def __init__(self, build_dir: Path, cache_file: Path):
        self.build_dir = build_dir
        self.manuscript_dir = build_dir.parent / "manuscript"
        self.cache = BuildCache(cache_file)
        
        # Define source files
        self.source_files = self._get_source_files()
        
        # Define build targets
        self.targets = {
            "pdf": {
                "output": build_dir / "_out" / "villain-in-the-verse.pdf",
                "command": ["make", "book-pdf"],
                "description": "PDF format"
            },
            "epub": {
                "output": build_dir / "_out" / "villain-in-the-verse.epub", 
                "command": ["make", "book-epub"],
                "description": "EPUB format"
            },
            "docx": {
                "output": build_dir / "_out" / "villain-in-the-verse.docx",
                "command": ["make", "book-docx"],
                "description": "DOCX format"
            }
        }
    
    def _get_source_files(self) -> List[Path]:
        """Get list of all source files that affect the build."""
        sources = []
        
        # Master file
        master_file = self.build_dir.parent / "villain-verse-complete.md"
        if master_file.exists():
            sources.append(master_file)
        
        # Manuscript files
        for pattern in ["frontmatter/*.md", "part*/*.md"]:
            sources.extend(self.manuscript_dir.glob(pattern))
        
        # Build configuration files
        build_configs = [
            "pandoc.yaml",
            "Makefile", 
            "epub.css",
            "templates/*.latex",
            "filters/*.lua"
        ]
        
        for pattern in build_configs:
            sources.extend(self.build_dir.glob(pattern))
        
        return [p for p in sources if p.exists()]
    
    def needs_split(self) -> bool:
        """Check if split operation is needed."""
        master_file = self.build_dir.parent / "villain-verse-complete.md"
        if not master_file.exists():
            return False
        
        # Check if master file changed
        if self.cache.has_file_changed(master_file):
            return True
        
        # Check if any individual chapters are missing
        script_dir = self.build_dir.parent / "scripts"
        try:
            result = subprocess.run([
                "python3", str(script_dir / "sync_checker.py"), "--json"
            ], capture_output=True, text=True, cwd=self.build_dir)
            
            if result.returncode == 0:
                sync_data = json.loads(result.stdout)
                return sync_data.get("status") != "success"
        except Exception:
            pass
        
        return True
    
    def run_split(self) -> bool:
        """Run split operation if needed."""
        if not self.needs_split():
            print("📚 Split not needed - files are synchronized")
            return True
        
        print("📚 Splitting master file...")
        try:
            result = subprocess.run(
                ["make", "split"], 
                cwd=self.build_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Split completed successfully")
                return True
            else:
                print(f"❌ Split failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Split error: {e}")
            return False
    
    def needs_build(self, target: str) -> bool:
        """Check if target needs rebuilding."""
        if target not in self.targets:
            return False
        
        target_info = self.targets[target]
        return self.cache.has_target_changed(target, self.source_files)
    
    def build_target(self, target: str, force: bool = False) -> bool:
        """Build a specific target."""
        if target not in self.targets:
            print(f"❌ Unknown target: {target}")
            return False
        
        target_info = self.targets[target]
        
        if not force and not self.needs_build(target):
            print(f"📖 {target_info['description']}: up to date")
            return True
        
        print(f"🔨 Building {target_info['description']}...")
        
        try:
            result = subprocess.run(
                target_info["command"],
                cwd=self.build_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ {target_info['description']} built successfully")
                self.cache.update_target(target, target_info["output"], self.source_files)
                return True
            else:
                print(f"❌ {target_info['description']} build failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Build error for {target}: {e}")
            return False
    
    def build_all(self, force: bool = False, targets: List[str] = None) -> bool:
        """Build all targets (or specified targets)."""
        if targets is None:
            targets = list(self.targets.keys())
        
        success = True
        
        # Ensure output directory exists
        output_dir = self.build_dir / "_out"
        output_dir.mkdir(exist_ok=True)
        
        for target in targets:
            if not self.build_target(target, force):
                success = False
        
        return success
    
    def clean(self):
        """Clean build artifacts."""
        print("🧹 Cleaning build artifacts...")
        try:
            result = subprocess.run(
                ["make", "clean"],
                cwd=self.build_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Clean completed")
                # Clear cache for targets since they were deleted
                self.cache.cache["targets"] = {}
            else:
                print(f"❌ Clean failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Clean error: {e}")
    
    def status(self):
        """Show build status."""
        print("📊 BUILD STATUS")
        print("=" * 50)
        
        # Check source files
        changed_files = [f for f in self.source_files if self.cache.has_file_changed(f)]
        if changed_files:
            print(f"📝 Changed files ({len(changed_files)}):")
            for f in changed_files[:10]:  # Show first 10
                rel_path = f.relative_to(self.build_dir.parent)
                print(f"   • {rel_path}")
            if len(changed_files) > 10:
                print(f"   ... and {len(changed_files) - 10} more")
        else:
            print("📝 No changed source files detected")
        
        print()
        
        # Check targets
        for target, target_info in self.targets.items():
            needs_build = self.needs_build(target)
            exists = target_info["output"].exists()
            
            status_icon = "🔨" if needs_build else "✅" if exists else "❓"
            status_text = "needs build" if needs_build else "up to date" if exists else "not built"
            
            print(f"{status_icon} {target_info['description']}: {status_text}")
        
        # Cache info
        print(f"\n📋 Cache: {len(self.cache.cache['files'])} files tracked")
        if self.cache.cache.get("last_build"):
            last_build = time.ctime(self.cache.cache["last_build"])
            print(f"🕒 Last build: {last_build}")


def main():
    parser = argparse.ArgumentParser(description="Incremental build system for manuscript")
    parser.add_argument("--build-dir", default=".",
                       help="Build directory (default: current directory)")
    parser.add_argument("--cache", default="../.build_cache.json",
                       help="Cache file location")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Force rebuild even if up to date")
    parser.add_argument("--clean", action="store_true",
                       help="Clean build artifacts")
    parser.add_argument("--status", action="store_true",
                       help="Show build status")
    parser.add_argument("targets", nargs="*", 
                       choices=["pdf", "epub", "docx", "all"],
                       help="Specific targets to build (default: all)")
    
    args = parser.parse_args()
    
    build_dir = Path(args.build_dir).resolve()
    cache_file = (build_dir / args.cache).resolve()
    
    builder = IncrementalBuilder(build_dir, cache_file)
    
    try:
        if args.clean:
            builder.clean()
            return 0
        
        if args.status:
            builder.status()
            return 0
        
        # Determine targets
        targets = args.targets if args.targets else ["all"]
        if "all" in targets:
            targets = ["pdf", "epub", "docx"]
        
        # Run split if needed
        if not builder.run_split():
            return 1
        
        # Build targets
        success = builder.build_all(args.force, targets)
        
        # Update cache
        builder.cache.cache["last_build"] = time.time()
        builder.cache.save_cache()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n❌ Build interrupted")
        return 1
    except Exception as e:
        print(f"❌ Build error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
