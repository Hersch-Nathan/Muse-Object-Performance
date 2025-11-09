.PHONY: all build clean help init

# Default target
all: build

# Initialize submodules
init:
	@echo "Initializing submodules..."
	git submodule update --init --recursive

# Build the play script
build: init
	@echo "Creating build directory..."
	mkdir -p build
	@echo "Building objectify.tex (first pass)..."
	pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build plays/objectify.tex
	@echo "Building objectify.tex (second pass)..."
	pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build plays/objectify.tex
	@echo "Build complete! PDF: build/objectify.pdf"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/

# Show help
help:
	@echo "Makefile targets:"
	@echo "  make          - Initialize submodules and build the play script"
	@echo "  make build    - Initialize submodules and build the play script"
	@echo "  make init     - Initialize git submodules"
	@echo "  make clean    - Remove build artifacts"
	@echo "  make help     - Show this help message"
