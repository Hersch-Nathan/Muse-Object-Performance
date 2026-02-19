import csv
import os

try:
	import yaml
except ImportError as exc:  # pragma: no cover - runtime dependency message
	raise SystemExit(
		"Missing dependency: pyyaml. Install with 'pip install pyyaml'."
	) from exc


def load_config(path: str) -> dict:
	with open(path, "r", encoding="utf-8") as handle:
		return yaml.safe_load(handle)


def ensure_output_dir(path: str) -> None:
	os.makedirs(path, exist_ok=True)


def write_csv(path: str, headers: list[str], rows: list[dict]) -> None:
	with open(path, "w", encoding="utf-8", newline="") as handle:
		writer = csv.DictWriter(handle, fieldnames=headers)
		writer.writeheader()
		writer.writerows(rows)


def build_show_order_rows(config: dict) -> list[dict]:
	rows: list[dict] = []
	for item in config.get("show_order", []):
		rows.append(
			{
				"Run": item["run_label"],
				"SceneA": item["scene_a"],
				"SceneB": item["scene_b"],
				"Notes": item.get("notes", ""),
			}
		)
	return rows


def build_week_timeline_rows(config: dict) -> list[dict]:
	rows: list[dict] = []
	for day in config.get("week_timeline", []):
		day_label = day["day"]
		for entry in day.get("entries", []):
			rows.append(
				{
					"Day": day_label,
					"Time": entry["time"],
					"Event": entry["event"],
					"Notes": entry.get("notes", ""),
				}
			)
	return rows


def build_performer_call_rows(config: dict, performer_key: str) -> list[dict]:
	performer = config["performers"][performer_key]
	rows: list[dict] = []
	for item in performer.get("calls", []):
		rows.append(
			{
				"Day": item["day"],
				"CallType": item["call_type"],
				"Time": item["time"],
				"Notes": item.get("notes", ""),
			}
		)
	return rows


def main() -> None:
	base_dir = os.path.dirname(os.path.abspath(__file__))
	config_path = os.path.join(base_dir, "config.yaml")
	performers_dir = os.path.join(base_dir, "performers")

	config = load_config(config_path)

	show_order_rows = build_show_order_rows(config)
	week_rows = build_week_timeline_rows(config)
	moose_rows = build_performer_call_rows(config, "moose")
	luca_rows = build_performer_call_rows(config, "luca")

	show_order_headers = ["Run", "SceneA", "SceneB", "Notes"]
	week_headers = ["Day", "Time", "Event", "Notes"]
	call_headers = ["Day", "CallType", "Time", "Notes"]

	write_csv(os.path.join(base_dir, "general_show_order.csv"), show_order_headers, show_order_rows)
	write_csv(os.path.join(base_dir, "week_timeline.csv"), week_headers, week_rows)

	ensure_output_dir(performers_dir)
	write_csv(os.path.join(performers_dir, "moose.csv"), call_headers, moose_rows)
	write_csv(os.path.join(performers_dir, "luca.csv"), call_headers, luca_rows)


if __name__ == "__main__":
	main()
