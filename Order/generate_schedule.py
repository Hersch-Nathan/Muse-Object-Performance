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


def validate_permutation(perm, position, run_history, other_position_perm=None):
    """
    Validate if a permutation can be used at this position.
    Returns (is_valid, gap_score) where gap_score is used for preference ranking.
    
    Hard Rules (must pass):
    1. Same permutation cannot appear consecutively in same position
    2. Same permutation cannot appear in both positions in same run
    3. Same object cannot appear in both positions in same run
    
    Soft Rules (affects gap_score):
    5. Prefer gap >= 2 between same permutation in same position
    """
    obj, performer = perm
    
    # Rule 2: Check if same permutation already used in other position this run
    if other_position_perm and other_position_perm == perm:
        return False, -1000
    
    # Rule 3: Check if same object already used in other position this run
    if other_position_perm:
        other_obj, _ = other_position_perm
        if obj == other_obj:
            return False, -1000
    
    # Rule 1: Check for consecutive same permutation in same position
    position_history = [entry[position] for entry in run_history]
    if position_history and position_history[-1] == perm:
        return False, -1000  # Hard violation
    
    # Rule 5: Calculate gap score (prefer larger gaps)
    gap_score = 0
    for i in range(len(position_history) - 1, -1, -1):
        if position_history[i] == perm:
            gap = len(position_history) - 1 - i
            if gap >= 2:
                gap_score = 100  # Good gap
            elif gap == 1:
                gap_score = 50   # Acceptable gap
            # gap == 0 would be consecutive, already rejected above
            break
    else:
        gap_score = 100  # Never used in this position, best score
    
    return True, gap_score


def select_best_permutation(available_perms, position, run_history, other_position_perm=None):
    """
    Select the best permutation from available options based on constraints.
    Returns (best_perm, index_in_available) or (None, -1) if no valid option.
    """
    valid_options = []
    
    for idx, perm in enumerate(available_perms):
        is_valid, gap_score = validate_permutation(perm, position, run_history, other_position_perm)
        if is_valid:
            valid_options.append((perm, idx, gap_score))
    
    if not valid_options:
        return None, -1
    
    # Sort by gap_score (descending) to prefer better gaps
    valid_options.sort(key=lambda x: x[2], reverse=True)
    best_perm, best_idx, _ = valid_options[0]
    
    return best_perm, best_idx


