# Tech/Show Week Schedule

This folder generates a single DRAFT PDF schedule for tech/show week.

It uses the existing Order generator (`../generate_schedule.py`) and reads
`../show_order.csv` for the Order 12 run sequence shown on Tuesday-Thursday pages.

## Outputs

- `general_show_order.csv`
- `days/*_timeline.csv`
- `days/*_runs.csv`
- `performers/moose.csv`
- `performers/luca.csv`
- `tech_show_week.pdf`

## Build

From this folder:

```bash
python3 generate_tech_week_schedule.py
pdflatex -interaction=nonstopmode tech_show_week.tex
```

Run `pdflatex` a second time if table layout references need another pass.
