
SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: help clean html

help:
	@echo "Usage:"
	@echo "  make html   # build HTML docs"
	@echo "  make clean  # remove built files"

clean:
	@echo "Cleaning $(BUILDDIR)…"
	rm -rf $(BUILDDIR)

html:
	@echo "Building HTML from $(SOURCEDIR) into $(BUILDDIR)/html…"
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."