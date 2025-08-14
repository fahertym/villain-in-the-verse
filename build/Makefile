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

all: clean book-pdf book-epub book-docx

clean:
	@rm -rf $(OUT)
	@mkdir -p $(OUT)

book-pdf:
	pandoc -d pandoc.yaml -d pandoc.yaml --pdf-engine=xelatex -o $(OUT)/villain-in-the-verse.pdf $(SRC)

book-epub:
	pandoc -d pandoc.yaml -d pandoc.yaml -o $(OUT)/villain-in-the-verse.epub $(SRC)

book-docx:
	pandoc -d pandoc.yaml -d pandoc.yaml -o $(OUT)/villain-in-the-verse.docx $(SRC)

lint:
	@echo "(add markdown linting here)"
