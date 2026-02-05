import csv
import os
import random
from datetime import datetime, timedelta

try:
    import yaml
except ImportError as exc:  # pragma: no cover - runtime dependency message
    raise SystemExit(
        "Missing dependency: pyyaml. Install with 'pip install pyyaml'."
    ) from exc

from rules_engine import RulesEngine


TIME_FORMATS = ["%I:%M %p", "%I %p", "%H:%M"]


def parse_time(value: str) -> datetime:
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Unsupported time format: {value}")


def format_time(value: datetime) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def sanitize_filename(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in value.strip().lower())
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_") or "performer"


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ensure_output_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def build_rows(config: dict) -> tuple[list[dict], dict[str, list[dict]], list[str]]:
    """
    Build master and performer schedules using RulesEngine for constraint validation.
    
    Uses 5 rules:
    - Hard Rule 1: No same performer in both positions in same run
    - Hard Rule 2: No same object in both positions in same run
    - Hard Rule 3: No same object in same position across consecutive runs
    - Soft Rule 4: Prefer gap of 2+ between same (object, performer) pair
    - Soft Rule 5: Try to place Animatronic at intermission boundaries
    """
    show = config["show"]
    characters = config["characters"]
    objects = config["objects"]
    all_performers = config.get("performers", [])

    # Expand "all" in object performers
    for obj in objects:
        if obj.get("performers") == ["all"]:
            obj["performers"] = all_performers.copy()

    run_count = int(show["run_count"])
    step_minutes = int(show["step_minutes"])
    intermission = show.get("intermission", {})
    intermission_every = int(intermission.get("every_n_runs", 0) or 0)
    intermission_length = int(intermission.get("length_minutes", 0) or 0)
    none_before_after = intermission.get("none_before_after", False)

    # Handle random seed
    random_seed = show.get("random_seed")
    if random_seed is not None:
        random.seed(random_seed)

    # Build base permutation pool
    base_permutation_pool = []
    animatronic_perm = None
    for obj in objects:
        obj_name = obj["name"]
        available_performers = obj.get("performers", ["None"])
        for performer in available_performers:
            perm = (obj_name, performer)
            base_permutation_pool.append(perm)
            if obj_name == "Animatronic" and performer == "None":
                animatronic_perm = perm

    start_time = parse_time(show["start_time"])
    current_time = start_time

    performer_rows: dict[str, list[dict]] = {
        name: [] for name in all_performers if name != "None"
    }

    master_rows: list[dict] = []
    rules = RulesEngine()

    # Calculate segments
    if intermission_every > 0:
        num_segments = (run_count + intermission_every - 1) // intermission_every
    else:
        num_segments = 1
    
    # Process runs in segments
    for segment_index in range(num_segments):
        segment_start = segment_index * intermission_every if intermission_every > 0 else 0
        segment_end = min(segment_start + intermission_every, run_count) if intermission_every > 0 else run_count
        
        # Fresh shuffle per segment
        segment_pool = base_permutation_pool.copy()
        if random_seed is not None:
            random.seed(random_seed + segment_index)
            random.shuffle(segment_pool)
        
        # Reset rules engine for new segment
        rules.reset()
        
        # Create pool iterators
        domin_pool = segment_pool.copy()
        alquist_pool = segment_pool.copy()
        if len(alquist_pool) > 1:
            alquist_pool = alquist_pool[1:] + alquist_pool[:1]
        
        domin_idx = 0
        alquist_idx = 0
        
        for run_index in range(segment_start, segment_end):
            run_number = run_index + 1
            run_label = str(run_number)
            run_time = format_time(current_time)

            row: dict[str, str] = {"Run": run_label, "Time": run_time}

            # Rule 5: Try to place Animatronic at intermission boundaries
            try_force_domin_none = False
            try_force_alquist_none = False
            if none_before_after and intermission_every > 0 and animatronic_perm:
                if run_number % intermission_every == 0 and run_number != run_count:
                    try_force_domin_none = True
                elif run_number % intermission_every == 1 and run_number != 1:
                    try_force_alquist_none = True

            domin_perm = None
            alquist_perm = None

            # Find Domin permutation
            if try_force_domin_none:
                # Try forced Animatronic first
                if rules.rule3_no_same_object_consecutive_runs("Domin", "Animatronic"):
                    domin_perm = animatronic_perm
            
            if not domin_perm:
                # Search pool for valid permutation
                attempts = 0
                max_attempts = len(domin_pool) * 2
                while attempts < max_attempts:
                    candidate = domin_pool[domin_idx % len(domin_pool)]
                    if rules.rule3_no_same_object_consecutive_runs("Domin", candidate[0]):
                        domin_perm = candidate
                        break
                    domin_idx += 1
                    attempts += 1
                
                if not domin_perm:
                    domin_perm = domin_pool[domin_idx % len(domin_pool)]

            # Find Alquist permutation
            if try_force_alquist_none and not try_force_domin_none:
                if rules.rule3_no_same_object_consecutive_runs("Alquist", "Animatronic"):
                    # Check hard rules with Domin
                    if (rules.rule1_no_same_performer_both_positions(domin_perm, animatronic_perm) and
                        rules.rule2_no_same_object_both_positions(domin_perm, animatronic_perm)):
                        alquist_perm = animatronic_perm
            
            if not alquist_perm:
                # Search pool for valid permutation
                attempts = 0
                max_attempts = len(alquist_pool) * 2
                while attempts < max_attempts:
                    candidate = alquist_pool[alquist_idx % len(alquist_pool)]
                    # Check all hard rules
                    if (rules.rule3_no_same_object_consecutive_runs("Alquist", candidate[0]) and
                        rules.rule1_no_same_performer_both_positions(domin_perm, candidate) and
                        rules.rule2_no_same_object_both_positions(domin_perm, candidate)):
                        alquist_perm = candidate
                        break
                    alquist_idx += 1
                    attempts += 1
                
                if not alquist_perm:
                    alquist_perm = alquist_pool[alquist_idx % len(alquist_pool)]

            # Record in row
            domin_obj, domin_performer = domin_perm
            alquist_obj, alquist_performer = alquist_perm
            
            row["Domin"] = domin_obj
            row["DominPerformer"] = domin_performer
            row["Alquist"] = alquist_obj
            row["AlquistPerformer"] = alquist_performer
            
            # Track in rules engine
            rules.record_run(domin_perm, alquist_perm)

            # Add performer schedule entries
            for character in characters:
                char_name = character["name"]
                
                if char_name == "Domin":
                    obj_name = domin_obj
                    performer = domin_performer
                else:
                    obj_name = alquist_obj
                    performer = alquist_performer

                if performer != "None":
                    performer_rows.setdefault(performer, [])
                    offset_start = int(character.get("offset_start_min", 0))
                    offset_end = int(character.get("offset_end_min", 0))
                    in_time = format_time(current_time + timedelta(minutes=offset_start))
                    out_time = format_time(current_time + timedelta(minutes=offset_end))
                    performer_rows[performer].append(
                        {
                            "Run": run_label,
                            "RunStart": run_time,
                            "Character": char_name,
                            "CharacterInTime": in_time,
                            "CharacterOutTime": out_time,
                        }
                    )

            master_rows.append(row)
            current_time += timedelta(minutes=step_minutes)
            domin_idx += 1
            alquist_idx += 1

            # Add intermission
            if (intermission_every and intermission_length and 
                run_number % intermission_every == 0 and run_number != run_count):
                
                intermission_time = format_time(current_time)
                intermission_row: dict[str, str] = {
                    "Run": "Intermission",
                    "Time": intermission_time,
                    "Domin": "",
                    "DominPerformer": "",
                    "Alquist": "",
                    "AlquistPerformer": "",
                }
                master_rows.append(intermission_row)
                
                for performer in performer_rows.keys():
                    performer_rows[performer].append({
                        "Run": "Intermission",
                        "RunStart": intermission_time,
                        "Character": "",
                        "CharacterInTime": "",
                        "CharacterOutTime": "",
                    })
                
                current_time += timedelta(minutes=intermission_length)

    headers = ["Run", "Time", "Domin", "DominPerformer", "Alquist", "AlquistPerformer"]
    return master_rows, performer_rows, headers


def write_csv(path: str, headers: list[str], rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.yaml")
    output_path = os.path.join(base_dir, "show_order.csv")
    performers_dir = os.path.join(base_dir, "performers")

    config = load_config(config_path)
    master_rows, performer_rows, headers = build_rows(config)

    write_csv(output_path, headers, master_rows)

    ensure_output_dir(performers_dir)
    performer_headers = [
        "Run",
        "RunStart",
        "Character",
        "CharacterInTime",
        "CharacterOutTime",
    ]

    for performer, rows in performer_rows.items():
        filename = f"{sanitize_filename(performer)}.csv"
        write_csv(os.path.join(performers_dir, filename), performer_headers, rows)


if __name__ == "__main__":
    main()
