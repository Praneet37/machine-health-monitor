/*
  machine_detail.js
  -------------------
  Powers the individual Machine Details page:
    - Loads sensor history + latest AI prediction
    - Renders 4 Chart.js line/bar charts (Temp, Vibration, Pressure, RPM)
    - Shows AI Health Score, Failure Probability, RUL, Recommended Maintenance
    - Supports both auto-refresh (simulated live data) and a manual
      "Refresh Now" button, per project requirements.

  Expects a global `MACHINE_ID` variable to be set by machine_detail.html
*/

let tempChart, vibChart, pressureChart, rpmChart;
const AUTO_REFRESH_INTERVAL_MS = 8000; // auto-refresh every 8 seconds

document.addEventListener("DOMContentLoaded", () => {
    loadMachineDetail();

    document.getElementById("refresh-btn").addEventListener("click", () => {
        simulateNewReading();
    });

    // Auto-refresh loop
    setInterval(() => {
        simulateNewReading();
    }, AUTO_REFRESH_INTERVAL_MS);
});

// ---------------------------------------------------------------
// Initial load: full history + charts + AI panel
// ---------------------------------------------------------------
async function loadMachineDetail() {
    try {
        const res = await fetch(`/api/machines/${MACHINE_ID}`);
        const data = await res.json();

        document.getElementById("machine-name").textContent = data.machine.name;
        document.getElementById("machine-type").textContent = data.machine.machine_type;
        document.getElementById("machine-installed").textContent = data.machine.installed_date;

        renderAllCharts(data.history);
        updateAIPanel(data.prediction);
        updateLatestMetrics(data.history[data.history.length - 1]);
    } catch (err) {
        console.error("Failed to load machine detail:", err);
    }
}

// ---------------------------------------------------------------
// Simulate a new live reading (auto-refresh + manual button both call this)
// ---------------------------------------------------------------
async function simulateNewReading() {
    try {
        const res = await fetch(`/api/machines/${MACHINE_ID}/simulate`, { method: "POST" });
        const data = await res.json();

        appendReadingToCharts(data.reading);
        updateAIPanel(data.prediction);
        updateLatestMetrics(data.reading);
        flashRefreshIndicator();
    } catch (err) {
        console.error("Failed to simulate new reading:", err);
    }
}

// ---------------------------------------------------------------
// Chart rendering
// ---------------------------------------------------------------
function renderAllCharts(history) {
    const labels = history.map((h) => formatTime(h.timestamp));

    tempChart = makeLineChart("tempChart", labels, history.map((h) => h.temperature), "Temperature (°C)", "#0288D1");
    vibChart = makeLineChart("vibChart", labels, history.map((h) => h.vibration), "Vibration (mm/s)", "#F9A825");
    pressureChart = makeLineChart("pressureChart", labels, history.map((h) => h.pressure), "Pressure (PSI)", "#4FC3F7");
    rpmChart = makeBarChart("rpmChart", labels, history.map((h) => h.rpm), "RPM", "#26A69A");
}

function makeLineChart(canvasId, labels, data, label, color) {
    const ctx = document.getElementById(canvasId);
    return new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label, data,
                borderColor: color,
                backgroundColor: color + "22",
                fill: true, tension: 0.35, pointRadius: 2
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });
}

function makeBarChart(canvasId, labels, data, label, color) {
    const ctx = document.getElementById(canvasId);
    return new Chart(ctx, {
        type: "bar",
        data: { labels, datasets: [{ label, data, backgroundColor: color, borderRadius: 5 }] },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });
}

// Append one new point to each chart, keeping a rolling window of 20 points
function appendReadingToCharts(reading) {
    const time = formatTime(reading.timestamp);
    [ [tempChart, reading.temperature], [vibChart, reading.vibration],
      [pressureChart, reading.pressure], [rpmChart, reading.rpm] ].forEach(([chart, value]) => {
        if (!chart) return;
        chart.data.labels.push(time);
        chart.data.datasets[0].data.push(value);
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        chart.update();
    });
}

// ---------------------------------------------------------------
// AI Prediction panel + top metric boxes
// ---------------------------------------------------------------
function updateAIPanel(prediction) {
    if (!prediction) return;

    const status = prediction.status;
    document.getElementById("ai-health-score").textContent = `${prediction.health_score}%`;
    document.getElementById("ai-failure-prob").textContent = `${prediction.failure_probability}%`;
    document.getElementById("ai-rul").textContent = `${prediction.rul_days} days`;
    document.getElementById("ai-confidence").textContent = `${prediction.confidence}%`;
    document.getElementById("ai-recommendation").textContent =
        prediction.suggested_action || prediction.recommended_action;

    const badge = document.getElementById("ai-status-badge");
    badge.textContent = status;
    badge.className = `badge ${status}`;
}

function updateLatestMetrics(reading) {
    if (!reading) return;
    document.getElementById("metric-temp").textContent = `${reading.temperature} °C`;
    document.getElementById("metric-vib").textContent = `${reading.vibration} mm/s`;
    document.getElementById("metric-pressure").textContent = `${reading.pressure} PSI`;
    document.getElementById("metric-rpm").textContent = `${reading.rpm} RPM`;
}

// Small visual cue on the refresh button when new data lands
function flashRefreshIndicator() {
    const btn = document.getElementById("refresh-btn");
    btn.textContent = "✓ Updated";
    setTimeout(() => { btn.textContent = "🔄 Refresh Now"; }, 1200);
}

function formatTime(timestamp) {
    const parts = timestamp.split(" ");
    return parts[1] ? parts[1].slice(0, 5) : timestamp;
}