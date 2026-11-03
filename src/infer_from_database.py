"""Run the current PyTorch layer on telemetry in a device-time interval."""

import argparse
from datetime import datetime, timezone

from .database import fetch_telemetry_between
from .model_inference import correct_spatial_drift


def parse_utc_datetime(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def main():
    parser = argparse.ArgumentParser(
        description="Run PyTorch inference on saved telemetry in a UTC time range."
    )
    parser.add_argument("start", help="Inclusive ISO-8601 start, e.g. 2026-11-02T14:30:00Z")
    parser.add_argument("end", help="Inclusive ISO-8601 end, e.g. 2026-11-02T14:31:00Z")
    args = parser.parse_args()

    start_time = parse_utc_datetime(args.start)
    end_time = parse_utc_datetime(args.end)
    if start_time > end_time:
        parser.error("start must be earlier than or equal to end")

    rows = fetch_telemetry_between(start_time, end_time)
    if not rows:
        print("No telemetry found in that device-time range.")
        return

    processed = 0
    for row in rows:
        sensor_values = [
            row["accel_x"], row["accel_y"], row["accel_z"],
            row["gyro_x"], row["gyro_y"], row["gyro_z"],
        ]
        if any(value is None for value in sensor_values):
            continue

        accel = [float(row[f"accel_{axis}"]) for axis in "xyz"]
        gyro = [float(row[f"gyro_{axis}"]) for axis in "xyz"]
        prediction = correct_spatial_drift(accel, gyro)
        print(
            f"{row['device_timestamp'].isoformat()} | row {row['id']} | "
            f"layer output: pitch={prediction[0]:.6f}, roll={prediction[1]:.6f}"
        )
        processed += 1

    print(f"Processed {processed} complete rows out of {len(rows)} fetched.")


if __name__ == "__main__":
    main()
