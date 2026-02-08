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


def build_object_pair_sequence(
    object_names: list[str],
    run_count: int,
    intermission_every: int,
    none_before_after: bool,
    animatronic_obj: str | None,
    random_seed: int | None,
) -> list[tuple[str, str]]:
    pairs = [(a, b) for a in object_names for b in object_names if a != b]
    if not pairs:
        return []

    base = run_count // len(pairs)
    remainder = run_count % len(pairs)
    counts = {pair: 0 for pair in pairs}
    sequence: list[tuple[str, str]] = []
    rng = random.Random(random_seed)

    def can_use(pair: tuple[str, str], remaining_runs_after: int) -> bool:
        new_count = counts[pair] + 1
        if new_count > base + 1:
            return False

        extra_used = 0
        for count in counts.values():
            if count > base:
                extra_used += count - base
        if counts[pair] >= base:
            extra_used += 1
        if extra_used > remainder:
            return False

        required_min = 0
        for key, count in counts.items():
            if key == pair:
                count = new_count
            if count < base:
                required_min += base - count
        if required_min > remaining_runs_after:
            return False

        extra_needed = remainder - extra_used
        available_slots = remaining_runs_after - required_min
        if available_slots < extra_needed:
            return False

        return True

    def prefer_animatronic(pair: tuple[str, str], run_number: int) -> int:
        if not none_before_after or not animatronic_obj or intermission_every <= 0:
            return 0
        if run_number % intermission_every == 0 and run_number != run_count:
            return 1 if pair[0] == animatronic_obj else 0
        if run_number % intermission_every == 1 and run_number != 1:
            return 1 if pair[1] == animatronic_obj else 0
        return 0

    def backtrack(run_index: int, last_pair: tuple[str, str] | None) -> bool:
        if run_index == run_count:
            return True

        run_number = run_index + 1
        remaining_runs_after = run_count - run_number

        candidates = [
            pair
            for pair in pairs
            if counts[pair] < base + 1
            and (
                last_pair is None
                or (
                    pair[0] != last_pair[0]
                    and pair[1] != last_pair[1]
                    and not (pair[0] == last_pair[1] and pair[1] == last_pair[0])
                )
            )
        ]
        rng.shuffle(candidates)
        candidates.sort(
            key=lambda pair: (counts[pair], -prefer_animatronic(pair, run_number))
        )

        for pair in candidates:
            if not can_use(pair, remaining_runs_after):
                continue
            counts[pair] += 1
            sequence.append(pair)
            if backtrack(run_index + 1, pair):
                return True
            sequence.pop()
            counts[pair] -= 1

        return False

    if not backtrack(0, None):
        raise RuntimeError("No valid object pairing sequence found.")

    return sequence


def build_rows(config: dict) -> tuple[list[dict], dict[str, list[dict]], list[str]]:
    show = config["show"]
    characters = config["characters"]
    objects = config["objects"]
    all_performers = config.get("performers", [])

    for obj in objects:
        if obj.get("performers") == ["all"]:
            obj["performers"] = all_performers.copy()

    run_count = int(show["run_count"])
    step_minutes = int(show["step_minutes"])
    intermission = show.get("intermission", {})
    intermission_every = int(intermission.get("every_n_runs", 0) or 0)
    intermission_length = int(intermission.get("length_minutes", 0) or 0)
    none_before_after = intermission.get("none_before_after", False)

    random_seed = show.get("random_seed")
    if random_seed is not None:
        random.seed(random_seed)

    object_performers: dict[str, list[str]] = {}
    animatronic_perm = None
    animatronic_obj = None
    for obj in objects:
        obj_name = obj["name"]
        available_performers = obj.get("performers", ["None"])
        object_performers[obj_name] = available_performers
        if obj_name == "Animatronic" and "None" in available_performers:
            animatronic_perm = (obj_name, "None")
            animatronic_obj = obj_name

    start_time = parse_time(show["start_time"])
    current_time = start_time

    object_names = [obj["name"] for obj in objects]

    performer_rows: dict[str, list[dict]] = {
        name: [] for name in all_performers if name != "None"
    }

    master_rows: list[dict] = []
    rules = RulesEngine(all_performers, object_names, run_count)
    last_intermission_pair_performer = None
    object_pair_sequence = build_object_pair_sequence(
        object_names,
        run_count,
        intermission_every,
        none_before_after,
        animatronic_obj,
        random_seed,
    )

    for run_index, (domin_obj, alquist_obj) in enumerate(object_pair_sequence):
        run_number = run_index + 1
        run_label = str(run_number)
        run_time = format_time(current_time)

        row: dict[str, str] = {"Run": run_label, "Time": run_time}

        is_after_intermission = (
            intermission_every > 0
            and run_number % intermission_every == 1
            and run_number != 1
        )

        domin_candidates = [
            (domin_obj, performer)
            for performer in object_performers.get(domin_obj, ["None"])
        ]
        alquist_candidates = [
            (alquist_obj, performer)
            for performer in object_performers.get(alquist_obj, ["None"])
        ]

        best_score = None
        best_pair = None

        for domin_candidate in domin_candidates:
            if not rules.rule3_no_same_object_consecutive_runs("Domin", domin_candidate[0]):
                continue
            if not rules.rule4_consecutive_object_same_performer("Domin", domin_candidate):
                continue

            for alquist_candidate in alquist_candidates:
                if not rules.rule3_no_same_object_consecutive_runs("Alquist", alquist_candidate[0]):
                    continue
                if not rules.rule4_consecutive_object_same_performer("Alquist", alquist_candidate):
                    continue
                if not rules.rule1_no_same_performer_both_positions(
                    domin_candidate, alquist_candidate
                ):
                    continue
                if not rules.rule2_no_same_object_both_positions(
                    domin_candidate, alquist_candidate
                ):
                    continue

                score = rules.score_permutation(
                    domin_candidate,
                    alquist_candidate,
                    last_intermission_pair_performer,
                    is_after_intermission,
                    animatronic_perm,
                    run_number,
                )
                if best_score is None or score > best_score:
                    best_score = score
                    best_pair = (domin_candidate, alquist_candidate)

        if best_pair is None:
            raise RuntimeError(
                "No valid performer assignment found without violating hard rules."
            )

        domin_perm, alquist_perm = best_pair
        domin_obj, domin_performer = domin_perm
        alquist_obj, alquist_performer = alquist_perm

        row["Domin"] = domin_obj
        row["DominPerformer"] = domin_performer
        row["Alquist"] = alquist_obj
        row["AlquistPerformer"] = alquist_performer

        rules.record_run(domin_perm, alquist_perm)

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

        if (
            intermission_every
            and run_number % intermission_every == 0
            and run_number != run_count
        ):
            if animatronic_perm:
                if domin_perm == animatronic_perm:
                    last_intermission_pair_performer = alquist_performer
                elif alquist_perm == animatronic_perm:
                    last_intermission_pair_performer = domin_performer
                else:
                    last_intermission_pair_performer = None

        if (
            intermission_every
            and intermission_length
            and run_number % intermission_every == 0
            and run_number != run_count
        ):
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
