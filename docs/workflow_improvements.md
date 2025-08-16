# Workflow Improvements Guide

This document explains the new workflow improvements added to streamline your book writing process.

## 🆕 New Features Added

### 1. **Sync Checking** 
Verify that your master file and split chapters are synchronized:

```bash
cd build
make sync-check         # Check sync status
make sync-check-fix     # Auto-fix sync issues
make sync-master        # Regenerate master from chapters
```

### 2. **Chapter Management**
Easily create, rename, and move chapters:

```bash
cd build
make chapter-new        # Create new chapter from template
make chapter-rename     # Rename existing chapter
make chapter-move       # Move chapter to different part
make chapter-status     # Show completion overview
```

### 3. **Enhanced Development Workflow**
Streamlined commands for faster iteration:

```bash
cd build
make dev-start          # Start full development environment
make quick-build        # Fast build without quality checks
make progress           # Show current progress and tasks
```

### 4. **Incremental Builds**
Smart building that only rebuilds what's changed:

```bash
cd build
make build-incremental  # Build only what's changed
make build-status       # Show what needs rebuilding
make build-force        # Force rebuild everything
make build-clean        # Clean build cache
```

### 5. **GitHub Actions**
Automated quality checks on every pull request:

- **Quality Check Workflow**: Runs linting, sync checks, and build tests
- **Release Workflow**: Automatically builds and releases tagged versions
- **PR Comments**: Adds quality reports to pull requests

## 🔧 How to Use

### Daily Writing Workflow

1. **Start your writing session**:
   ```bash
   cd build
   make dev-start
   ```

2. **Create a new chapter**:
   ```bash
   make chapter-new
   ```

3. **Check your progress**:
   ```bash
   make progress
   ```

4. **Quick iteration** (while writing):
   ```bash
   make build-incremental  # Only rebuilds changed content
   ```

5. **Quality check** (before committing):
   ```bash
   make quality-fast
   ```

### Chapter Management

**Creating a new chapter**:
```bash
make chapter-new
# Follow prompts for title and part
```

**Moving chapters between parts**:
```bash
make chapter-move
# Enter chapter identifier and target part
```

**Checking completion status**:
```bash
make chapter-status     # Detailed view
make progress          # Summary view
```

### Sync Management

**Check if master and chapters are in sync**:
```bash
make sync-check
```

**Fix sync issues automatically**:
```bash
make sync-check-fix
```

**Regenerate master file from individual chapters**:
```bash
make sync-master  # ⚠️ This overwrites the master file!
```

### Build Optimization

**Smart incremental builds** (recommended for daily use):
```bash
make build-incremental
```

**Check what needs rebuilding**:
```bash
make build-status
```

**Force complete rebuild** (if something seems wrong):
```bash
make build-force
```

## 📊 Quality Assurance

### Automated Checks
The system now runs comprehensive quality checks:

- **File structure** validation
- **Sync status** between master and chapters  
- **Linting** for markdown formatting
- **Word count** and progress tracking
- **Build verification** for all formats

### GitHub Integration
- Pull requests automatically get quality reports
- Failed builds prevent merging
- Releases are automatically built and published

## 🎯 Best Practices

### 1. **Use Incremental Builds**
For daily writing, use `make build-incremental` instead of `make all`. It's much faster.

### 2. **Check Sync Regularly**
Run `make sync-check` periodically to ensure your dual-source system stays synchronized.

### 3. **Monitor Progress**
Use `make progress` to see completion status and identify next tasks.

### 4. **Commit Often**
The GitHub Actions will catch issues early if you commit frequently.

### 5. **Use Chapter Manager**
Let the chapter manager handle file naming and organization rather than doing it manually.

## 🚀 Performance Improvements

These improvements provide significant speed gains:

- **Incremental builds**: 5-10x faster for daily iteration
- **Smart sync checking**: Avoids unnecessary splits
- **Parallel GitHub Actions**: Quality checks run in parallel
- **Cached builds**: Reuses work when possible

## 🔧 Troubleshooting

### Sync Issues
If sync check fails:
```bash
make sync-check-fix     # Try automatic fix
make split              # Force re-split if needed
```

### Build Issues
If builds are failing:
```bash
make build-clean        # Clear incremental cache
make build-force        # Force rebuild
make quality           # Check for underlying issues
```

### GitHub Actions Failing
Check the Actions tab in GitHub for detailed error logs. Common issues:
- Linting failures (run `make lint-fix`)
- Sync problems (run `make sync-check-fix`)
- Build errors (run `make quality` locally)

## 📈 Metrics

Track your workflow efficiency:
- **Build time**: `make build-status` shows what's cached
- **Word count progress**: `make stats-detail`
- **Chapter completion**: `make chapter-status`
- **Quality score**: `make quality` success rate

These improvements transform your workflow from manual and error-prone to automated and efficient, letting you focus on writing great content rather than managing the build process.
