import csv
import os

try:
    import yaml
except ImportError as exc:  # pragma: no cover - runtime dependency message
    raise SystemExit(
        "Missing dependency: pyyaml. Install with 'pip install pyyaml'."
    ) from exc


EOS_HEADERS = [
    "Q",
    "Name",
    "Intensity Palette Number",
    "Intensity Palette",
    "Color Palette Number",
    "Color Palette",
]

QLAB_HEADERS = ["qlab q", "qlab name", "eos q number", "eos name"]

PERMUTATION_HEADERS = ["Permutation", "Object A", "Object B"]

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def normalize_text(value: str, typo_fixes: dict) -> str:
    for wrong, correct in typo_fixes.items():
        value = value.replace(wrong, correct)
    return " ".join(value.split())


def parse_q_number(value: str) -> tuple[int, int]:
    if "." in value:
        main, suffix = value.split(".", 1)
        return int(main), int(suffix or 0)
    return int(value), 0


def object_pairs(objects: list[str]) -> list[tuple[str, str]]:
    return [(first, second) for first in objects for second in objects if first != second]


def keyword_palette(label: str, keywords: list[dict], default: str) -> str:
    label_lower = label.lower()
    for entry in keywords:
        keyword = entry.get("keyword", "").lower()
        palette = entry.get("palette", "")
        if keyword and palette and keyword in label_lower:
            return palette
    return default


def keyword_cue_type(label: str, entries: list[dict], default: str) -> str:
    label_lower = label.lower()
    for entry in entries:
        keywords = [value.lower() for value in entry.get("keywords", []) if value]
        cue_type = entry.get("cue_type", "")
        if not keywords or not cue_type:
            continue
        if all(keyword in label_lower for keyword in keywords):
            return cue_type
    return default


def palette_number(object_index: int, palette_index: int) -> str:
    return f"{object_index}{palette_index:02d}"


def format_palette_entry(
    objects: list[str],
    palette_name: str,
    palette_index: int,
    object_index_map: dict[str, int],
) -> tuple[str, str]:
    numbers = []
    names = []
    for obj in objects:
        index = object_index_map[obj]
        numbers.append(palette_number(index, palette_index))
        names.append(f"{obj} {palette_name}")
    return " + ".join(numbers), " + ".join(names)


