# Real-Time Spatial Telemetry Pipeline for Gyroscope Drift Mitigation

An end-to-end IoT data pipeline that captures high-frequency spatial metrics from a mobile device IMU to track technician proficiency, accelerate muscle memory training, and automate kinetic error assessment.

![System Demo](demo.gif)

## 🛠️ Architecture & Tech Stack
* **Sensor Streaming Layer:** Mobile 6-DoF IMU Telemetry (100Hz Stream via HTTP POST)
* **Backend API Framework:** Flask (Python)
* **Processing & Core Fusion Math:** PyTorch (Sequence Layer Pipeline) + Mathematical Complementary Filtering
* **Containerized Storage Layer:** MySQL deployed via Docker Container Network

## 🚀 Features & Automated Analytics
* **Real-Time Data Ingestion:** Processes continuous 100Hz inertial datasets with <20ms latency.
* **Drift Mitigation Filter:** Combines gyroscope and accelerometer vectors to continuously adjust tracking coordinates and eliminate sensor drift.
* **Kinetic Proficiency Profiling:** Detects and logs movement threshold errors including excessive rotation speed and off-target angles.
* **Programmatic Database Initialization:** Implements repeatable database configurations using Docker containerization bridges.

## 📦 Local Setup & Deployment

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and Python 3 first. Run the commands below from the repository root. The virtual environment keeps the Python dependencies isolated; activate it again whenever you open a new terminal.

### macOS

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```
2. Activate it:
   ```bash
   source .venv/bin/activate
   ```
3. Install the Python dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Start the MySQL database:
   ```bash
   docker compose -f src/docker-compose.yml up -d
   ```
5. Create the database schema:
   ```bash
   python -m src.init_db
   ```
6. Start the telemetry server:
   ```bash
   python -m src.app
   ```

### Windows (PowerShell)

1. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
2. Activate it:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
3. Install the Python dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Start the MySQL database:
   ```powershell
   docker compose -f src/docker-compose.yml up -d
   ```
5. Create the database schema:
   ```powershell
   python -m src.init_db
   ```
6. Start the telemetry server:
   ```powershell
   python -m src.app
   ```

If PowerShell blocks virtual environment activation, use Command Prompt instead and activate with `.venv\Scripts\activate.bat`.

The Flask server listens on port `5001`. Keep the database container running while the app stores telemetry. To stop the database, run `docker compose -f src/docker-compose.yml down` from the repository root.

The telemetry endpoint pairs `accelerometer` and `gyroscope` entries that share the same phone sample time and stores them with a `device_timestamp`. The database `timestamp` column records when MySQL received the row. If the schema already exists, rerun `python -m src.init_db` after pulling schema changes so it can add the device timestamp column.

### Model definition and training

The first model uses a sliding window of 32 synchronized samples. Each sample has six input features in this order: `accel_x`, `accel_y`, `accel_z`, `gyro_x`, `gyro_y`, `gyro_z`. A GRU processes the window and predicts the orientation quaternion `(qx, qy, qz, qw)` at the final sample. The phone's `orientation` payload supplies this training target; the app stores it with the sensor row when the timestamps match.

Collect multiple phone sessions with `accelerometer`, `gyroscope`, and `orientation` entries enabled. Then initialize or migrate the schema and train the model:

```bash
python -m src.init_db
python -m src.train_model --window-size 32 --epochs 30
```

Training uses separate sessions for validation when multiple sessions are available. With one session, it uses an earlier time segment for training and a later segment for validation. A checkpoint is saved to `models/orientation_model.pt`. Restart the Flask server after training so it loads the checkpoint. During inference, Flask keeps a 32-sample in-memory window per phone session and returns `model_orientation_quaternion` once the window is full; until then `model_status` is `warming_up`. Without a checkpoint, `model_status` is `model_not_trained`.

The phone's quaternion is a fused orientation estimate. This initial model therefore learns to reproduce the phone's estimate. To measure actual drift correction accuracy, collect orientation labels from an independent reference system and compare against it.

### Run inference on stored data

With MySQL running and the Python dependencies installed, select an inclusive UTC range of device sample timestamps:

```bash
python -m src.infer_from_database "2026-11-02T14:30:00Z" "2026-11-02T14:31:00Z"
```

The script reads complete paired accel/gyro rows in that range, builds the same rolling windows, and prints predicted quaternions after training. Replace the example times with the range you want to inspect. It requires the checkpoint created by `python -m src.train_model`.
