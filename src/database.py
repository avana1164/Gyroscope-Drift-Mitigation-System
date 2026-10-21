import mysql.connector

def save_telemetry_batch(readings):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ultrasound_tracker"
        )
        cursor = conn.cursor()
        
        # Batch inserting to optimize database write-I/O overhead
        query = """INSERT INTO telemetry (accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z) 
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        
        batch_data = [
            (r.get('accel_x'), r.get('accel_y'), r.get('accel_z'), 
             r.get('gyro_x'), r.get('gyro_y'), r.get('gyro_z')) 
            for r in readings
        ]
        
        cursor.executemany(query, batch_data)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
