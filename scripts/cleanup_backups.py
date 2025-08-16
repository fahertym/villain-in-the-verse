#!/usr/bin/env python3
"""
Clean up backup directories created by split operations.
Provides options to remove old backups while keeping recent ones.
"""

import argparse
import re
import shutil
import sys
import time
from pathlib import Path
from typing import List, Tuple


def parse_backup_timestamp(backup_name: str) -> float:
    """Extract timestamp from backup directory name."""
    match = re.search(r'__backup__(\d{8}-\d{6})$', backup_name)
    if not match:
        return 0
    
    timestamp_str = match.group(1)
    try:
        # Parse YYYYMMDD-HHMMSS format
        return time.mktime(time.strptime(timestamp_str, '%Y%m%d-%H%M%S'))
    except ValueError:
        return 0


def find_backup_directories(manuscript_dir: Path) -> List[Tuple[Path, float]]:
    """Find all backup directories with their timestamps."""
    backups = []
    
    for item in manuscript_dir.iterdir():
        if item.is_dir() and '__backup__' in item.name:
            timestamp = parse_backup_timestamp(item.name)
            if timestamp > 0:
                backups.append((item, timestamp))
    
    # Sort by timestamp (newest first)
    backups.sort(key=lambda x: x[1], reverse=True)
    return backups


def get_backup_groups(backups: List[Tuple[Path, float]]) -> dict:
    """Group backups by their base directory name."""
    groups = {}
    
    for backup_path, timestamp in backups:
        # Extract base name (everything before __backup__)
        base_name = backup_path.name.split('__backup__')[0]
        if base_name not in groups:
            groups[base_name] = []
        groups[base_name].append((backup_path, timestamp))
    
    # Sort each group by timestamp (newest first)
    for group in groups.values():
        group.sort(key=lambda x: x[1], reverse=True)
    
    return groups


def cleanup_backups(manuscript_dir: Path, keep_recent: int = 0, older_than_days: int = 0, 
                   dry_run: bool = False, force: bool = False) -> int:
    """Clean up backup directories based on criteria."""
    
    if not manuscript_dir.exists():
        print(f"❌ Manuscript directory not found: {manuscript_dir}", file=sys.stderr)
        return 1
    
    backups = find_backup_directories(manuscript_dir)
    
    if not backups:
        print("✅ No backup directories found to clean up")
        return 0
    
    print(f"🔍 Found {len(backups)} backup directories")
    
    # Determine what to remove
    to_remove = []
    
    if keep_recent > 0:
        # Group by base directory and keep N most recent per group
        groups = get_backup_groups(backups)
        
        for base_name, group_backups in groups.items():
            if len(group_backups) > keep_recent:
                to_remove.extend([path for path, _ in group_backups[keep_recent:]])
                print(f"📁 {base_name}: keeping {keep_recent} most recent, removing {len(group_backups) - keep_recent}")
    
    elif older_than_days > 0:
        # Remove backups older than specified days
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        to_remove = [path for path, timestamp in backups if timestamp < cutoff_time]
        print(f"🗓️  Removing backups older than {older_than_days} days ({len(to_remove)} directories)")
    
    else:
        # Remove all backups
        to_remove = [path for path, _ in backups]
        print(f"🗑️  Removing all backup directories ({len(to_remove)} directories)")
    
    if not to_remove:
        print("✅ No backups need to be removed based on criteria")
        return 0
    
    # Show what will be removed
    print("\n📋 Directories to be removed:")
    total_size = 0
    for path in to_remove:
        try:
            size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            total_size += size
            size_mb = size / (1024 * 1024)
            print(f"  - {path.name} ({size_mb:.1f} MB)")
        except Exception:
            print(f"  - {path.name}")
    
    total_mb = total_size / (1024 * 1024)
    print(f"\n💾 Total space to be freed: {total_mb:.1f} MB")
    
    if dry_run:
        print("\n🔍 DRY RUN: No files were actually removed")
        return 0
    
    # Confirm removal
    if not force:
        response = input(f"\n❓ Remove {len(to_remove)} backup directories? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cleanup cancelled")
            return 1
    
    # Remove directories
    removed_count = 0
    for path in to_remove:
        try:
            shutil.rmtree(path)
            removed_count += 1
            print(f"✅ Removed {path.name}")
        except Exception as e:
            print(f"❌ Failed to remove {path.name}: {e}", file=sys.stderr)
    
    print(f"\n🎉 Successfully removed {removed_count} backup directories")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Clean up manuscript backup directories")
    parser.add_argument("--manuscript", default="../manuscript",
                       help="Path to manuscript directory (default: ../manuscript)")
    
    # Cleanup strategies (mutually exclusive)
    strategy = parser.add_mutually_exclusive_group()
    strategy.add_argument("--keep-recent", type=int, metavar="N",
                         help="Keep N most recent backups per directory type")
    strategy.add_argument("--older-than", type=int, metavar="DAYS",
                         help="Remove backups older than N days")
    strategy.add_argument("--all", action="store_true",
                         help="Remove all backup directories")
    
    # Options
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be removed without actually removing")
    parser.add_argument("--force", action="store_true",
                       help="Remove without confirmation")
    
    args = parser.parse_args()
    
    # Default behavior if no strategy specified
    if not any([args.keep_recent, args.older_than, args.all]):
        args.keep_recent = 2  # Keep 2 most recent by default
    
    script_dir = Path(__file__).parent
    manuscript_dir = (script_dir / args.manuscript).resolve()
    
    keep_recent = args.keep_recent if args.keep_recent else 0
    older_than_days = args.older_than if args.older_than else 0
    
    if args.all:
        keep_recent = 0
        older_than_days = 0
    
    return cleanup_backups(
        manuscript_dir=manuscript_dir,
        keep_recent=keep_recent,
        older_than_days=older_than_days,
        dry_run=args.dry_run,
        force=args.force
    )


if __name__ == "__main__":
    sys.exit(main())
