"""
seed_data.py
------------
Populates the database with sample machines and simulated sensor
reading history, since there's no real hardware. Run this once
after the database is created (app.py calls it automatically if
the machines table is empty).
"""

import random
from datetime import datetime, timedelta
from models import get_connection, now_str
from ai_predictor import predict_health

MACHINE_NAMES = [
    ("Compressor Unit A1", "Air Compressor"),
    ("Conveyor Motor B2", "Conveyor Motor"),
    ("Hydraulic Press C1", "Hydraulic Press"),
    ("CNC Spindle D3", "CNC Machine"),
    ("Cooling Pump E2", "Water Pump"),
    ("Turbine Generator F1", "Turbine"),
    ("Packaging Robot G4", "Robotic Arm"),
    ("Boiler Unit H1", "Boiler"),
]


def _simulate_reading(base_temp, base_vib, base_pressure, base_rpm, drift):
    """Generate one simulated sensor reading with some random noise,
    plus a 'drift' factor to simulate gradual degradation for some machines."""
    return {
        "temperature": round(base_temp + drift * 15 + random.uniform(-2, 2), 1),
        "vibration": round(base_vib + drift * 3 + random.uniform(-0.3, 0.3), 2),
        "pressure": round(base_pressure + drift * 10 + random.uniform(-3, 3), 1),
        "rpm": round(base_rpm - drift * 400 + random.uniform(-50, 50), 0),
    }


def seed_machines_and_readings():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as cnt FROM machines")
    if cur.fetchone()["cnt"] > 0:
        conn.close()
        return  # Already seeded

    for name, mtype in MACHINE_NAMES:
        installed_date = (datetime.now() - timedelta(days=random.randint(200, 900))).strftime("%Y-%m-%d")
        cur.execute(
            "INSERT INTO machines (name, machine_type, installed_date) VALUES (?, ?, ?)",
            (name, mtype, installed_date)
        )
        machine_id = cur.lastrowid

        # Give ~30% of machines a "degrading" drift trend to create realistic
        # variety across Healthy / Warning / Critical statuses.
        drift_trend = random.choice([0, 0, 0, 0.3, 0.6, 0.9])

        # Generate 20 historical readings, most recent last, with a gentle
        # upward drift trend if drift_trend > 0 (simulating wear over time)
        last_reading = None
        for i in range(20):
            progress = i / 19  # 0 -> 1 across the history
            current_drift = drift_trend * progress
            reading = _simulate_reading(60, 1.5, 55, 1800, current_drift)
            timestamp = (datetime.now() - timedelta(hours=(20 - i) * 6)).strftime("%Y-%m-%d %H:%M:%S")

            cur.execute("""
                INSERT INTO sensor_readings
                (machine_id, temperature, vibration, pressure, rpm, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (machine_id, reading["temperature"], reading["vibration"],
                  reading["pressure"], reading["rpm"], timestamp))

            last_reading = reading

        # Run the AI predictor on the latest reading and store the prediction
        result = predict_health(
            last_reading["temperature"], last_reading["vibration"],
            last_reading["pressure"], last_reading["rpm"]
        )
        cur.execute("""
            INSERT INTO predictions
            (machine_id, health_score, status, failure_probability,
             confidence, rul_days, recommended_action, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (machine_id, result["health_score"], result["status"],
              result["failure_probability"], result["confidence"],
              result["rul_days"], result["suggested_action"], now_str()))

    conn.commit()
    conn.close()
    print(f"Seeded {len(MACHINE_NAMES)} machines with sample sensor history.")