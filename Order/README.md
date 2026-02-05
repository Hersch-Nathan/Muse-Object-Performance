# Show Order Generator

This directory contains tools for generating performance schedules for the show.

## Files

- `config.yaml` - Configuration file with show settings, characters, performers, and objects
- `generate_schedule.py` - Python script that generates CSV schedules from config
- `show_order.csv` - Master schedule showing all runs with object-performer assignments
- `show_order.tex` - LaTeX document that imports CSVs and generates the PDF
- `show_order.pdf` - Final PDF output with master schedule and per-performer schedules
- `performers/` - Directory containing individual CSV schedules for each performer

## Quick Start

To regenerate all schedules and the PDF:

```bash
python3 generate_schedule.py && pdflatex -interaction=nonstopmode show_order.tex
```

## Configuration

Edit `config.yaml` to customize:

### Show Settings
- `name` - Show name displayed in PDF
- `start_time` - First run start time (e.g., "7:00 PM")
- `run_count` - Total number of performance runs
- `step_minutes` - Minutes between each run (e.g., 15)
- `random_seed` - Set to a number for reproducible random permutation order, or `null` for sequential

### Intermission Settings
- `every_n_runs` - Insert intermission after this many runs (e.g., 6)
- `length_minutes` - Intermission duration in minutes
- `none_before_after` - If `true`, forces Animatronic (None performer) on one position before intermission and the other position after intermission to give performers a break

### Characters
Define timing offsets for when each character appears/exits during a run:
- `offset_start_min` - Minutes from run start when character enters
- `offset_end_min` - Minutes from run start when character exits

### Performers
List of all performers (e.g., ["Moose", "Luca"])

### Objects
Define objects and their allowed performers:
- `performers: ["all"]` - Any performer can play this object
- `performers: ["Performer1", "Performer2"]` - Only specific performers
- `performers: ["None"]` - No performer needed (e.g., Animatronic)

## How It Works

1. **Permutation Pool** - The generator creates all valid (object, performer) pairs
2. **Cycling** - Domin and Alquist positions cycle through the permutation pool with an offset
3. **Balanced Assignment** - Each permutation appears once before repeating
4. **Intermission Breaks** - When `none_before_after: true`, one position gets Animatronic before intermission and the other position after intermission, ensuring different performers get breaks

## Output Files

- **Master Schedule** (`show_order.csv`) - Shows all runs with both character positions
- **Performer Schedules** (`performers/*.csv`) - Individual schedules showing when each performer is on/off with character timing windows
- **PDF** (`show_order.pdf`) - Complete formatted document with all schedules

## Example

With 4 objects (Shirt, Muppet, Animatronic, Robot) and 2 performers (Moose, Luca):
- Each run assigns one object-performer pair to Domin
- Each run assigns one object-performer pair to Alquist (offset by 1)
- Objects rotate through both positions
- Performers are balanced across all appearances
- Intermission breaks alternate: Domin gets Animatronic before intermission, Alquist gets Animatronic after

## Requirements

- Python 3 with `pyyaml` package: `pip install pyyaml`
- LaTeX with `datatool`, `longtable`, and `geometry` packages
