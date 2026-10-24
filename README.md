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
