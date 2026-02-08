# Show Order Generator

This directory contains tools for generating performance schedules for the show.

## Files

- `config.yaml` - Configuration file with show settings, characters, performers, and objects
- `generate_schedule.py` - Python script that generates CSV schedules from config with constraint validation
- `show_order.csv` - Master schedule showing all runs with object-performer assignments
- `show_order.tex` - LaTeX document that imports CSVs and generates the PDF
- `show_order.pdf` - Final PDF output with master schedule and per-performer schedules
- `performers/` - Directory containing individual CSV schedules for each performer

## Quick Start

To regenerate all schedules and the PDF:

```bash
python3 generate_schedule.py && pdflatex -interaction=nonstopmode show_order.tex
```

To verify the schedule, inspect show_order.csv and performer schedules after generation.

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

### Object Pair Sequencing
- Build a full sequence of ordered object pairs (Domin object, Alquist object)
- Enforce even distribution across the full schedule and avoid consecutive repeats or full swaps
- After object pairs are fixed, assign performers using hard rules and soft scoring

### Constraint-Based Assignment
The scheduling algorithm respects the following rules:

**Hard Rules (Must Never Violate):**
1. **No Same Performer in Both Positions** - A performer cannot appear in both Domin and Alquist in the same run
2. **No Same Object in Both Positions** - An object cannot appear in both Domin and Alquist in the same run
3. **No Same Object in Same Position Across Consecutive Runs** - The same object cannot appear in the same position in back-to-back runs
4. **Consecutive Object Switch Keeps Performer** - If an object switches positions between consecutive runs, the performer must stay the same
5. **Object Pairing Distribution** - Ordered object pairs (Domin object, Alquist object) are distributed as evenly as possible across the full schedule
6. **No Full Object Swap Across Consecutive Runs** - If Run N has Domin=A and Alquist=B, Run N+1 cannot be Domin=B and Alquist=A

**Soft Rules (Preferred):**
7. **Performer Balance** - Keep each performer balanced across Domin and Alquist and across objects
8. **Intermission Partner Variety** - When Animatronic appears before and after intermission, prefer a different paired performer across the boundary
9. **Gap Preference** - Prefer a gap of at least 2 runs between the same permutation in the same position. If impossible, allow a gap of 1. Consecutive assignments only allowed when absolutely necessary (but hard rules prevent this). Intermission rows do not count as runs when calculating gaps.
10. **Intermission Breaks** - Try to place Animatronic at intermission boundaries (before and after). If constraints prevent placing both, try at least one. Falls back gracefully if neither is possible.
11. **Avoid None on First/Last Run** - Prefer runs 1 and R to use real performers (no "None")

### Algorithm
For each run:
1. Try to satisfy intermission break requirements (if configured)
2. Search through available permutations to find valid options that pass all hard rules
3. Score valid options by gap preference (higher score for larger gaps)
4. Select the highest-scoring permutation
5. Track assignment in run history for future constraint checks

## Output Files

- **Master Schedule** (`show_order.csv`) - Shows all runs with both character positions
- **Performer Schedules** (`performers/*.csv`) - Individual schedules showing when each performer is on/off with character timing windows
- **PDF** (`show_order.pdf`) - Complete formatted document with all schedules

## Example

With 4 objects (Shirt, Muppet, Animatronic, Robot) and 2 performers (Moose, Luca):

**Segment 1 (Runs 1-6):**
- Runs cycle through permutation pool independently
- Run 5: Animatronic appears in Domin position
- Run 6: Different objects in both positions (Robot vs Shirt)

**Intermission (Run 6-7 boundary):**
- If `none_before_after: true`, Run 7 has Animatronic in Alquist position

**Segment 2 (Runs 7-12):**
- Fresh permutation shuffle (different order than Segment 1)
- Maintains same constraint rules and offset cycling

**Validation:**
- No permutation repeats consecutively in same position
- No object appears in both positions in same run
- All rules satisfied automatically by constraint-based algorithm

## Requirements

- Python 3 with `pyyaml` package: `pip install pyyaml`
- LaTeX with `datatool`, `longtable`, and `geometry` packages

## Troubleshooting

**Schedule Not Meeting Constraints:**
- Run `python3 validate_schedule.py` to check for violations
- If violations exist, the configuration may be over-constrained
- Try adjusting: increasing `run_count`, reducing `intermission_every`, or adding more objects/performers

**PDF Not Compiling:**
- Ensure LaTeX is installed: `which pdflatex`
- Check that all CSV files were generated: `ls performers/*.csv show_order.csv`
- Try recompiling: `pdflatex -interaction=nonstopmode show_order.tex`

**Reproducible Schedules:**
- Set `random_seed` to a specific number in `config.yaml` for consistent results across runs
- Use `null` for different permutation orders each time
