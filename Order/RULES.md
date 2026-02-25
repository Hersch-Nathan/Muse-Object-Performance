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
- Example: Run 2 has Shirt,Luca AND Muppet,Luca
- Applies to: Every run

**Rule 2: No Same Object in Both Positions**
- An object cannot appear in both Domin AND Alquist in the same run
- Example: Run with Shirt,Moose AND Shirt,Luca
- Applies to: Every run

**Rule 3: No Same Object in Same Position Across Consecutive Runs**
- Same object cannot appear in same position (Domin or Alquist) in back-to-back runs
- Example: Run 1 Domin=Shirt, Run 2 Domin=Shirt
- Applies to: All consecutive run pairs

**Rule 4: Consecutive Object Switch Keeps Performer**
- If an object appears in consecutive runs but switches positions, the performer must stay the same
- Example: Run N Alquist=Shirt,Moose → Run N+1 Domin=Shirt,Moose
- Example: Run N Alquist=Shirt,Moose → Run N+1 Domin=Shirt,Luca

**Rule 5: Object Pairing Distribution**
- Count permutations as ordered object pairs (Domin object, Alquist object)
- Let $P = N \times (N - 1)$ where $N$ is the number of objects
- Over the full schedule, each permutation should appear either $\lfloor R/P \rfloor$ or $\lceil R/P \rceil$ times
- Exactly $R \bmod P$ permutations appear $\lceil R/P \rceil$ times
- Example: $N=4 \Rightarrow P=12$, $R=23$ runs → 11 permutations appear 2 times, 1 permutation appears 1 time

**Rule 6: No Full Object Swap Across Consecutive Runs**
- If Run N has Domin=A and Alquist=B, then Run N+1 cannot be Domin=B and Alquist=A

### SOFT RULES (Prefer But Fallback if Needed)

**Rule 7: Performer Balance Across Characters and Objects**
- Performers (excluding "None") should appear about the same number of times
	- as Domin vs Alquist
	- on each object
- Prefer assignments that reduce imbalance over time

**Rule 8: Intermission Partner Variety**
- When Animatronic appears before and after an intermission, the performer paired with it should change
- Prefer a different performer paired against Animatronic across the boundary

**Rule 9: Gap Preference for (Object, Performer) Pairs**
- Gap of 2+ runs: Preferred (best score)
- Gap of 1 run: Acceptable (lower score)
- Gap of 0 (consecutive): Only if no other option exists
- Intermission rows do not count as runs when calculating gaps
- Example: Shirt,Moose in Run 1, can appear again in Run 4+ (gap=2)

**Rule 10: Intermission Breaks (None_Before_After)**
- Try to place Animatronic at intermission boundaries
- Before intermission: One position gets Animatronic
- After intermission: Other position gets Animatronic
- Soft rule: Skip if hard rules would be violated

**Rule 10b: No-Intermission Middle Boundary (None_Before_After)**
- If no actual intermission boundary occurs in the schedule, treat the two middle runs as a virtual boundary
- For odd run counts, use runs $(\lfloor R/2 \rfloor + 1)$ and $(\lfloor R/2 \rfloor + 2)$ (example: $R=9 \Rightarrow 5,6$)
- For even run counts, use the central pair (example: $R=8 \Rightarrow 4,5$)
- Apply the same boundary pattern: first middle run prefers Animatronic in Domin, second middle run prefers Animatronic in Alquist

**Rule 10c: Animatronic Spacing Around Virtual Boundary**
- When using the virtual middle boundary, avoid placing Animatronic on runs directly adjacent to those two middle runs
- Prefer larger gaps between additional Animatronic appearances to avoid clustering

**Rule 11: Avoid None on First/Last Run**
- Prefer runs 1 and $R$ to use real performers (no "None")

**Rule 12: Prefer Non-Animatronic Opening Run**
- Soft preference: avoid starting the show with Animatronic in run 1 when alternatives satisfy hard rules

**Rule 13: Consecutive Animatronic Partner Must Switch**
- If two consecutive runs both include Animatronic, the non-Animatronic object must be performed by different performers across those two runs
- Example target: run 5 pairs with Luca, run 6 pairs with Moose

**Rule 14: Continue Animatronic Partner Rotation**
- After the consecutive Animatronic pair, prefer alternating the paired performer on future Animatronic runs

## Implementation Order

User will specify the order to implement rules 1-8 in generate_schedule.py

