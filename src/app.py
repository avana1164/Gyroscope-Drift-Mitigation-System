from flask import Flask, request, jsonify
import time
import math
from collections import deque
from datetime import datetime, timezone
from .database import save_telemetry_batch
from .model_inference import load_orientation_model, predict_orientation

app = Flask(__name__)

current_pitch = 0.0
current_roll = 0.0
last_timestamp = None
ROTATION_THRESHOLD = 3.0  # Radians per second threshold for errors
loaded_model = load_orientation_model()
model_window_size = loaded_model[3] if loaded_model else 32
orientation_buffers = {}


def parse_device_timestamp(value):
    """Convert an ISO-8601 or Unix timestamp from the phone to a naive UTC datetime."""
    if value is None:
        return None

    try:
        if isinstance(value, (int, float)):
            timestamp_seconds = unix_timestamp_seconds(value)
            parsed = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        elif isinstance(value, str):
            text_value = value.strip()
            if not text_value:
                return None
            try:
                timestamp_seconds = float(text_value)
                timestamp_seconds = unix_timestamp_seconds(timestamp_seconds)
                parsed = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
            except ValueError:
                parsed = datetime.fromisoformat(text_value.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            return None
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except (OverflowError, OSError, TypeError, ValueError):
        return None


def unix_timestamp_seconds(value):
    """Normalize Unix seconds, milliseconds, microseconds, or nanoseconds."""
    magnitude = abs(value)
    if magnitude >= 1e17:  # nanoseconds
        return value / 1e9
    if magnitude >= 1e14:  # microseconds
        return value / 1e6
    if magnitude >= 1e11:  # milliseconds
        return value / 1e3
    return value

@app.route('/telemetry', methods=['POST'])
def receive_telemetry():
    global current_pitch, current_roll, last_timestamp
    
    data = request.json
    if not data or 'payload' not in data:
        return jsonify({"status": "error", "message": "No payload detected"}), 400
        
    current_time = time.time()
    dt = current_time - last_timestamp if last_timestamp else 0.01
    last_timestamp = current_time

    # Pair calibrated accel/gyro and the phone's orientation target by sample time.
    paired_readings = {}
    status = "NORMAL"
    
    # Core parsing loops to process nested Sensor Logger payloads
    request_timestamp = data.get('timestamp', data.get('time'))
    for item_index, item in enumerate(data['payload']):
        name = item.get('name', '')
        values = item.get('values', {})
        
        # Guard clause for empty test vectors
        if not values or not isinstance(values, dict):
            continue

        normalized_name = name.lower()
        if normalized_name not in {"accelerometer", "gyroscope", "orientation"}:
            continue

        # Sensor Logger variants commonly put the sample time on each item;
        # accept a request-level time as a fallback. Missing times remain NULL.
        sample_time = item.get('time', item.get('timestamp', request_timestamp))
        device_timestamp = parse_device_timestamp(sample_time)

        # Use a unique key if the sender supplies no sample timestamp; do not
        # accidentally combine unrelated readings that have no shared time.
        sample_key = str(sample_time) if sample_time is not None else f"untimed-{item_index}"
        reading = paired_readings.setdefault(sample_key, {
            'device_timestamp': device_timestamp,
            'session_id': data.get('sessionId'),
            'accel_x': None, 'accel_y': None, 'accel_z': None,
            'gyro_x': None, 'gyro_y': None, 'gyro_z': None,
            'orientation_qx': None, 'orientation_qy': None,
            'orientation_qz': None, 'orientation_qw': None,
        })
            
        # Standard schema parsing
        x = values.get('x', 0.0)
        y = values.get('y', 0.0)
        z = values.get('z', 0.0)

        # Allocate variables depending on device message tags
        if normalized_name == "accelerometer":
            # Calculate orientation baseline from gravity vector
            accel_pitch = math.atan2(y, math.sqrt(x**2 + z**2 if (x**2 + z**2) > 0 else 1.0))
            accel_roll = math.atan2(-x, z if z != 0 else 1.0)
            current_pitch = 0.98 * current_pitch + 0.02 * accel_pitch
            current_roll = 0.98 * current_roll + 0.02 * accel_roll
            
            reading.update({'accel_x': x, 'accel_y': y, 'accel_z': z})

        elif normalized_name == "gyroscope":
            # Calculate total rotational angular velocity magnitude
            gyro_magnitude = math.sqrt(x**2 + y**2 + z**2)
            current_pitch += x * dt
            current_roll += y * dt
            
            if gyro_magnitude > ROTATION_THRESHOLD:
                status = "CRITICAL: Excessive Rotation Speed"
            
            reading.update({'gyro_x': x, 'gyro_y': y, 'gyro_z': z})

        elif normalized_name == "orientation":
            reading.update({
                'orientation_qx': values.get('qx'),
                'orientation_qy': values.get('qy'),
                'orientation_qz': values.get('qz'),
                'orientation_qw': values.get('qw'),
            })

    # Save rows in sample order and update the in-memory sequence for inference.
    db_readings = sorted(
        paired_readings.values(),
        key=lambda row: row['device_timestamp'] or datetime.min,
    )
    if db_readings:
        save_telemetry_batch(db_readings)

    model_prediction = None
    model_status = "model_not_trained" if loaded_model is None else "warming_up"
    if loaded_model is not None:
        stream_key = (data.get('deviceId'), data.get('sessionId'))
        sample_buffer = orientation_buffers.setdefault(
            stream_key, deque(maxlen=model_window_size)
        )
        for reading in db_readings:
            required = [reading[f'{sensor}_{axis}']
                        for sensor in ('accel', 'gyro') for axis in 'xyz']
            if any(value is None for value in required):
                continue
            sample_buffer.append([float(value) for value in required])
            if len(sample_buffer) == model_window_size:
                model_prediction = predict_orientation(loaded_model, list(sample_buffer))
                model_status = "ready"

    # Print out a clean, real-time spatial dashboard on your screen
    print(f"🔮 Pitch: {math.degrees(current_pitch):.1f}° | Roll: {math.degrees(current_roll):.1f}° | Status: {status}")

    return jsonify({
        "status": status,
        "orientation": {"pitch": current_pitch, "roll": current_roll},
        "model_orientation_quaternion": model_prediction,
        "model_status": model_status,
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
