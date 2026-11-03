import mysql.connector


def get_connection(include_database=True):
    config = {
        "host": "localhost",
        "user": "root",
        "password": "",
    }
    if include_database:
        config["database"] = "gyroscope_data"
    return mysql.connector.connect(**config)


def save_telemetry_batch(readings):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Batch inserting to optimize database write-I/O overhead
        query = """INSERT INTO telemetry
                   (device_timestamp, session_id, accel_x, accel_y, accel_z,
                    gyro_x, gyro_y, gyro_z, orientation_qx, orientation_qy,
                    orientation_qz, orientation_qw)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        batch_data = [
            (r.get('device_timestamp'), r.get('session_id'),
             r.get('accel_x'), r.get('accel_y'), r.get('accel_z'),
             r.get('gyro_x'), r.get('gyro_y'), r.get('gyro_z'),
             r.get('orientation_qx'), r.get('orientation_qy'),
             r.get('orientation_qz'), r.get('orientation_qw'))
            for r in readings
        ]
        
        cursor.executemany(query, batch_data)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")


def fetch_telemetry_between(start_time, end_time):
    """Fetch paired telemetry rows in an inclusive device-time range (UTC)."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT id, session_id, device_timestamp, accel_x, accel_y, accel_z,
                      gyro_x, gyro_y, gyro_z
               FROM telemetry
               WHERE device_timestamp BETWEEN %s AND %s
               ORDER BY session_id ASC, device_timestamp ASC, id ASC""",
            (start_time, end_time),
        )
        return cursor.fetchall()
    finally:
        conn.close()


def fetch_training_rows():
    """Fetch complete sensor windows with phone quaternion targets."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT id, session_id, device_timestamp,
                      accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z,
                      orientation_qx, orientation_qy, orientation_qz, orientation_qw
               FROM telemetry
               WHERE device_timestamp IS NOT NULL
                 AND accel_x IS NOT NULL AND accel_y IS NOT NULL AND accel_z IS NOT NULL
                 AND gyro_x IS NOT NULL AND gyro_y IS NOT NULL AND gyro_z IS NOT NULL
                 AND orientation_qx IS NOT NULL AND orientation_qy IS NOT NULL
                 AND orientation_qz IS NOT NULL AND orientation_qw IS NOT NULL
               ORDER BY session_id, device_timestamp, id"""
        )
        return cursor.fetchall()
    finally:
        conn.close()
