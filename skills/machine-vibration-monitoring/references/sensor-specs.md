# STWIN.box Sensor Specifications

## IIS3DWB — Wideband 3-Axis Accelerometer

| Parameter | Value |
|---|---|
| Type | 3-axis MEMS accelerometer |
| Bandwidth | Up to 6.3 kHz (flat), usable to ~13 kHz |
| ODR (Output Data Rate) | 26667 Hz |
| Full-scale range | ±2g, ±4g, ±8g, ±16g |
| Noise density | 75 µg/√Hz |
| Sensitivity | 0.061 mg/LSB (±2g) |
| Best for | Bearing fault detection, high-frequency vibration |

### Recommended settings for vibration monitoring:
- **ODR**: 26667 Hz (fixed — only available rate)
- **Full scale**: ±4g for general machinery, ±16g for impacts
- **Duration**: ≥1 s for 1 Hz frequency resolution

## ISM330DHCX — 6-Axis IMU with MLC

| Parameter | Value |
|---|---|
| Type | 3-axis accel + 3-axis gyro |
| Accel ODR options | 12.5, 26, 52, 104, 208, 417, 833, 1667, 3333, 6667 Hz |
| Accel full-scale | ±2g, ±4g, ±8g, ±16g |
| Accel noise density | 70 µg/√Hz (high-performance mode) |
| Gyro ODR options | Same as accel |
| Gyro full-scale | ±125, ±250, ±500, ±1000, ±2000, ±4000 dps |
| MLC | Machine Learning Core for on-edge classification |
| Best for | General vibration, unbalance, misalignment detection |

### Recommended settings by application:
- **General vibration**: ODR 6667 Hz, ±4g
- **Low-speed machines (<120 RPM)**: ODR 833 Hz, ±2g
- **Medium machines**: ODR 3333 Hz, ±4g

## IIS2ICLX — High-Accuracy Inclinometer

| Parameter | Value |
|---|---|
| Type | 2-axis (pitch + roll) |
| Range | ±0.5g, ±1g, ±2g, ±3g |
| ODR | 12.5, 26, 52, 104, 208, 416, 833 Hz |
| Noise | 30 µg/√Hz |
| Best for | Structural tilt monitoring, foundation checks |

## STTS22H — Temperature Sensor

| Parameter | Value |
|---|---|
| Range | -40 to +125 °C |
| Accuracy | ±0.5 °C |
| ODR | 1, 25, 50, 100, 200 Hz |
| Best for | Thermal monitoring, correlating temp with vibration |

## ILPS22QS — Pressure Sensor

| Parameter | Value |
|---|---|
| Range | 260–1260 hPa |
| Accuracy | ±0.5 hPa |
| ODR | 1, 4, 10, 25, 50, 75, 100, 200 Hz |
| Best for | Environmental pressure monitoring |

## IMP23ABSU — Analog MEMS Microphone

| Parameter | Value |
|---|---|
| Bandwidth | 100 Hz – 80 kHz |
| SNR | 64 dB |
| AOP | 130 dB SPL |
| Best for | Acoustic emission, ultrasound leak detection |

## Sensor Selection Guide by Use Case

| Use Case | Primary Sensor | ODR | Duration |
|---|---|---|---|
| Bearing fault detection | IIS3DWB | 26667 Hz | ≥2 s |
| Unbalance / misalignment | ISM330DHCX | 6667 Hz | ≥2 s |
| Low-speed machines | ISM330DHCX | 833 Hz | ≥5 s |
| Structural health | IIS2ICLX | 104 Hz | ≥10 s |
| Acoustic emission | IMP23ABSU | 192000 Hz | ≥1 s |
| Temperature trending | STTS22H | 1 Hz | continuous |
