from flask import Flask, request, jsonify
import time
import math

app = Flask(__name__)

# State variables for orientation tracking
current_pitch = 0.0
current_roll = 0.0
last_timestamp = None

ROTATION_THRESHOLD = 3.0  # Radians per second threshold for "excessive movement"

@app.route('/telemetry', methods=['POST'])
def receive_telemetry():
    global current_pitch, current_roll, last_timestamp
    
    data = request.json
    # Sensor Logger app structures data in a list of readings
    if not data or 'readings' not in data:
        return jsonify({"status": "error", "message": "Invalid payload"}), 400
        
    current_time = time.time()
    dt = current_time - last_timestamp if last_timestamp else 0.01
    last_timestamp = current_time

    for reading in data['readings']:
        # Extract 6-DoF data
        gyro_x = reading.get('gyro_x', 0.0)
        gyro_y = reading.get('gyro_y', 0.0)
        gyro_z = reading.get('gyro_z', 0.0)
        
        accel_x = reading.get('accel_x', 0.0)
        accel_y = reading.get('accel_y', 0.0)
        accel_z = reading.get('accel_z', 1.0) # Prevent division by zero

        # 1. Physics-based Sensor Fusion (Complementary Filter) to stop drift
        # Calculate pitch and roll angles directly from gravity (Accelerometer)
        accel_pitch = math.atan2(accel_y, math.sqrt(accel_x**2 + accel_z**2))
        accel_roll = math.atan2(-accel_x, accel_z)

        # Integrate gyroscope velocity, blend with accelerometer to eliminate gyro drift
        current_pitch = 0.98 * (current_pitch + gyro_x * dt) + 0.02 * accel_pitch
        current_roll = 0.98 * (current_roll + gyro_y * dt) + 0.02 * accel_roll

        # 2. Threshold Analytics (Real-Time Error Catching)
        gyro_magnitude = math.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)
        status = "NORMAL"
        if gyro_magnitude > ROTATION_THRESHOLD:
            status = "CRITICAL: Excessive Rotation Speed"
            print(f"[{status}] Magnitude: {gyro_magnitude:.2f} rad/s")

    # This mock PyTorch endpoint structure mirrors your eventual ML inference payload
    return jsonify({
        "status": status,
        "orientation": {"pitch": current_pitch, "roll": current_roll},
        "metrics_logged": len(data['readings'])
    }), 200

if __name__ == '__main__':
    # Run on local network so your phone can reach your computer's IP address
    app.run(host='0.0.0.0', port=5000, debug=True)
