include images.mk
OUT=./_out
SRC=../manuscript/frontmatter/titlepage.md \
    ../manuscript/frontmatter/introduction.md \
    ../manuscript/part1_case_files/*.md \
    ../manuscript/part2_patterns/patterns_overview.md \
    ../manuscript/part2_patterns/*.md \
    ../manuscript/part3_fallout/fallout_overview.md \
    ../manuscript/part4_apologetics/field_guide.md \
    ../manuscript/part5_exit_routes/exit_routes.md \
    ../manuscript/frontmatter/acknowledgments.md

all: images split clean book-pdf book-epub book-docx

split:
	@echo "Splitting master file into individual chapters..."
	@python3 ../scripts/split_from_complete.py ../villain-verse-complete.md --dest ../manuscript

clean:
	@rm -rf $(OUT)
	@mkdir -p $(OUT)

book-pdf:
	pandoc -d pandoc.yaml --resource-path=..:../.. --pdf-engine=xelatex -o $(OUT)/villain-in-the-verse.pdf $(SRC)

book-epub:
	pandoc -d pandoc.yaml --resource-path=..:../.. -o $(OUT)/villain-in-the-verse.epub $(SRC)

book-docx:
	pandoc -d pandoc.yaml --resource-path=..:../.. -o $(OUT)/villain-in-the-verse.docx $(SRC)

lint:
	@echo "🔍 Linting manuscript..."
	@python3 ../scripts/lint_manuscript.py

lint-fix:
	@echo "🔧 Auto-fixing markdown issues..."
	@if command -v markdownlint >/dev/null 2>&1; then \
		find ../manuscript -name "*.md" -exec markdownlint --fix --config .markdownlint.yaml {} \; ; \
		markdownlint --fix --config .markdownlint.yaml ../villain-verse-complete.md 2>/dev/null || true ; \
	else \
		echo "markdownlint not installed. Install with: npm install -g markdownlint-cli" ; \
	fi

setup-linting:
	@echo "📦 Setting up linting tools..."
	@if ! command -v markdownlint >/dev/null 2>&1; then \
		echo "Installing markdownlint-cli..." ; \
		npm install -g markdownlint-cli || echo "Failed to install markdownlint. Please install manually." ; \
	else \
		echo "markdownlint already installed ✅" ; \
	fi

split-only:
	@echo "Splitting master file into individual chapters..."
	@python3 ../scripts/split_from_complete.py ../villain-verse-complete.md --dest ../manuscript

stats:
	@echo "📊 Analyzing manuscript statistics..."
	@python3 ../scripts/word_count.py --target 80000 --chart

stats-detail:
	@echo "📊 Detailed manuscript statistics..."
	@python3 ../scripts/word_count.py --target 80000 --details --chart --save ../progress.json

preview:
	@echo "🌐 Starting development server with live preview..."
	@python3 ../scripts/dev_server.py

preview-build:
	@echo "🔨 Building HTML preview..."
	@python3 ../scripts/dev_server.py --build-only

watch:
	@echo "👀 Watching for changes and auto-rebuilding..."
	@while true; do \
		inotifywait -r -e modify ../manuscript/ ../villain-verse-complete.md 2>/dev/null && \
		echo "📝 Changes detected, rebuilding..." && \
		make split clean book-pdf || true; \
	done

quality:
	@echo "🔍 Running comprehensive quality checks..."
	@python3 ../scripts/quality_check.py

quality-fast:
	@echo "🔍 Running quality checks (no build test)..."
	@python3 ../scripts/quality_check.py --no-build

sync-check:
	@echo "🔄 Checking sync between master and split files..."
	@python3 ../scripts/sync_checker.py

sync-check-fix:
	@echo "🔧 Checking sync and auto-fixing if needed..."
	@python3 ../scripts/sync_checker.py --fix

sync-master:
	@echo "🔄 Regenerating master file from split chapters..."
	@echo "⚠️  This will overwrite the master file!"
	@read -p "Continue? (y/N) " confirm && [ "$$confirm" = "y" ] || exit 1
	@python3 ../scripts/merge_chapters.py --output ../villain-verse-complete.md

dev-start:
	@echo "🚀 Starting development environment..."
	@echo "📊 Checking sync status..."
	@python3 ../scripts/sync_checker.py || true
	@echo "🌐 Starting preview server..."
	@python3 ../scripts/dev_server.py &
	@echo "👀 Starting file watcher..."
	@make watch

quick-build:
	@echo "⚡ Quick build for development (skipping quality checks)..."
	@make split clean book-pdf

chapter-new:
	@echo "📝 Creating new chapter..."
	@python3 ../scripts/chapter_manager.py create

chapter-rename:
	@echo "📝 Renaming chapter..."
	@python3 ../scripts/chapter_manager.py rename

chapter-move:
	@echo "📝 Moving chapter..."
	@python3 ../scripts/chapter_manager.py move

chapter-status:
	@echo "📋 Chapter status overview..."
	@python3 ../scripts/chapter_manager.py status

progress:
	@echo "📊 Current progress and next tasks..."
	@python3 ../scripts/word_count.py --target 80000
	@echo ""
	@python3 ../scripts/chapter_manager.py status --summary

# Incremental build targets
build-incremental:
	@echo "⚡ Incremental build (only rebuild what's changed)..."
	@python3 ../scripts/incremental_build.py

build-status:
	@echo "📊 Build status..."
	@python3 ../scripts/incremental_build.py --status

build-force:
	@echo "🔨 Force rebuild all targets..."
	@python3 ../scripts/incremental_build.py --force

build-clean:
	@echo "🧹 Clean incremental build cache..."
	@python3 ../scripts/incremental_build.py --clean

help:
	@echo "📚 The Villain in the Verse - Build Commands"
	@echo "=============================================="
	@echo "📖 Content Management:"
	@echo "  split        - Split master file into chapters"
	@echo "  split-only   - Split without building"
	@echo "  sync-check   - Check sync between master and split files"
	@echo "  sync-check-fix - Check sync and auto-fix if needed"
	@echo "  sync-master  - Regenerate master from split chapters"
	@echo ""
	@echo "📝 Chapter Management:"
	@echo "  chapter-new  - Create new chapter from template"
	@echo "  chapter-rename - Rename existing chapter"
	@echo "  chapter-move - Move chapter to different part"
	@echo "  chapter-status - Show chapter completion status"
	@echo ""
	@echo "🔨 Building:"
	@echo "  all            - Build all formats (PDF, EPUB, DOCX)"
	@echo "  book-pdf       - Build PDF only"
	@echo "  book-epub      - Build EPUB only"
	@echo "  book-docx      - Build DOCX only"
	@echo "  quick-build    - Fast build (skip quality checks)"
	@echo "  build-incremental - Smart incremental build"
	@echo "  build-status   - Show what needs rebuilding"
	@echo "  build-force    - Force rebuild everything"
	@echo "  build-clean    - Clean incremental build cache"
	@echo ""
	@echo "🔍 Quality:"
	@echo "  quality      - Run comprehensive quality checks"
	@echo "  quality-fast - Quick quality checks (skip build test)"
	@echo "  lint         - Check markdown formatting and style"
	@echo "  lint-fix     - Auto-fix formatting issues"
	@echo "  setup-linting- Install linting tools"
	@echo ""
	@echo "📊 Analytics:"
	@echo "  stats        - Show word count and progress"
	@echo "  stats-detail - Detailed stats with progress tracking"
	@echo "  progress     - Current progress and next tasks"
	@echo ""
	@echo "🌐 Development:"
	@echo "  dev-start    - Start full development environment"
	@echo "  preview      - Start live preview server only"
	@echo "  preview-build- Build HTML preview only"
	@echo "  watch        - Auto-rebuild on file changes"
	@echo ""
	@echo "📦 Distribution:"
	@echo "  dist         - Copy output files to dist/"

dist:
	@mkdir -p ../dist && cp -v ./_out/* ../dist/
