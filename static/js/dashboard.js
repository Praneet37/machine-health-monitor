/*
  dashboard.js
  -------------
  Powers the main Dashboard page:
    - Fetches summary counts for the 4 top cards
    - Fetches machine list for notifications + charts
    - Renders 3 Chart.js charts: Health Distribution (pie),
      Temperature Trend (line), Health Score Trend (bar)
*/

document.addEventListener("DOMContentLoaded", () => {
    loadSummaryCards();
    loadChartsAndNotifications();
});

// ---------------------------------------------------------------
// Summary cards: Total / Healthy / Warning / Critical
// ---------------------------------------------------------------
async function loadSummaryCards() {
    try {
        const res = await fetch("/api/dashboard-summary");
        const data = await res.json();

        document.getElementById("total-count").textContent = data.total_machines;
        document.getElementById("healthy-count").textContent = data.healthy;
        document.getElementById("warning-count").textContent = data.warning;
        document.getElementById("critical-count").textContent = data.critical;
    } catch (err) {
        console.error("Failed to load dashboard summary:", err);
    }
}

// ---------------------------------------------------------------
// Charts + Notifications (both driven by the machine list)
// ---------------------------------------------------------------
async function loadChartsAndNotifications() {
    try {
        const res = await fetch("/api/machines");
        const machines = await res.json();

        renderHealthDistributionChart(machines);
        renderHealthScoreChart(machines);
        await renderTemperatureTrendChart(machines);
        renderNotifications(machines);
    } catch (err) {
        console.error("Failed to load machine data:", err);
    }
}

// Pie chart: how many machines are Healthy / Warning / Critical
function renderHealthDistributionChart(machines) {
    const counts = { Healthy: 0, Warning: 0, Critical: 0 };
    machines.forEach((m) => { if (counts[m.status] !== undefined) counts[m.status]++; });

    const ctx = document.getElementById("healthDistributionChart");
    new Chart(ctx, {
        type: "pie",
        data: {
            labels: ["Healthy", "Warning", "Critical"],
            datasets: [{
                data: [counts.Healthy, counts.Warning, counts.Critical],
                backgroundColor: ["#2E7D32", "#F9A825", "#C62828"],
                borderWidth: 2,
                borderColor: "#fff"
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 12 } } } }
        }
    });
}

// Bar chart: current health score per machine
function renderHealthScoreChart(machines) {
    const ctx = document.getElementById("healthScoreChart");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: machines.map((m) => m.name),
            datasets: [{
                label: "Health Score",
                data: machines.map((m) => m.health_score),
                backgroundColor: machines.map((m) => statusColor(m.status)),
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            scales: { y: { beginAtZero: true, max: 100 } },
            plugins: { legend: { display: false } }
        }
    });
}

// Line chart: temperature history, using the first machine's history
// as a representative live trend line for the dashboard overview.
async function renderTemperatureTrendChart(machines) {
    if (machines.length === 0) return;

    const res = await fetch(`/api/machines/${machines[0].id}`);
    const detail = await res.json();
    const history = detail.history;

    const ctx = document.getElementById("temperatureTrendChart");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: history.map((h) => formatTime(h.timestamp)),
            datasets: [{
                label: `Temperature (${machines[0].name})`,
                data: history.map((h) => h.temperature),
                borderColor: "#0288D1",
                backgroundColor: "rgba(79, 195, 247, 0.15)",
                fill: true,
                tension: 0.35,
                pointRadius: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true, position: "bottom" } }
        }
    });
}

// ---------------------------------------------------------------
// Notifications panel — generated from current machine statuses
// ---------------------------------------------------------------
function renderNotifications(machines) {
    const container = document.getElementById("notif-list");
    container.innerHTML = "";

    machines.forEach((m) => {
        let items = [];

        if (m.status === "Critical") {
            if (m.temperature > 85) items.push({ text: `${m.name}: High Temperature Detected`, type: "critical", icon: "⚠" });
            if (m.vibration > 4.5) items.push({ text: `${m.name}: Excessive Vibration`, type: "critical", icon: "⚠" });
            if (items.length === 0) items.push({ text: `${m.name}: Critical condition detected`, type: "critical", icon: "⚠" });
        } else if (m.status === "Warning") {
            items.push({ text: `${m.name}: Maintenance Required Soon`, type: "warn", icon: "⚠" });
        } else {
            items.push({ text: `${m.name}: Machine Operating Normally`, type: "ok", icon: "✔" });
        }

        items.forEach((item) => {
            const div = document.createElement("div");
            div.className = `notif-item ${item.type}`;
            div.innerHTML = `<span>${item.icon}</span><span>${item.text}</span>`;
            container.appendChild(div);
        });
    });
}

// ---------------------------------------------------------------
// Shared helpers (also used by other JS files)
// ---------------------------------------------------------------
function statusColor(status) {
    if (status === "Healthy") return "#4FC3F7";
    if (status === "Warning") return "#F9A825";
    if (status === "Critical") return "#C62828";
    return "#B0BEC5";
}

function formatTime(timestamp) {
    // "2026-07-19 14:00:00" -> "14:00"
    const parts = timestamp.split(" ");
    return parts[1] ? parts[1].slice(0, 5) : timestamp;
}