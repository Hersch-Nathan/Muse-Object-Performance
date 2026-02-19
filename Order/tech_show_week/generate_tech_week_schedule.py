import csv
import os
import subprocess
import sys

try:
	import yaml
except ImportError as exc:  # pragma: no cover - runtime dependency message
	raise SystemExit(
		"Missing dependency: pyyaml. Install with 'pip install pyyaml'."
	) from exc


DAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]


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
						"Notes": "Intermission",
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
					"Notes": "Order 12 from base schedule generator",
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


def build_week_timeline_by_day(config: dict) -> dict[str, list[dict]]:
	by_day: dict[str, list[dict]] = {key: [] for key in DAY_KEYS}
	for day in config.get("week_timeline", []):
		day_label = day["day"]
		day_key = day_label.split(",")[0].strip().lower()
		rows = by_day.setdefault(day_key, [])
		for entry in day.get("entries", []):
			rows.append(
				{
					"Time": entry["time"],
					"Event": entry["event"],
					"Notes": entry.get("notes", ""),
				}
			)
	return by_day


def build_monday_explicit_runs(config: dict) -> list[dict]:
	rows: list[dict] = []
	for item in config.get("show_order", []):
		run_label = str(item.get("run_label", "")).strip()
		if run_label not in {"Run 1", "Run 2", "Run 3", "Run 4"}:
			continue
		rows.append(
			{
				"Run": run_label,
				"Time": "",
				"Domin": item.get("scene_a", ""),
				"DominPerformer": "",
				"Alquist": item.get("scene_b", ""),
				"AlquistPerformer": "",
				"Notes": item.get("notes", "Monday explicit run order"),
			}
		)
	return rows


def build_general_show_order_rows(monday_rows: list[dict], order12_rows: list[dict]) -> list[dict]:
	summary_rows: list[dict] = []
	summary_rows.extend(monday_rows)
	summary_rows.extend(order12_rows)
	return summary_rows


def build_day_run_orders(config: dict, order12_rows: list[dict]) -> dict[str, list[dict]]:
	monday_rows = build_monday_explicit_runs(config)
	day_runs: dict[str, list[dict]] = {
		"monday": monday_rows,
		"tuesday": order12_rows,
		"wednesday": order12_rows,
		"thursday": order12_rows,
		"friday": [
			{
				"Run": "Show",
				"Time": "7:00 PM",
				"Domin": "Performance",
				"DominPerformer": "",
				"Alquist": "",
				"AlquistPerformer": "",
				"Notes": "Show day",
			}
		],
		"saturday": [
			{
				"Run": "Show",
				"Time": "7:00 PM",
				"Domin": "Performance",
				"DominPerformer": "",
				"Alquist": "",
				"AlquistPerformer": "",
				"Notes": "Show day",
			}
		],
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

	timeline_by_day = build_week_timeline_by_day(config)
	run_orders_by_day = build_day_run_orders(config, order12_rows)
	moose_rows = build_performer_call_rows(config, "moose")
	luca_rows = build_performer_call_rows(config, "luca")

	run_headers = ["Run", "Time", "Domin", "DominPerformer", "Alquist", "AlquistPerformer", "Notes"]
	timeline_headers = ["Time", "Event", "Notes"]
	call_headers = ["Day", "CallType", "Time", "Notes"]

	monday_rows = run_orders_by_day["monday"]
	write_csv(
		os.path.join(base_dir, "general_show_order.csv"),
		run_headers,
		build_general_show_order_rows(monday_rows, order12_rows),
	)

	ensure_output_dir(days_dir)
	for day_key in DAY_KEYS:
		write_csv(
			os.path.join(days_dir, f"{day_key}_timeline.csv"),
			timeline_headers,
			timeline_by_day.get(day_key, []),
		)
		write_csv(
			os.path.join(days_dir, f"{day_key}_runs.csv"),
			run_headers,
			run_orders_by_day.get(day_key, []),
		)

	ensure_output_dir(performers_dir)
	write_csv(os.path.join(performers_dir, "moose.csv"), call_headers, moose_rows)
	write_csv(os.path.join(performers_dir, "luca.csv"), call_headers, luca_rows)


if __name__ == "__main__":
	main()
