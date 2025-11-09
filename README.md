# Muse Object Performance

## Overview

This piece is an interactive performance examining how audiences respond to different forms of object performance. The audience will experience the same short piece four times, each performed through a different medium placed along a spectrum.

First, a single object (such as a blanket) will be animated as an expressive marionette. Next, the piece will be performed with a simple hand puppet, then with an animatronic character, and finally with a small robot. If time allows, additional mediums may also be explored.

The goal of this work is to investigate how meaning and emotional response shift as the object changes, and to provoke curiosity about the boundaries between object, character, and performer.

## Repository Structure

```
Muse-Object-Performance/
├── README.md                    # This file
├── .gitignore                   # Git ignore rules
├── LatexTemplates/              # LaTeX template submodule
│   └── playscript.cls          # Playscript class file
└── plays/                       # Play scripts and compiled PDFs
    ├── objectify.tex           # Main play script (R.U.R. excerpt)
    └── objectify.pdf           # Compiled PDF
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

To rebuild the PDF from the LaTeX source:

```bash
cd plays
pdflatex objectify.tex
pdflatex objectify.tex  # Run twice for proper cross-references
```

The compiled PDF will be at `plays/objectify.pdf`. LaTeX build artifacts (`.aux`, `.log`, etc.) are ignored by git.

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

See `LatexTemplates/docs/playscript-guide.md` for complete documentation.

## Troubleshooting

### LaTeX Build Errors

**"Class file not found"**
- Ensure submodules are initialized: `git submodule update --init --recursive`
- The class file should be at `LatexTemplates/playscript.cls`

**"Package XYZ not found"**
- Install missing package via TeX Live Manager: `tlmgr install <package-name>`
- Or install a complete distribution like MacTeX

**Underfull/Overfull box warnings**
- These are typically cosmetic and don't prevent PDF generation
- The one underfull box warning in the current build is minor and acceptable

### Git Submodule Issues

**"Submodule path 'LatexTemplates': checked out 'abc123'"**
- This is normal - the submodule is tracking a specific commit

**Empty submodule directory**
- Run: `git submodule update --init --recursive`

**Updating the submodule to latest version**
```bash
cd LatexTemplates
git checkout main
git pull
cd ..
git add LatexTemplates
git commit -m "Update LatexTemplates submodule"
```

## Build Verification

After a successful build, you should see:
- Exit code 0 from `pdflatex`
- File created: `plays/objectify.pdf` (~60KB)
- 11 pages in the output PDF
- At most minor "underfull hbox" warnings (cosmetic)

To verify:
```bash
ls -lh plays/objectify.pdf
```

Expected output:
```
-rw-r--r--  1 user  staff    59K Nov  8 22:14 plays/objectify.pdf
```

## Contact

**Hersch Nathan** - hersch.nathan@uky.edu
