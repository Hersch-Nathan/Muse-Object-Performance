import csv
import os
import subprocess
import sys
from datetime import datetime, timedelta

try:
	import yaml
except ImportError as exc:  # pragma: no cover - runtime dependency message
	raise SystemExit(
		"Missing dependency: pyyaml. Install with 'pip install pyyaml'."
	) from exc


DAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]


def parse_clock_minutes(value: str) -> int:
	text = (value or "").strip()
	if not text:
		return 10_000
	parsed = datetime.strptime(text, "%I:%M %p")
	return parsed.hour * 60 + parsed.minute


def format_clock(value: datetime) -> str:
	return value.strftime("%I:%M %p").lstrip("0")


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


def run_base_order_generator(order_dir: str) -> None:
	script_path = os.path.join(order_dir, "generate_schedule.py")
	subprocess.run([sys.executable, script_path], cwd=order_dir, check=True)


def load_base_run_order_rows(path: str) -> list[dict]:
	rows: list[dict] = []
	with open(path, "r", encoding="utf-8", newline="") as handle:
		reader = csv.DictReader(handle)
		for row in reader:
			run_value = (row.get("Run") or "").strip()
			if run_value == "Intermission":
				rows.append(
					{
						"Run": "Intermission",
						"Time": (row.get("Time") or "").strip(),
						"Domin": "",
						"DominPerformer": "",
						"Alquist": "",
						"AlquistPerformer": "",
					}
				)
				continue

			rows.append(
				{
					"Run": run_value,
					"Time": (row.get("Time") or "").strip(),
					"Domin": (row.get("Domin") or "").strip(),
					"DominPerformer": (row.get("DominPerformer") or "").strip(),
					"Alquist": (row.get("Alquist") or "").strip(),
					"AlquistPerformer": (row.get("AlquistPerformer") or "").strip(),
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


def build_week_timeline_by_day(config: dict) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
	by_day: dict[str, list[dict]] = {key: [] for key in DAY_KEYS}
	notes_by_day: dict[str, list[dict]] = {key: [] for key in DAY_KEYS}

	for day in config.get("week_timeline", []):
		day_label = day["day"]
		day_key = day_label.split(",")[0].strip().lower()
		rows = by_day.setdefault(day_key, [])
		day_notes = notes_by_day.setdefault(day_key, [])

		for entry in day.get("entries", []):
			rows.append(
				{
					"Time": entry["time"],
					"Event": entry["event"],
					"Notes": entry.get("notes", ""),
				}
			)

		custom_notes = day.get("day_notes", [])
		if isinstance(custom_notes, str):
			custom_notes = [custom_notes]

		for note in custom_notes:
			text = str(note).strip()
			if text:
				day_notes.append({"Note": text})

	return by_day, notes_by_day


def build_monday_explicit_runs(config: dict) -> list[dict]:
	rows: list[dict] = []
	run_time = datetime.strptime("6:45 PM", "%I:%M %p")
	run_step = timedelta(minutes=14)

	for item in config.get("show_order", []):
		run_label = str(item.get("run_label", "")).strip()
		if run_label not in {"Run 1", "Run 2", "Run 3", "Run 4"}:
			continue
		rows.append(
			{
				"Run": run_label,
				"Time": format_clock(run_time),
				"Domin": item.get("scene_a", ""),
				"DominPerformer": "",
				"Alquist": item.get("scene_b", ""),
				"AlquistPerformer": "",
			}
		)
		run_time += run_step
	return rows


def build_day_combined_rows(
	timeline_rows: list[dict],
	run_rows: list[dict],
) -> list[dict]:
	combined: list[dict] = []

	for row in timeline_rows:
		combined.append(
			{
				"Time": row.get("Time", ""),
				"Type": "Schedule",
				"Event": row.get("Event", ""),
				"Domin": "",
				"DominPerformer": "",
				"Alquist": "",
				"AlquistPerformer": "",
			}
		)

	for row in run_rows:
		combined.append(
			{
				"Time": row.get("Time", ""),
				"Type": "Run",
				"Event": row.get("Run", ""),
				"Domin": row.get("Domin", ""),
				"DominPerformer": row.get("DominPerformer", ""),
				"Alquist": row.get("Alquist", ""),
				"AlquistPerformer": row.get("AlquistPerformer", ""),
			}
		)

	combined.sort(
		key=lambda row: (
			parse_clock_minutes(row.get("Time", "")),
			0 if row.get("Type") == "Schedule" else 1,
			row.get("Event", ""),
		)
	)

	return combined


def build_day_run_orders(config: dict, order12_rows: list[dict]) -> dict[str, list[dict]]:
	monday_rows = build_monday_explicit_runs(config)
	day_runs: dict[str, list[dict]] = {
		"monday": monday_rows,
		"tuesday": order12_rows,
		"wednesday": order12_rows,
		"thursday": order12_rows,
		"friday": order12_rows,
		"saturday": order12_rows,
	}
	return day_runs


def main() -> None:
	base_dir = os.path.dirname(os.path.abspath(__file__))
	order_dir = os.path.dirname(base_dir)
	config_path = os.path.join(base_dir, "config.yaml")
	performers_dir = os.path.join(base_dir, "performers")
	days_dir = os.path.join(base_dir, "days")

	config = load_config(config_path)

	run_base_order_generator(order_dir)
	order12_rows = load_base_run_order_rows(os.path.join(order_dir, "show_order.csv"))

	timeline_by_day, notes_by_day = build_week_timeline_by_day(config)
	run_orders_by_day = build_day_run_orders(config, order12_rows)
	moose_rows = build_performer_call_rows(config, "moose")
	luca_rows = build_performer_call_rows(config, "luca")

	run_headers = ["Run", "Time", "Domin", "DominPerformer", "Alquist", "AlquistPerformer"]
	timeline_headers = ["Time", "Event", "Notes"]
	combined_headers = [
		"Time",
		"Type",
		"Event",
		"Domin",
		"DominPerformer",
		"Alquist",
		"AlquistPerformer",
	]
	day_note_headers = ["Note"]
	call_headers = ["Day", "CallType", "Time", "Notes"]

	ensure_output_dir(days_dir)
	for day_key in DAY_KEYS:
		timeline_rows = timeline_by_day.get(day_key, [])
		run_rows = run_orders_by_day.get(day_key, [])

		write_csv(
			os.path.join(days_dir, f"{day_key}_timeline.csv"),
			timeline_headers,
			timeline_rows,
		)
		write_csv(
			os.path.join(days_dir, f"{day_key}_runs.csv"),
			run_headers,
			run_rows,
		)
		write_csv(
			os.path.join(days_dir, f"{day_key}_combined.csv"),
			combined_headers,
			build_day_combined_rows(timeline_rows, run_rows),
		)
		write_csv(
			os.path.join(days_dir, f"{day_key}_notes.csv"),
			day_note_headers,
			notes_by_day.get(day_key, []),
		)

	ensure_output_dir(performers_dir)
	write_csv(os.path.join(performers_dir, "moose.csv"), call_headers, moose_rows)
	write_csv(os.path.join(performers_dir, "luca.csv"), call_headers, luca_rows)


if __name__ == "__main__":
	main()