def build_rows(config: dict) -> tuple[list[dict], dict[str, list[dict]], list[str]]:
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

    # Build base permutation pool: all valid (object, performer) pairs
    base_permutation_pool = []
    animatronic_perm = None
    for obj in objects:
        obj_name = obj["name"]
        available_performers = obj.get("performers", ["None"])
        for performer in available_performers:
            perm = (obj_name, performer)
            base_permutation_pool.append(perm)
            # Track Animatronic permutation for intermission breaks
            if obj_name == "Animatronic" and performer == "None":
                animatronic_perm = perm

    start_time = parse_time(show["start_time"])
    current_time = start_time

    performer_rows: dict[str, list[dict]] = {
        name: [] for name in all_performers if name != "None"
    }

    master_rows: list[dict] = []
    
    # Track run history for constraint validation: list of {"Domin": perm, "Alquist": perm}
    run_history = []

    # Calculate segments based on intermission_every
    if intermission_every > 0:
        num_segments = (run_count + intermission_every - 1) // intermission_every
    else:
        num_segments = 1
    
    # Process runs in segments
    for segment_index in range(num_segments):
        # Calculate runs in this segment
        segment_start = segment_index * intermission_every if intermission_every > 0 else 0
        segment_end = min(segment_start + intermission_every, run_count) if intermission_every > 0 else run_count
        
        # Create a fresh shuffle for this segment
        segment_pool = base_permutation_pool.copy()
        if random_seed is not None:
            # Use segment index to vary the shuffle per segment
            random.seed(random_seed + segment_index)
            random.shuffle(segment_pool)
        
        # Create circular iterator lists for each position
        domin_pool = segment_pool.copy()
        alquist_pool = segment_pool.copy()
        # Maintain offset: Alquist starts 1 position ahead
        if len(alquist_pool) > 1:
            alquist_pool = alquist_pool[1:] + alquist_pool[:1]
        
        domin_idx = 0
        alquist_idx = 0
        
        for run_index in range(segment_start, segment_end):
            run_number = run_index + 1
            run_label = str(run_number)
            run_time = format_time(current_time)

            row: dict[str, str] = {"Run": run_label, "Time": run_time}

            # Determine if we should try to force Animatronic for intermission breaks
            try_force_domin_none = False
            try_force_alquist_none = False
            if none_before_after and intermission_every > 0 and animatronic_perm:
                # Run before intermission: try Domin = Animatronic
                if run_number % intermission_every == 0 and run_number != run_count:
                    try_force_domin_none = True
                # Run after intermission: try Alquist = Animatronic
                elif run_number % intermission_every == 1 and run_number != 1:
                    try_force_alquist_none = True

            domin_perm = None
            alquist_perm = None

            # Process Domin first
            if try_force_domin_none:
                # Try to use Animatronic if it passes constraints
                is_valid, _ = validate_permutation(animatronic_perm, "Domin", run_history, None)
                if is_valid:
                    domin_perm = animatronic_perm
            
            if not domin_perm:
                # Search for valid permutation in domin_pool
                attempts = 0
                max_attempts = len(domin_pool) * 2  # Allow wraparound
                while attempts < max_attempts:
                    candidate = domin_pool[domin_idx % len(domin_pool)]
                    is_valid, _ = validate_permutation(candidate, "Domin", run_history, None)
                    if is_valid:
                        domin_perm = candidate
                        break
                    domin_idx += 1
                    attempts += 1
                
                if not domin_perm:
                    # Fallback: use current position anyway (should not happen with valid config)
                    domin_perm = domin_pool[domin_idx % len(domin_pool)]
            
            # Process Alquist
            if try_force_alquist_none and not try_force_domin_none:  # Don't force both
                # Try to use Animatronic if it passes constraints
                is_valid, _ = validate_permutation(animatronic_perm, "Alquist", run_history, domin_perm)
                if is_valid:
                    alquist_perm = animatronic_perm
            
            if not alquist_perm:
                # Search for valid permutation in alquist_pool
                attempts = 0
                max_attempts = len(alquist_pool) * 2
                while attempts < max_attempts:
                    candidate = alquist_pool[alquist_idx % len(alquist_pool)]
                    is_valid, _ = validate_permutation(candidate, "Alquist", run_history, domin_perm)
                    if is_valid:
                        alquist_perm = candidate
                        break
                    alquist_idx += 1
                    attempts += 1
                
                if not alquist_perm:
                    # Fallback: use current position anyway
                    alquist_perm = alquist_pool[alquist_idx % len(alquist_pool)]
            
            # Store selections
            domin_obj, domin_performer = domin_perm
            alquist_obj, alquist_performer = alquist_perm
            
            row["Domin"] = domin_obj
            row["DominPerformer"] = domin_performer
            row["Alquist"] = alquist_obj
            row["AlquistPerformer"] = alquist_performer
            
            # Track in run history for future constraint checks
            run_history.append({"Domin": domin_perm, "Alquist": alquist_perm})

            # Add performer schedule entries
            for character in characters:
                char_name = character["name"]
                
                if char_name == "Domin":
                    obj_name = domin_obj
                    performer = domin_performer
                else:  # Alquist
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

            # Advance pool indices for next run (prefer to move forward)
            domin_idx += 1
            alquist_idx += 1

            # Add intermission if this is the last run of the segment (but not the last run overall)
            if (
                intermission_every
                and intermission_length
                and run_number % intermission_every == 0
                and run_number != run_count
            ):
                intermission_time = format_time(current_time)
                intermission_row: dict[str, str] = {"Run": "Intermission", "Time": intermission_time}
                intermission_row["Domin"] = ""
                intermission_row["DominPerformer"] = ""
                intermission_row["Alquist"] = ""
                intermission_row["AlquistPerformer"] = ""
                master_rows.append(intermission_row)
                
                # Add intermission to all performer schedules
                for performer in performer_rows.keys():
                    performer_rows[performer].append(
                        {
                            "Run": "Intermission",
                            "RunStart": intermission_time,
                            "Character": "",
                            "CharacterInTime": "",
                            "CharacterOutTime": "",
                        }
                    )
                
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
