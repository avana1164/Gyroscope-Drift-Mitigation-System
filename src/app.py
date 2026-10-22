from flask import Flask, request, jsonify
import time
import math
from database import save_telemetry_batch  # Imports your Docker insert logic

app = Flask(__name__)

current_pitch = 0.0
current_roll = 0.0
last_timestamp = None
ROTATION_THRESHOLD = 3.0  # Radians per second threshold for errors

@app.route('/telemetry', methods=['POST'])
def receive_telemetry():
    global current_pitch, current_roll, last_timestamp
    
    data = request.json
    if not data or 'payload' not in data:
        return jsonify({"status": "error", "message": "No payload detected"}), 400
        
    current_time = time.time()
    dt = current_time - last_timestamp if last_timestamp else 0.01
    last_timestamp = current_time

    # Containers for batch processing
    db_readings = []
    status = "NORMAL"
    
    # Core parsing loops to process nested Sensor Logger payloads
    for item in data['payload']:
        name = item.get('name', '')
        values = item.get('values', {})
        
        # Guard clause for empty test vectors
        if not values or not isinstance(values, dict):
            continue
            
        # Standard schema parsing
        x = values.get('x', 0.0)
        y = values.get('y', 0.0)
        z = values.get('z', 0.0)

        # Allocate variables depending on device message tags
        if "accel" in name.lower():
            # Calculate orientation baseline from gravity vector
            accel_pitch = math.atan2(y, math.sqrt(x**2 + z**2 if (x**2 + z**2) > 0 else 1.0))
            accel_roll = math.atan2(-x, z if z != 0 else 1.0)
            current_pitch = 0.98 * current_pitch + 0.02 * accel_pitch
            current_roll = 0.98 * current_roll + 0.02 * accel_roll
            
            # Queue structured dictionary for background database writer
            db_readings.append({
                'accel_x': x, 'accel_y': y, 'accel_z': z,
                'gyro_x': 0.0, 'gyro_y': 0.0, 'gyro_z': 0.0
            })

        elif "gyro" in name.lower():
            # Calculate total rotational angular velocity magnitude
            gyro_magnitude = math.sqrt(x**2 + y**2 + z**2)
            current_pitch += x * dt
            current_roll += y * dt
            
            if gyro_magnitude > ROTATION_THRESHOLD:
                status = "CRITICAL: Excessive Rotation Speed"
            
            db_readings.append({
                'accel_x': 0.0, 'accel_y': 0.0, 'accel_z': 0.0,
                'gyro_x': x, 'gyro_y': y, 'gyro_z': z
            })

    # Asynchronously pipe buffered metrics to Docker MySQL container
    if db_readings:
        save_telemetry_batch(db_readings)

    # Print out a clean, real-time spatial dashboard on your screen
    print(f"🔮 Pitch: {math.degrees(current_pitch):.1f}° | Roll: {math.degrees(current_roll):.1f}° | Status: {status}")

    return jsonify({
        "status": status,
        "orientation": {"pitch": current_pitch, "roll": current_roll}
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
