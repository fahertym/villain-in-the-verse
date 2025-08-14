SVG_DIR := ../figures
SVGS    := $(wildcard $(SVG_DIR)/*.svg)
PDFS    := $(SVGS:.svg=.pdf)
PNGS    := $(SVGS:.svg=.png)

$(SVG_DIR)/%.pdf: $(SVG_DIR)/%.svg
	rsvg-convert -f pdf -o $@ $<

$(SVG_DIR)/%.png: $(SVG_DIR)/%.svg
	rsvg-convert -f png -o $@ $<

images: $(PDFS) $(PNGS)
