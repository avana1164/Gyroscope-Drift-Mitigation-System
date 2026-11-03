import mysql.connector

def initialize_database():
    try:
        # 1. Connect to the local MySQL server root
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""  # Default is empty for XAMPP / basic local setups
        )
        cursor = conn.cursor()
        
        # 2. Automatically create the database if missing
        cursor.execute("CREATE DATABASE IF NOT EXISTS gyroscope_data")
        print("Database 'gyroscope_data' verified/created.")
        
        # 3. Switch context to the new database
        cursor.execute("USE gyroscope_data")
        
        # 4. Define and create the structured tracking table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS telemetry (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),
            device_timestamp DATETIME(6) NULL,
            session_id VARCHAR(64) NULL,
            accel_x FLOAT,
            accel_y FLOAT,
            accel_z FLOAT,
            gyro_x FLOAT,
            gyro_y FLOAT,
            gyro_z FLOAT,
            orientation_qx FLOAT NULL,
            orientation_qy FLOAT NULL,
            orientation_qz FLOAT NULL,
            orientation_qw FLOAT NULL
        );
        """
        cursor.execute(create_table_query)

        # Add columns to databases created with earlier versions of this schema.
        migrations = {
            "device_timestamp": "DATETIME(6) NULL",
            "session_id": "VARCHAR(64) NULL",
            "orientation_qx": "FLOAT NULL",
            "orientation_qy": "FLOAT NULL",
            "orientation_qz": "FLOAT NULL",
            "orientation_qw": "FLOAT NULL",
        }
        for column, definition in migrations.items():
            cursor.execute(f"SHOW COLUMNS FROM telemetry LIKE '{column}'")
            if cursor.fetchone() is None:
                cursor.execute(
                    f"ALTER TABLE telemetry ADD COLUMN {column} {definition}"
                )
        print("Table 'telemetry' verified/created successfully.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Initialization Failed: {e}")

if __name__ == "__main__":
    initialize_database()
