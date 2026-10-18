#include <Wire.h>

const uint8_t MPU_ADDR = 0x68;
const unsigned long SAMPLE_INTERVAL_MS = 50;  // 20 samples per second

enum ProbeStatus : uint8_t {
  STATUS_UNKNOWN,
  STATUS_OK,
  STATUS_ADJUST,
  STATUS_SENSOR_ERROR
};

unsigned long lastSampleMs = 0;
ProbeStatus previousStatus = STATUS_UNKNOWN;

// -----------------------------
// DEMO THRESHOLDS
// Change these experimentally
// -----------------------------

// Maximum comfortable rotational speed
const float MAX_GYRO = 30.0;   // degrees/second

// Maximum acceleration change
const float MAX_ACCEL_CHANGE = 0.30;  // g

// Desired probe orientation
const float TARGET_ROLL = 0.0;
const float TARGET_PITCH = 0.0;

// Allowed orientation error
const float ANGLE_TOLERANCE = 15.0;


// Previous acceleration
float previousAx = 0;
float previousAy = 0;
float previousAz = 1;


// ----------------------------------
// Read MPU-6050
// ----------------------------------

bool readMPU(
  int16_t &ax,
  int16_t &ay,
  int16_t &az,
  int16_t &gx,
  int16_t &gy,
  int16_t &gz
) {


  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);

  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  if (Wire.requestFrom(MPU_ADDR, (uint8_t)14, true) != 14) {
    return false;
  }

  ax = (Wire.read() << 8) | Wire.read();
  ay = (Wire.read() << 8) | Wire.read();
  az = (Wire.read() << 8) | Wire.read();

  // Temperature
  Wire.read();
  Wire.read();

  gx = (Wire.read() << 8) | Wire.read();
  gy = (Wire.read() << 8) | Wire.read();
  gz = (Wire.read() << 8) | Wire.read();

  return true;
}


// ----------------------------------
// Setup
// ----------------------------------

void setup() {

  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);

  delay(1000);

  // Wake MPU-6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission();

  // Gyroscope ±250 deg/s
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1B);
  Wire.write(0);
  Wire.endTransmission();

  // Accelerometer ±2g
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1C);
  Wire.write(0);
  Wire.endTransmission();

  Serial.println("================================");
  Serial.println(" Ultrasound Probe Monitor");
  Serial.println("================================");
  Serial.println();

  delay(1000);
}


// ----------------------------------
// Main loop
// ----------------------------------

void loop() {

  unsigned long now = millis();
  if (now - lastSampleMs < SAMPLE_INTERVAL_MS) {
    return;
  }
  lastSampleMs = now;

  int16_t rawAx, rawAy, rawAz;
  int16_t rawGx, rawGy, rawGz;

  if (!readMPU(
        rawAx,
        rawAy,
        rawAz,
        rawGx,
        rawGy,
        rawGz
      )) {

    if (previousStatus != STATUS_SENSOR_ERROR) {
      Serial.println("SENSOR ERROR");
      previousStatus = STATUS_SENSOR_ERROR;
    }
    return;
  }


  // ----------------------------------
  // Convert accelerometer
  // ----------------------------------

  float ax = rawAx / 16384.0;
  float ay = rawAy / 16384.0;
  float az = rawAz / 16384.0;


  // ----------------------------------
  // Convert gyroscope
  // ----------------------------------

  float gx = rawGx / 131.0;
  float gy = rawGy / 131.0;
  float gz = rawGz / 131.0;


  // ----------------------------------
  // Calculate orientation
  // ----------------------------------

  float roll =
    atan2(ay, az) * 180.0 / PI;

  float pitch =
    atan2(
      -ax,
      sqrt(ay * ay + az * az)
    ) * 180.0 / PI;


  // ----------------------------------
  // Calculate acceleration change
  // ----------------------------------

  float accelerationChange =
    sqrt(
      (ax - previousAx)*(ax - previousAx) +
      (ay - previousAy)*(ay - previousAy) +
      (az - previousAz)*(az - previousAz)
    );

  previousAx = ax;
  previousAy = ay;
  previousAz = az;


  // ----------------------------------
  // Calculate rotation speed
  // ----------------------------------

  float rotationSpeed =
    sqrt(
      gx * gx +
      gy * gy +
      gz * gz
    );


  // ==================================
  // ANGLE CHECK
  // ==================================
  float rollError =
    abs(roll - TARGET_ROLL);

  float pitchError =
    abs(pitch - TARGET_PITCH);


  // ==================================
  // OVERALL STATUS
  // ==================================

  bool movementOK =
    accelerationChange <= MAX_ACCEL_CHANGE;

  bool rotationOK =
    rotationSpeed <= MAX_GYRO;

  bool angleOK =
    rollError <= ANGLE_TOLERANCE &&
    pitchError <= ANGLE_TOLERANCE;


  ProbeStatus status = (movementOK && rotationOK && angleOK)
                         ? STATUS_OK
                         : STATUS_ADJUST;

  if (status != previousStatus) {
    Serial.println(status == STATUS_OK ? "OK" : "ADJUST PROBE");
    previousStatus = status;
  }
}