def load_base_cues(path: str, typo_fixes: dict) -> list[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(
                {
                    "Q": row.get("Q", "").strip(),
                    "Name": normalize_text(row.get("Name", ""), typo_fixes),
                    "Look": normalize_text(row.get("Look", ""), typo_fixes),
                }
            )
        return rows


def detect_mode(look: str) -> str:
    look_lower = look.lower()
    if "+" in look:
        return "pairs"
    if "preshow" in look_lower or "blackout" in look_lower:
        return "none"
    return "single"


def resolve_general_q_number(cue_type: str, cue_types: list[str], base: int) -> str:
    index = cue_types.index(cue_type) + 1
    return f"{base}{index:02d}"


def resolve_single_q_number(
    cue_type: str, cue_types: list[str], base: int
) -> str:
    index = cue_types.index(cue_type) + 1
    return f"{base}{index:02d}"


def resolve_double_q_number(
    cue_type: str,
    cue_types: list[str],
    base: int,
    objects: list[str],
    first: str,
    second: str,
) -> str:
    cue_index = cue_types.index(cue_type) + 1
    second_index_map = {obj: idx + 1 for idx, obj in enumerate(objects)}
    return f"{base}{second_index_map[second]}{cue_index}"


def build_eos_rows(config: dict) -> list[dict]:
    objects = config["objects"]
    cue_types = config["cue_types"]
    numbering = config["numbering"]
    bump_types = set(config.get("bump_types", []))
    typo_fixes = config.get("typo_fixes", {})
    intensity_keywords = config.get("intensity_keywords", [])
    color_keywords = config.get("color_keywords", [])
    intensity_palettes = config["intensity_palettes"]
    color_palettes = config["color_palettes"]

    object_index_map = {obj: idx + 1 for idx, obj in enumerate(objects)}
    intensity_index_map = {name: idx + 1 for idx, name in enumerate(intensity_palettes)}
    color_index_map = {name: idx + 1 for idx, name in enumerate(color_palettes)}

    rows: list[dict] = []

    index = 1
    for cue_type in cue_types["general"]:
        cue_type = normalize_text(cue_type, typo_fixes)
        q_number = f"{numbering['general_base']}{index:02d}"
        rows.append(
            {
                "Q": q_number,
                "Name": f"General {cue_type}",
                "Intensity Palette Number": "",
                "Intensity Palette": "",
                "Color Palette Number": "",
                "Color Palette": "",
                "_q_number": q_number,
            }
        )
        if cue_type in bump_types:
            rows.append(
                {
                    "Q": f"{q_number}.1",
                    "Name": "General Bump Return",
                    "Intensity Palette Number": "",
                    "Intensity Palette": "",
                    "Color Palette Number": "",
                    "Color Palette": "",
                    "_q_number": f"{q_number}.1",
                }
            )
        index += 1

    for obj in objects:
        index = 1
        base = numbering["single_bases"][obj]
        for cue_type in cue_types["single"]:
            cue_type = normalize_text(cue_type, typo_fixes)
            q_number = f"{base}{index:02d}"
            intensity_palette = keyword_palette(cue_type, intensity_keywords, "Base")
            color_palette = keyword_palette(cue_type, color_keywords, "Base")
            intensity_number, intensity_name = format_palette_entry(
                [obj],
                intensity_palette,
                intensity_index_map[intensity_palette],
                object_index_map,
            )
            color_number, color_name = format_palette_entry(
                [obj],
                color_palette,
                color_index_map[color_palette],
                object_index_map,
            )
            rows.append(
                {
                    "Q": q_number,
                    "Name": f"{obj} {cue_type}",
                    "Intensity Palette Number": intensity_number,
                    "Intensity Palette": intensity_name,
                    "Color Palette Number": color_number,
                    "Color Palette": color_name,
                    "_q_number": q_number,
                }
            )
            if cue_type in bump_types:
                rows.append(
                    {
                        "Q": f"{q_number}.1",
                        "Name": f"{obj} Bump Return",
                        "Intensity Palette Number": intensity_number,
                        "Intensity Palette": intensity_name,
                        "Color Palette Number": color_number,
                        "Color Palette": color_name,
                        "_q_number": f"{q_number}.1",
                    }
                )
            index += 1

    double_types = [normalize_text(value, typo_fixes) for value in cue_types["double"]]
    for first, second in object_pairs(objects):
        base = numbering["double_bases"][first]
        label = f"{first}+{second}"
        for cue_index, cue_type in enumerate(double_types, start=1):
            q_number = resolve_double_q_number(
                cue_type,
                cue_types["double"],
                base,
                objects,
                first,
                second,
            )
            intensity_palette = keyword_palette(cue_type, intensity_keywords, "Base")
            color_palette = keyword_palette(cue_type, color_keywords, "Base")
            intensity_number, intensity_name = format_palette_entry(
                [first, second],
                intensity_palette,
                intensity_index_map[intensity_palette],
                object_index_map,
            )
            color_number, color_name = format_palette_entry(
                [first, second],
                color_palette,
                color_index_map[color_palette],
                object_index_map,
            )
            rows.append(
                {
                    "Q": q_number,
                    "Name": cue_type.replace("A+B", label).strip(),
                    "Intensity Palette Number": intensity_number,
                    "Intensity Palette": intensity_name,
                    "Color Palette Number": color_number,
                    "Color Palette": color_name,
                    "_q_number": q_number,
                }
            )
            if cue_type in bump_types:
                rows.append(
                    {
                        "Q": f"{q_number}.1",
                        "Name": f"{label} Bump Return",
                        "Intensity Palette Number": intensity_number,
                        "Intensity Palette": intensity_name,
                        "Color Palette Number": color_number,
                        "Color Palette": color_name,
                        "_q_number": f"{q_number}.1",
                    }
                )

    rows.sort(key=lambda row: parse_q_number(row["_q_number"]))
    for row in rows:
        row.pop("_q_number", None)
    return rows


def build_qlab_rows(config: dict, eos_rows: list[dict]) -> list[dict]:
    objects = config["objects"]
    cue_types = config["cue_types"]
    numbering = config["numbering"]
    typo_fixes = config.get("typo_fixes", {})
    cue_type_keywords = config.get("cue_type_keywords", {})

    def format_eos_display(q_number: str) -> str:
        if not q_number:
            return ""
        if "." in q_number:
            main, suffix = q_number.split(".", 1)
        else:
            main, suffix = q_number, ""
        main_stripped = main.lstrip("0") or "0"
        return f"{main_stripped}.{suffix}" if suffix else main_stripped

    eos_map = {row["Q"]: row["Name"] for row in eos_rows}
    base_q_csv = config.get("base_q_csv", "lightingcues.csv")
    base_cues = load_base_cues(
        os.path.join(os.path.dirname(__file__), base_q_csv), typo_fixes
    )

    rows: list[dict] = []
    for cue in base_cues:
        base_q = cue["Q"]
        look = cue["Look"]
        mode = detect_mode(look)

        if mode == "none":
            cue_type = keyword_cue_type(
                look,
                cue_type_keywords.get("general", []),
                cue_types["general"][0],
            )
            eos_q = resolve_general_q_number(
                cue_type, cue_types["general"], numbering["general_base"]
            )
            rows.append(
                {
                    "qlab q": base_q,
                    "qlab name": look,
                    "eos q number": format_eos_display(eos_q),
                    "eos name": eos_map.get(eos_q, ""),
                }
            )
            continue

        if mode == "single":
            rows.append(
                {
                    "qlab q": base_q,
                    "qlab name": look,
                    "eos q number": "",
                    "eos name": "",
                }
            )
            cue_type = keyword_cue_type(
                look,
                cue_type_keywords.get("single", []),
                "Base",
            )
            for index, obj in enumerate(objects, start=1):
                qlab_q = f"{base_q}.{index}"
                eos_q = resolve_single_q_number(
                    cue_type,
                    cue_types["single"],
                    numbering["single_bases"][obj],
                )
                rows.append(
                    {
                        "qlab q": qlab_q,
                        "qlab name": f"{look} - {obj}",
                        "eos q number": format_eos_display(eos_q),
                        "eos name": eos_map.get(eos_q, ""),
                    }
                )
            continue

        rows.append(
            {
                "qlab q": base_q,
                "qlab name": look,
                "eos q number": "",
                "eos name": "",
            }
        )
        cue_type = keyword_cue_type(
            look,
            cue_type_keywords.get("double", []),
            "A+B",
        )
        for first, second in object_pairs(objects):
            suffix = f"{numbering['double_bases'][first]}{numbering['single_bases'][second]}"
            qlab_q = f"{base_q}.{suffix}"
            eos_q = resolve_double_q_number(
                cue_type,
                cue_types["double"],
                numbering["double_bases"][first],
                objects,
                first,
                second,
            )
            rows.append(
                {
                    "qlab q": qlab_q,
                    "qlab name": f"{look} - {first}+{second}",
                    "eos q number": format_eos_display(eos_q),
                    "eos name": eos_map.get(eos_q, ""),
                }
            )
    return rows


def build_permutation_rows(objects: list[str], numbering: dict) -> list[dict]:
    rows = []
    for first, second in object_pairs(objects):
        suffix = f"{numbering['double_bases'][first]}{numbering['single_bases'][second]}"
        rows.append(
            {
                "Permutation": suffix,
                "Object A": first,
                "Object B": second,
            }
        )
    return rows


def write_csv(
    path: str,
    rows: list[dict],
    headers: list[str],
    include_header: bool = True,
) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        if include_header:
            writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.yaml")
    config = load_config(config_path)
    eos_output = os.path.join(base_dir, config.get("output_eos_csv", "eoslightingcues.csv"))
    qlab_output = os.path.join(base_dir, config.get("output_qlab_csv", "qlablightingcue.csv"))
    permutation_output = os.path.join(
        base_dir, config.get("output_permutation_csv", "permutation_numbers.csv")
    )

    eos_rows = build_eos_rows(config)
    qlab_rows = build_qlab_rows(config, eos_rows)
    permutation_rows = build_permutation_rows(config["objects"], config["numbering"])

    write_csv(eos_output, eos_rows, EOS_HEADERS)
    qlab_include_header = config.get("qlab_include_header", False)
    write_csv(qlab_output, qlab_rows, QLAB_HEADERS, include_header=qlab_include_header)
    write_csv(permutation_output, permutation_rows, PERMUTATION_HEADERS)


if __name__ == "__main__":
    main()
