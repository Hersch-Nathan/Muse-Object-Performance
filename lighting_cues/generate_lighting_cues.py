import csv
import os

try:
    import yaml
except ImportError as exc:  # pragma: no cover - runtime dependency message
    raise SystemExit(
        "Missing dependency: pyyaml. Install with 'pip install pyyaml'."
    ) from exc


HEADERS = ["Q", "Name", "Intensity Pallet", "Color Pallet"]


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def format_q_name(label: str, cue_type: str) -> str:
    return f"{label} {cue_type}".strip()


def format_double_name(label: str, cue_type: str) -> str:
    name = cue_type.replace("A+B", label).strip()
    return " ".join(name.split())


def normalize_cue_type(value: str) -> str:
    return " ".join(value.split())


def format_q_number(base: int, index: int) -> str:
    return f"{base}{index:02d}"


def parse_q_number(value: str) -> tuple[int, int]:
    if "." in value:
        main, suffix = value.split(".", 1)
        return int(main), int(suffix or 0)
    return int(value), 0


def object_pairs(objects: list[str]) -> list[tuple[str, str]]:
    pairs = []
    for first in objects:
        for second in objects:
            if first == second:
                continue
            pairs.append((first, second))
    return pairs


def build_rows(config: dict) -> list[dict]:
    objects = config["objects"]
    cue_types = config["cue_types"]
    numbering = config["numbering"]
    bump_types = set(config.get("bump_types", []))

    rows: list[dict] = []

    index = 1
    for cue_type in cue_types["general"]:
        cue_type = normalize_cue_type(cue_type)
        q_number = format_q_number(numbering["general_base"], index)
        rows.append(
            {
                "Q Number": q_number,
                "Name": format_q_name("General", cue_type),
                "Intensity Pallet": "",
                "Color Pallet": "",
                "_q_number": q_number,
            }
        )
        if cue_type in bump_types:
            rows.append(
                {
                    "Q Number": f"{q_number}.1",
                    "Name": format_q_name("General", "Bump Return"),
                    "Intensity Pallet": "",
                    "Color Pallet": "",
                    "_q_number": f"{q_number}.1",
                }
            )
        index += 1

    for obj in objects:
        index = 1
        base = numbering["single_bases"][obj]
        for cue_type in cue_types["single"]:
            cue_type = normalize_cue_type(cue_type)
            q_number = format_q_number(base, index)
            rows.append(
                {
                    "Q Number": q_number,
                    "Name": format_q_name(obj, cue_type),
                    "Intensity Pallet": "",
                    "Color Pallet": "",
                    "_q_number": q_number,
                }
            )
            if cue_type in bump_types:
                rows.append(
                    {
                        "Q Number": f"{q_number}.1",
                        "Name": format_q_name(obj, "Bump Return"),
                        "Intensity Pallet": "",
                        "Color Pallet": "",
                        "_q_number": f"{q_number}.1",
                    }
                )
            index += 1

    double_types = [normalize_cue_type(value) for value in cue_types["double"]]
    object_index = {obj: idx for idx, obj in enumerate(objects)}

    for first, second in object_pairs(objects):
        base = numbering["double_bases"][first]
        label = f"{first}+{second}"
        second_candidates = [obj for obj in objects if obj != first]
        group_index = second_candidates.index(second) + 1
        for cue_index, cue_type in enumerate(double_types, start=1):
            q_number = f"{base}{group_index}{cue_index}"
            rows.append(
                {
                    "Q Number": q_number,
                    "Name": format_double_name(label, cue_type),
                    "Intensity Pallet": "",
                    "Color Pallet": "",
                    "_q_number": q_number,
                }
            )
            if cue_type in bump_types:
                rows.append(
                    {
                        "Q Number": f"{q_number}.1",
                        "Name": format_q_name(label, "Bump Return"),
                        "Intensity Pallet": "",
                        "Color Pallet": "",
                        "_q_number": f"{q_number}.1",
                    }
                )

    rows.sort(key=lambda row: parse_q_number(row["_q_number"]))
    for row in rows:
        row.pop("_q_number", None)

    return rows


def write_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.yaml")
    config = load_config(config_path)
    output_csv = os.path.join(base_dir, config.get("output_csv", "lighting_cues.csv"))

    rows = build_rows(config)
    write_csv(output_csv, rows)


if __name__ == "__main__":
    main()
