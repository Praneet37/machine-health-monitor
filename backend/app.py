"""
app.py
------
Main Flask application. Handles page routing, session-based login,
and JSON API endpoints consumed by the frontend JavaScript.
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import os
import random

from models import init_db, get_connection, seed_default_user, now_str
from ai_predictor import predict_health
from seed_data import seed_machines_and_readings

app = Flask(__name__)
app.secret_key = "demo-secret-key-change-in-production"  # fine for a demo app


# ---------------------------------------------------------------------------
# Startup: create tables + seed demo data (only runs once, on first launch)
# ---------------------------------------------------------------------------
init_db()
seed_default_user()
seed_machines_and_readings()


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------
def login_required(view_func):
    """Simple decorator to protect pages behind login."""
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ---------------------------------------------------------------------------
# PAGE ROUTES (render HTML templates)
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username"))


@app.route("/machines")
@login_required
def machines_page():
    return render_template("machines.html", username=session.get("username"))


@app.route("/machines/<int:machine_id>")
@login_required
def machine_detail_page(machine_id):
    return render_template("machine_detail.html", username=session.get("username"), machine_id=machine_id)


@app.route("/predictions")
@login_required
def predictions_page():
    return render_template("predictions.html", username=session.get("username"))


@app.route("/reports")
@login_required
def reports_page():
    return render_template("reports.html", username=session.get("username"))


@app.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html", username=session.get("username"))


# ---------------------------------------------------------------------------
# API ROUTES (return JSON, consumed by static/js files)
# ---------------------------------------------------------------------------

def _latest_prediction(cur, machine_id):
    """Fetch the most recent prediction row for a machine."""
    cur.execute("""
        SELECT * FROM predictions WHERE machine_id = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (machine_id,))
    return cur.fetchone()


def _latest_reading(cur, machine_id):
    """Fetch the most recent sensor reading for a machine."""
    cur.execute("""
        SELECT * FROM sensor_readings WHERE machine_id = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (machine_id,))
    return cur.fetchone()


@app.route("/api/dashboard-summary")
@login_required
def api_dashboard_summary():
    """Returns counts for the summary cards + pie chart data."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM machines")
    machine_ids = [row["id"] for row in cur.fetchall()]

    counts = {"Healthy": 0, "Warning": 0, "Critical": 0}
    for mid in machine_ids:
        pred = _latest_prediction(cur, mid)
        if pred:
            counts[pred["status"]] += 1

    conn.close()
    return jsonify({
        "total_machines": len(machine_ids),
        "healthy": counts["Healthy"],
        "warning": counts["Warning"],
        "critical": counts["Critical"]
    })


@app.route("/api/machines")
@login_required
def api_machines():
    """Returns the full machine health table data."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM machines ORDER BY id")
    machines = cur.fetchall()

    result = []
    for m in machines:
        reading = _latest_reading(cur, m["id"])
        pred = _latest_prediction(cur, m["id"])
        result.append({
            "id": m["id"],
            "name": m["name"],
            "machine_type": m["machine_type"],
            "temperature": reading["temperature"] if reading else None,
            "vibration": reading["vibration"] if reading else None,
            "pressure": reading["pressure"] if reading else None,
            "rpm": reading["rpm"] if reading else None,
            "health_score": pred["health_score"] if pred else None,
            "status": pred["status"] if pred else "Unknown",
            "failure_probability": pred["failure_probability"] if pred else None,
        })

    conn.close()
    return jsonify(result)


@app.route("/api/machines/<int:machine_id>")
@login_required
def api_machine_detail(machine_id):
    """Returns full details for one machine, including sensor history
    (for graphs) and the latest AI prediction."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM machines WHERE id = ?", (machine_id,))
    machine = cur.fetchone()
    if not machine:
        conn.close()
        return jsonify({"error": "Machine not found"}), 404

    cur.execute("""
        SELECT temperature, vibration, pressure, rpm, timestamp
        FROM sensor_readings WHERE machine_id = ?
        ORDER BY timestamp ASC
    """, (machine_id,))
    history = [dict(row) for row in cur.fetchall()]

    pred = _latest_prediction(cur, machine_id)
    conn.close()

    return jsonify({
        "machine": dict(machine),
        "history": history,
        "prediction": dict(pred) if pred else None
    })


@app.route("/api/machines/<int:machine_id>/simulate", methods=["POST"])
@login_required
def api_simulate_reading(machine_id):
    """
    Simulates a NEW live sensor reading for a machine, runs it through
    the AI predictor, and stores both. This is what powers the
    'refresh data' / real-time feel of the demo.
    """
    conn = get_connection()
    cur = conn.cursor()

    last = _latest_reading(cur, machine_id)
    if last:
        # Small random walk from the last reading, occasionally with a spike,
        # to simulate realistic sensor fluctuation.
        spike = random.random() < 0.15  # 15% chance of an anomalous spike
        multiplier = random.uniform(1.15, 1.4) if spike else 1.0

        temperature = round(last["temperature"] * multiplier + random.uniform(-1.5, 1.5), 1)
        vibration = round(last["vibration"] * multiplier + random.uniform(-0.2, 0.2), 2)
        pressure = round(last["pressure"] * multiplier + random.uniform(-2, 2), 1)
        rpm = round(last["rpm"] + random.uniform(-60, 60), 0)
    else:
        temperature, vibration, pressure, rpm = 60.0, 1.5, 55.0, 1800.0

    timestamp = now_str()
    cur.execute("""
        INSERT INTO sensor_readings (machine_id, temperature, vibration, pressure, rpm, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (machine_id, temperature, vibration, pressure, rpm, timestamp))

    result = predict_health(temperature, vibration, pressure, rpm)
    cur.execute("""
        INSERT INTO predictions
        (machine_id, health_score, status, failure_probability,
         confidence, rul_days, recommended_action, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (machine_id, result["health_score"], result["status"],
          result["failure_probability"], result["confidence"],
          result["rul_days"], result["suggested_action"], timestamp))

    conn.commit()
    conn.close()

    return jsonify({
        "reading": {
            "temperature": temperature, "vibration": vibration,
            "pressure": pressure, "rpm": rpm, "timestamp": timestamp
        },
        "prediction": result
    })


@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    """
    Standalone AI Prediction endpoint (used by the 'Predictions' page)
    where a user manually inputs sensor values and gets an instant
    AI health assessment, not tied to any stored machine.
    """
    data = request.get_json()
    try:
        temperature = float(data.get("temperature"))
        vibration = float(data.get("vibration"))
        pressure = float(data.get("pressure"))
        rpm = float(data.get("rpm"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid sensor input"}), 400

    result = predict_health(temperature, vibration, pressure, rpm)
    return jsonify(result)


@app.route("/api/reports")
@login_required
def api_reports():
    """Returns maintenance report data: one row per machine with its
    current status, AI prediction, and recommendation."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM machines ORDER BY id")
    machines = cur.fetchall()

    report = []
    for m in machines:
        pred = _latest_prediction(cur, m["id"])
        report.append({
            "machine_name": m["name"],
            "machine_type": m["machine_type"],
            "status": pred["status"] if pred else "Unknown",
            "health_score": pred["health_score"] if pred else None,
            "failure_probability": pred["failure_probability"] if pred else None,
            "recommended_action": pred["recommended_action"] if pred else "N/A",
            "date": pred["timestamp"] if pred else "N/A",
        })

    conn.close()
    return jsonify(report)


if __name__ == "__main__":
    app.run(debug=True, port=5000)