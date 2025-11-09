# Muse Object Performance

## Overview

This piece is an interactive performance examining how audiences respond to different forms of object performance. The audience will experience the same short piece four times, each performed through a different medium placed along a spectrum.

First, a single object (such as a blanket) will be animated as an expressive marionette. Next, the piece will be performed with a simple hand puppet, then with an animatronic character, and finally with a small robot. If time allows, additional mediums may also be explored.

The goal of this work is to investigate how meaning and emotional response shift as the object changes, and to provoke curiosity about the boundaries between object, character, and performer.

## Repository Structure

```
Muse-Object-Performance/
├── README.md                    # This file
├── Makefile                     # Build helper for compiling LaTeX
├── plays/                       # Play scripts
│   └── objectify.tex           # Main play script (R.U.R. excerpt)
├── third_party/                # External dependencies
│   └── LatexTemplates/         # LaTeX template submodule
└── build/                      # Compiled artifacts (generated, not committed)
    ├── objectify.pdf           # Compiled play script PDF
    └── *.aux, *.log            # LaTeX build artifacts
```

## Getting Started

### Prerequisites

You need a working LaTeX installation with `pdflatex`. On macOS:

- **TeX Live** (recommended): Included with MacTeX
- Install via: `brew install --cask mactex` or download from [tug.org/mactex](https://tug.org/mactex/)

Required LaTeX packages (typically included in standard distributions):
- `fontenc` - Font encoding support
- `xparse` - Command parsing
- `setspace` - Line spacing control
- `parskip` - Paragraph spacing
- `titlesec` - Section title formatting
- `textcase` - Text case conversion
- `iftex` - TeX engine detection
- `geometry` - Page layout

### Initialize Submodules

This repository uses the `LatexTemplates` submodule for the `playscript.cls` class:

```bash
git submodule update --init --recursive
```

### Building the Play Script

#### Using Make (Recommended)

The easiest way to build the play script:

```bash
make
```

This will:
1. Initialize/update submodules
2. Create the `build/` directory
3. Run `pdflatex` twice to generate `build/objectify.pdf`

Other make targets:
```bash
make build    # Build the play script (same as 'make')
make init     # Initialize submodules only
make clean    # Remove build artifacts
make help     # Show available targets
```

#### Manual Build

If you prefer to build manually:

```bash
# Initialize submodules first
git submodule update --init --recursive

# Create build directory
mkdir -p build

# Compile (run twice for proper cross-references)
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build plays/objectify.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build plays/objectify.tex
```

The compiled PDF will be at `build/objectify.pdf`.

## Play Script Details

**File**: `plays/objectify.tex`

**Source**: Selected scenes from Karel Čapek's *R.U.R. (Rossum's Universal Robots)*, translated by Paul Selver and Nigel Playfair.

**Format**: Uses the `playscript.cls` LaTeX class from the LatexTemplates submodule, which provides professional theatrical playscript formatting including:
- Title pages with character lists
- Proper dialogue formatting
- Stage directions and parentheticals
- Character name centering
- Traditional playscript margins

### Editing the Play Script

The play script uses these main commands from `playscript.cls`:

```latex
\speaker{CHARACTER}        # Character name (centered, uppercase)
\dialogue{text}           # Dialogue block (centered, narrower column)
\paren{action}            # Brief stage direction/action
\vspace{0.5em}           # Add spacing between dialogue blocks
\beat                     # Indicate a pause
```

See `third_party/LatexTemplates/docs/playscript-guide.md` for complete documentation.

## Troubleshooting

### LaTeX Build Errors

**"Class file not found"**
- Ensure submodules are initialized: `git submodule update --init --recursive`
- The class file should be at `third_party/LatexTemplates/playscript.cls`

**"Package XYZ not found"**
- Install missing package via TeX Live Manager: `tlmgr install <package-name>`
- Or install a complete distribution like MacTeX

**"Permission denied" or "Cannot write to directory"**
- Ensure you have write permissions to the `build/` directory
- Try `mkdir -p build` and check permissions

**Underfull/Overfull box warnings**
- These are typically cosmetic and don't prevent PDF generation
- The one underfull box warning in the current build is minor and acceptable

### Git Submodule Issues

**"Submodule path 'third_party/LatexTemplates': checked out 'abc123'"**
- This is normal - the submodule is tracking a specific commit

**Empty submodule directory**
- Run: `git submodule update --init --recursive`

**Updating the submodule to latest version**
```bash
cd third_party/LatexTemplates
git checkout main
git pull
cd ../..
git add third_party/LatexTemplates
git commit -m "Update LatexTemplates submodule"
```

## Build Verification

After a successful build, you should see:
- Exit code 0 from `pdflatex`
- File created: `build/objectify.pdf` (~60KB)
- 11 pages in the output PDF
- At most minor "underfull hbox" warnings (cosmetic)

To verify:
```bash
ls -lh build/objectify.pdf
```

Expected output:
```
-rw-r--r--  1 user  staff    59K Nov  8 22:11 build/objectify.pdf
```

## Contact

**Hersch Nathan** - hersch.nathan@uky.edu
