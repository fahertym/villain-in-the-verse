OUT=./_out
MANU=../manuscript

all: clean book-pdf book-epub book-docx

clean:
	@rm -rf $(OUT)
	@mkdir -p $(OUT)

book-pdf:
	pandoc --pdf-engine=xelatex -o $(OUT)/villain-in-the-verse.pdf \
	  --from markdown \
	  --toc --toc-depth=2 \
	  --metadata title="The Villain in the Verse" \
	  $(MANU)/part2_patterns/patterns_overview.md \
	  $(MANU)/part3_fallout/fallout_overview.md \
	  $(MANU)/part4_apologetics/field_guide.md \
	  $(MANU)/part5_exit_routes/exit_routes.md

book-epub:
	pandoc -o $(OUT)/villain-in-the-verse.epub \
	  --from markdown \
	  --toc --toc-depth=2 \
	  --metadata title="The Villain in the Verse" \
	  $(MANU)/part2_patterns/patterns_overview.md \
	  $(MANU)/part3_fallout/fallout_overview.md \
	  $(MANU)/part4_apologetics/field_guide.md \
	  $(MANU)/part5_exit_routes/exit_routes.md

book-docx:
	pandoc -o $(OUT)/villain-in-the-verse.docx \
	  --from markdown \
	  --toc --toc-depth=2 \
	  --metadata title="The Villain in the Verse" \
	  $(MANU)/part2_patterns/patterns_overview.md \
	  $(MANU)/part3_fallout/fallout_overview.md \
	  $(MANU)/part4_apologetics/field_guide.md \
	  $(MANU)/part5_exit_routes/exit_routes.md

lint:
	@echo "(add markdown linting here)"
