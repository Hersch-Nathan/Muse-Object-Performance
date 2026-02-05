# Schedule Constraint Rules

This document defines the rules for valid show order scheduling.

## Current Violations in show_order.csv

### Violation 1: Repeating Objects Across Runs
- **Runs 1-2:** Both runs have Shirt,Muppet pattern (Shirt vs Muppet in same sequence)
- **Runs 3-4:** Similar pattern continuation

**Rule Needed:** Objects should not repeat in the same relative positions across consecutive runs

### Violation 2: Repeating Performers Across Objects in Consecutive Runs
- **Run 1:** Shirt,Moose + Muppet,Moose (Moose in both positions)
- **Run 2:** Shirt,Luca + Muppet,Luca (Luca in both positions)
- **Run 1-2:** Same performer (Moose, then Luca) used for both objects

**Rule Needed:** Performers should vary across both objects and positions

### Violation 3: Suboptimal Performer Distribution
- **Runs 4-5:** Alquist has Robot,Moose then Robot,Luca (same object, switching performers)
- **Runs 8, 10, 14, 16, 20, 22:** Alquist has Muppet,Moose repeatedly
- **Runs 10, 16, 22:** Robot,Moose repeating in Alquist

**Rule Needed:** Better distribution of specific (object, performer) pairs to avoid clustering

## Final Ruleset (Confirmed by User)

### HARD RULES (Must Never Violate)

**Rule 1: No Same Performer in Both Positions**
- A performer cannot appear in both Domin AND Alquist in the same run
- Example: ❌ Run 2 has Shirt,Luca AND Muppet,Luca
- Applies to: Every run

**Rule 2: No Same Object in Both Positions**
- An object cannot appear in both Domin AND Alquist in the same run
- Example: ❌ Run with Shirt,Moose AND Shirt,Luca
- Applies to: Every run

**Rule 3: No Same Object in Same Position Across Consecutive Runs**
- Same object cannot appear in same position (Domin or Alquist) in back-to-back runs
- Example: ❌ Run 1 Domin=Shirt, Run 2 Domin=Shirt
- Applies to: All consecutive run pairs

### SOFT RULES (Prefer But Fallback if Needed)

**Rule 4: Gap Preference for (Object, Performer) Pairs**
- Gap of 2+ runs: Preferred (best score)
- Gap of 1 run: Acceptable (lower score)
- Gap of 0 (consecutive): Only if no other option exists
- Example: Shirt,Moose in Run 1, can appear again in Run 4+ (gap=2)

**Rule 5: Intermission Breaks (None_Before_After)**
- Try to place Animatronic at intermission boundaries
- Before intermission: One position gets Animatronic
- After intermission: Other position gets Animatronic
- Soft rule: Skip if hard rules would be violated

## Implementation Order

User will specify the order to implement rules 1-5 in generate_schedule.py

