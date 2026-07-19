"""
models.py
----------
Handles all SQLite database setup and helper functions.
We use plain sqlite3 (no ORM) to keep things simple and beginner-friendly.
"""

import sqlite3
import os
from datetime import datetime

# Path to the SQLite database file (stored in /database)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "machine_health.db")
# Ensure the database folder exists (Git doesn't track empty folders,
# so this guarantees it's created fresh on any new deployment)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_connection():
    """Create and return a new database connection.
    row_factory lets us access columns by name (like a dict)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all required tables if they don't already exist."""
    conn = get_connection()
    cur = conn.cursor()

    # Users table - simple login credentials
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Machines table - basic machine info
    cur.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            machine_type TEXT NOT NULL,
            installed_date TEXT NOT NULL
        )
    """)

    # Sensor readings - historical simulated sensor data per machine
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id INTEGER NOT NULL,
            temperature REAL NOT NULL,
            vibration REAL NOT NULL,
            pressure REAL NOT NULL,
            rpm REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (machine_id) REFERENCES machines (id)
        )
    """)

    # Predictions - latest AI prediction result per machine
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id INTEGER NOT NULL,
            health_score REAL NOT NULL,
            status TEXT NOT NULL,
            failure_probability REAL NOT NULL,
            confidence REAL NOT NULL,
            rul_days INTEGER NOT NULL,
            recommended_action TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (machine_id) REFERENCES machines (id)
        )
    """)

    conn.commit()
    conn.close()


def seed_default_user():
    """Insert a default demo login (username: admin / password: admin123)
    only if no users exist yet."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM users")
    if cur.fetchone()["cnt"] == 0:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )
        conn.commit()
    conn.close()


def now_str():
    """Helper to get current timestamp as a string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")