/*
  reports.js
  -----------
  Powers the Reports page: fetches maintenance report data for all
  machines and renders it as a table. Also supports a simple
  "Print / Export" action using the browser's print dialog, so
  reports can be saved as PDF without extra backend work.
*/

document.addEventListener("DOMContentLoaded", () => {
    loadReports();

    document.getElementById("export-btn").addEventListener("click", () => {
        window.print();
    });
});

async function loadReports() {
    const tbody = document.getElementById("reports-tbody");
    try {
        const res = await fetch("/api/reports");
        const reports = await res.json();

        tbody.innerHTML = "";
        reports.forEach((r) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td><strong>${r.machine_name}</strong><br><span style="color:#90A4AE; font-size:11.5px;">${r.machine_type}</span></td>
                <td><span class="badge ${r.status}">${r.status}</span></td>
                <td>${r.health_score ?? "-"}%</td>
                <td>${r.failure_probability ?? "-"}%</td>
                <td>${r.recommended_action}</td>
                <td>${r.date}</td>
            `;
            tbody.appendChild(row);
        });

        if (reports.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#90A4AE;">No report data available.</td></tr>`;
        }
    } catch (err) {
        console.error("Failed to load reports:", err);
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#C62828;">Failed to load reports.</td></tr>`;
    }
}