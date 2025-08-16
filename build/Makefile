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
	@echo "(add markdown linting here)"

split-only:
	@echo "Splitting master file into individual chapters..."
	@python3 ../scripts/split_from_complete.py ../villain-verse-complete.md --dest ../manuscript

dist:
	@mkdir -p ../dist && cp -v ./_out/* ../dist/
