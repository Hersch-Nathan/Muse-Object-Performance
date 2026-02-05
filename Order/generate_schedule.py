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

    # Handle random seed
    random_seed = show.get("random_seed")
    if random_seed is not None:
        random.seed(random_seed)
        initial_object_index = random.randint(0, len(objects) - 1)
    else:
        initial_object_index = 0

    start_time = parse_time(show["start_time"])
    current_time = start_time

    performer_rows: dict[str, list[dict]] = {
        name: [] for name in all_performers if name != "None"
    }

    # Track performer usage counts (excluding None)
    performer_counts: dict[str, int] = {
        name: 0 for name in all_performers if name != "None"
    }

    master_rows: list[dict] = []

    for run_index in range(run_count):
        run_number = run_index + 1
        run_label = str(run_number)
        run_time = format_time(current_time)

        row: dict[str, str] = {"Run": run_label, "Time": run_time}

        for char_index, character in enumerate(characters):
            char_name = character["name"]
            obj_index = (initial_object_index + run_index + char_index) % len(objects)
            obj = objects[obj_index]
            obj_name = obj["name"]
            
            # Get available performers for this object
            available_performers = obj.get("performers", ["None"])
            
            # Choose performer with fewest appearances (balanced assignment)
            if "None" in available_performers:
                performer = "None"
            else:
                # Filter to real performers and find the one with minimum count
                valid_performers = [p for p in available_performers if p in performer_counts]
                if valid_performers:
                    performer = min(valid_performers, key=lambda p: performer_counts[p])
                    performer_counts[performer] += 1
                else:
                    performer = "None"

            row[char_name] = obj_name
            row[f"{char_name}Performer"] = performer

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

        if (
            intermission_every
            and intermission_length
            and run_number % intermission_every == 0
            and run_number != run_count
        ):
            intermission_time = format_time(current_time)
            intermission_row: dict[str, str] = {"Run": "Intermission", "Time": intermission_time}
            for character in characters:
                char_name = character["name"]
                intermission_row[char_name] = ""
                intermission_row[f"{char_name}Performer"] = ""
            master_rows.append(intermission_row)
            current_time += timedelta(minutes=intermission_length)

    headers = ["Run", "Time"]
    for character in characters:
        char_name = character["name"]
        headers.append(char_name)
        headers.append(f"{char_name}Performer")

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
