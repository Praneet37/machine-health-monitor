\# AI-Based Predictive Machine Health Monitoring



A demonstration web application that monitors industrial machine health, predicts

possible failures using a rule-based AI engine, and displays everything through

a clean, responsive dashboard. All sensor data (temperature, vibration, pressure,

RPM) is simulated — no real hardware is required.



\---



\## Tech Stack



\- \*\*Frontend:\*\* HTML, CSS, JavaScript, Chart.js

\- \*\*Backend:\*\* Python Flask

\- \*\*Database:\*\* SQLite



\---



\## Project Structure

machine-health-monitor/

│

├── backend/

│   ├── app.py              # Flask app, routes, and REST API

│   ├── models.py           # SQLite schema + DB helper functions

│   ├── ai\_predictor.py     # Rule-based AI prediction engine

│   ├── seed\_data.py        # Generates sample machines + sensor history

│   └── requirements.txt

│

├── database/

│   └── machine\_health.db   # Created automatically on first run

│

├── static/

│   ├── css/style.css

│   ├── js/

│   │   ├── login.js

│   │   ├── dashboard.js

│   │   ├── machines.js

│   │   ├── machine\_detail.js

│   │   ├── predictions.js

│   │   └── reports.js

│   └── assets/icons/       # SVG icons used across the UI

│

├── templates/

│   ├── login.html

│   ├── dashboard.html

│   ├── machines.html

│   ├── machine\_detail.html

│   ├── predictions.html

│   ├── reports.html

│   └── settings.html

│

└── README.md

