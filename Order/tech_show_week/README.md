# Tech/Show Week Schedule

This folder generates a single DRAFT PDF schedule for tech/show week.

## Outputs

- `general_show_order.csv`
- `week_timeline.csv`
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
