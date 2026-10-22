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
1. Start the isolated MySQL database container infrastructure:
   ```bash
   docker-compose up -d
   ```
2. Auto-initialize the relational relational schema tables:
   ```bash
   python init_db.py
   ```
3. Run the live ingestion server pipeline:
   ```bash
   python app.py
   ```
