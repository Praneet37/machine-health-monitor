/*
  machines.js
  ------------
  Powers the Machines page: loads the full machine health table
  and lets the user click a row to open that machine's detail page.
*/

document.addEventListener("DOMContentLoaded", () => {
    loadMachineTable();
});

async function loadMachineTable() {
    const tbody = document.getElementById("machines-tbody");
    try {
        const res = await fetch("/api/machines");
        const machines = await res.json();

        tbody.innerHTML = "";

        machines.forEach((m) => {
            const row = document.createElement("tr");
            row.addEventListener("click", () => {
                window.location.href = `/machines/${m.id}`;
            });

            row.innerHTML = `
                <td>#${String(m.id).padStart(3, "0")}</td>
                <td><strong>${m.name}</strong><br><span style="color:#90A4AE; font-size:11.5px;">${m.machine_type}</span></td>
                <td>${m.temperature ?? "-"} °C</td>
                <td>${m.vibration ?? "-"} mm/s</td>
                <td>${m.pressure ?? "-"} PSI</td>
                <td>${m.rpm ?? "-"} RPM</td>
                <td>${m.health_score ?? "-"}%</td>
                <td>${m.status}</td>
                <td><span class="badge ${m.status}">${m.status}</span></td>
            `;
            tbody.appendChild(row);
        });

        if (machines.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:#90A4AE;">No machines found.</td></tr>`;
        }
    } catch (err) {
        console.error("Failed to load machines:", err);
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color:#C62828;">Failed to load machine data.</td></tr>`;
    }
}