/*
  predictions.js
  ---------------
  Powers the standalone "AI Prediction" tool page where a user
  manually types in sensor values and gets an instant AI health
  assessment via POST /api/predict.
*/

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("predict-form");
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        await runPrediction();
    });
});

async function runPrediction() {
    const payload = {
        temperature: document.getElementById("input-temp").value,
        vibration: document.getElementById("input-vib").value,
        pressure: document.getElementById("input-pressure").value,
        rpm: document.getElementById("input-rpm").value,
    };

    const resultBox = document.getElementById("result-box");
    const statusEl = document.getElementById("result-status");

    try {
        const res = await fetch("/api/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            alert(err.error || "Prediction failed. Please check your inputs.");
            return;
        }

        const result = await res.json();

        // Status banner
        statusEl.textContent = `${statusIcon(result.status)} ${result.status}`;
        statusEl.className = `result-status ${result.status}`;
        statusEl.style.background = statusBg(result.status);
        statusEl.style.color = statusText(result.status);

        document.getElementById("result-health-score").textContent = `${result.health_score}%`;
        document.getElementById("result-confidence").textContent = `${result.confidence}%`;
        document.getElementById("result-rul").textContent = `${result.rul_days} days`;
        document.getElementById("result-failure-prob").textContent = `${result.failure_probability}%`;
        document.getElementById("result-action").textContent = result.suggested_action;

        resultBox.classList.add("show");
    } catch (err) {
        console.error("Prediction request failed:", err);
        alert("Something went wrong. Please try again.");
    }
}

function statusIcon(status) {
    if (status === "Healthy") return "✔";
    if (status === "Warning") return "⚠";
    return "⛔";
}
function statusBg(status) {
    if (status === "Healthy") return "#E8F5E9";
    if (status === "Warning") return "#FFF8E1";
    return "#FFEBEE";
}
function statusText(status) {
    if (status === "Healthy") return "#2E7D32";
    if (status === "Warning") return "#F9A825";
    return "#C62828";
}