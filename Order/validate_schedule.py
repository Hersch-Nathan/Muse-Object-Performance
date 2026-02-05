#!/usr/bin/env python3
"""Validate the show order schedule against all constraint rules."""

import csv


def validate_schedule(filename: str) -> bool:
    """Validate schedule against all hard and soft rules."""
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r['Run'] != 'Intermission']
    
    violations = {
        'consecutive': [],
        'duplicate_perm': [],
        'duplicate_object': []
    }
    
    print("=" * 70)
    print("SCHEDULE VALIDATION REPORT")
    print("=" * 70)
    
    # Rule 1: Check consecutive same permutation
    for i in range(len(rows) - 1):
        curr = rows[i]
        next_row = rows[i + 1]
        
        domin_curr = (curr['Domin'], curr['DominPerformer'])
        domin_next = (next_row['Domin'], next_row['DominPerformer'])
        alquist_curr = (curr['Alquist'], curr['AlquistPerformer'])
        alquist_next = (next_row['Alquist'], next_row['AlquistPerformer'])
        
        if domin_curr == domin_next:
            violations['consecutive'].append(
                f"Runs {curr['Run']}-{next_row['Run']}: Domin {domin_curr}"
            )
        if alquist_curr == alquist_next:
            violations['consecutive'].append(
                f"Runs {curr['Run']}-{next_row['Run']}: Alquist {alquist_curr}"
            )
    
    # Rule 2 & 3: Check same permutation/object in both positions
    for row in rows:
        domin_perm = (row['Domin'], row['DominPerformer'])
        alquist_perm = (row['Alquist'], row['AlquistPerformer'])
        domin_obj = row['Domin']
        alquist_obj = row['Alquist']
        
        if domin_perm == alquist_perm:
            violations['duplicate_perm'].append(
                f"Run {row['Run']}: Both positions have {domin_perm}"
            )
        if domin_obj == alquist_obj:
            violations['duplicate_object'].append(
                f"Run {row['Run']}: Both positions have object '{domin_obj}'"
            )
    
    # Print results
    print(f"\nTotal Runs: {len(rows)}")
    print(f"\nRule 1 (No consecutive same permutation): {len(violations['consecutive'])} violations")
    if violations['consecutive']:
        for v in violations['consecutive']:
            print(f"  ❌ {v}")
    else:
        print("  ✅ PASS")
    
    print(f"\nRule 2 (No duplicate permutation in run): {len(violations['duplicate_perm'])} violations")
    if violations['duplicate_perm']:
        for v in violations['duplicate_perm']:
            print(f"  ❌ {v}")
    else:
        print("  ✅ PASS")
    
    print(f"\nRule 3 (No duplicate object in run): {len(violations['duplicate_object'])} violations")
    if violations['duplicate_object']:
        for v in violations['duplicate_object']:
            print(f"  ❌ {v}")
    else:
        print("  ✅ PASS")
    
    total_violations = sum(len(v) for v in violations.values())
    print("\n" + "=" * 70)
    if total_violations == 0:
        print("✅ ALL RULES PASSED - Schedule is valid!")
    else:
        print(f"❌ {total_violations} total violations found")
    print("=" * 70)
    
    return total_violations == 0


if __name__ == "__main__":
    validate_schedule('show_order.csv')
