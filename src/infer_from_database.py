"""Run the current PyTorch layer on telemetry in a device-time interval."""

import argparse
from datetime import datetime, timezone
from collections import deque

from .database import fetch_telemetry_between
from .model_inference import load_orientation_model, predict_orientation


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

    loaded_model = load_orientation_model()
    if loaded_model is None:
        raise SystemExit("No trained checkpoint found. Run `python -m src.train_model` first.")
    window_size = loaded_model[3]
    window = deque(maxlen=window_size)
    active_session = object()

    processed = 0
    skipped = 0
    for row in rows:
        if row["session_id"] != active_session:
            window.clear()
            active_session = row["session_id"]

        sensor_values = [
            row["accel_x"], row["accel_y"], row["accel_z"],
            row["gyro_x"], row["gyro_y"], row["gyro_z"],
        ]
        if any(value is None for value in sensor_values):
            skipped += 1
            continue

        accel = [float(row[f"accel_{axis}"]) for axis in "xyz"]
        gyro = [float(row[f"gyro_{axis}"]) for axis in "xyz"]
        window.append(accel + gyro)
        if len(window) < window_size:
            continue
        prediction = predict_orientation(loaded_model, list(window))
        print(
            f"{row['device_timestamp'].isoformat()} | row {row['id']} | "
            f"predicted quaternion (qx, qy, qz, qw)="
            f"({prediction[0]:.6f}, {prediction[1]:.6f}, "
            f"{prediction[2]:.6f}, {prediction[3]:.6f})"
        )
        processed += 1

    print(
        f"Produced {processed} predictions from {len(rows)} fetched rows; "
        f"skipped {skipped} incomplete rows."
    )


if __name__ == "__main__":
    main()
