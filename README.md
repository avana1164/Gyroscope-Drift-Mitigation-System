# Real-Time Spatial Telemetry Pipeline for Automated Ultrasound Training

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

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
docker compose -f src/docker-compose.yml up -d
python -m src.init_db
python -m src.app
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
docker compose -f src/docker-compose.yml up -d
python -m src.init_db
python -m src.app
```

If PowerShell blocks virtual environment activation, use Command Prompt instead and activate with `.venv\Scripts\activate.bat`.

The Flask server listens on port `5001`. Keep the database container running while the app stores telemetry. To stop the database, run `docker compose -f src/docker-compose.yml down` from the repository root.
