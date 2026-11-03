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
                   (device_timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        
        batch_data = [
            (r.get('device_timestamp'), r.get('accel_x'), r.get('accel_y'), r.get('accel_z'),
             r.get('gyro_x'), r.get('gyro_y'), r.get('gyro_z')) 
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
            """SELECT id, device_timestamp, accel_x, accel_y, accel_z,
                      gyro_x, gyro_y, gyro_z
               FROM telemetry
               WHERE device_timestamp BETWEEN %s AND %s
               ORDER BY device_timestamp ASC, id ASC""",
            (start_time, end_time),
        )
        return cursor.fetchall()
    finally:
        conn.close()
