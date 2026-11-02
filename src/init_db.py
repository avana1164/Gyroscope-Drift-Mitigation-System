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
            accel_x FLOAT,
            accel_y FLOAT,
            accel_z FLOAT,
            gyro_x FLOAT,
            gyro_y FLOAT,
            gyro_z FLOAT
        );
        """
        cursor.execute(create_table_query)

        # Add the device timestamp to databases created before this schema change.
        cursor.execute("SHOW COLUMNS FROM telemetry LIKE 'device_timestamp'")
        if cursor.fetchone() is None:
            cursor.execute(
                "ALTER TABLE telemetry ADD COLUMN device_timestamp DATETIME(6) NULL"
            )
        print("Table 'telemetry' verified/created successfully.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Initialization Failed: {e}")

if __name__ == "__main__":
    initialize_database()
