let currentInterface = null;
let currentPeriod = "24h";

const GRAPH_REFRESH = 30000;
const TABLE_REFRESH = 30000;

// ===============================================
// Load Dashboard
// ===============================================

async function loadDashboard() {

    try {

        const res = await fetch("/api/interfaces");
        const data = await res.json();

        // Summary

        document.getElementById("totalPorts").textContent =
            data.summary.total_ports;

        document.getElementById("portsUp").textContent =
            data.summary.ports_up;

        document.getElementById("portsDown").textContent =
            data.summary.ports_down;

        document.getElementById("totalRx").textContent =
            data.summary.total_rx.toFixed(2) + " Mbps";

        document.getElementById("totalTx").textContent =
            data.summary.total_tx.toFixed(2) + " Mbps";

        document.getElementById("lastUpdate").textContent =
            new Date().toLocaleTimeString();

        renderTable(data.interfaces);

    }

    catch (e) {

        console.error(e);

    }

}

// ===============================================
// Render Table
// ===============================================

function renderTable(ports) {

    const tbody = document.getElementById("tableBody");

    tbody.innerHTML = "";

    const keyword =
        document.getElementById("search")
        .value
        .toLowerCase();

    ports.forEach(port => {

        if (!port.interface.toLowerCase().includes(keyword))
            return;

        let color = "greenFill";

        const util =
            Math.max(port.rx_util, port.tx_util);

        if (util >= 95)
            color = "redFill";

        else if (util >= 80)
            color = "yellowFill";

        tbody.innerHTML += `

<tr>

<td>${port.interface}</td>

<td>

<span class="status ${port.status=="UP"?"up":"down"}">

${port.status}

</span>

</td>

<td>

<span class="speed">

${port.speed} Mbps

</span>

</td>

<td>${port.rx_mbps.toFixed(3)}</td>

<td>${port.tx_mbps.toFixed(3)}</td>

<td>

<div class="bar">

<div class="fill ${color}"
style="width:${Math.min(port.rx_util,100)}%">

${port.rx_util.toFixed(2)}%

</div>

</div>

</td>

<td>

<div class="bar">

<div class="fill ${color}"
style="width:${Math.min(port.tx_util,100)}%">

${port.tx_util.toFixed(2)}%

</div>

</div>

</td>

<td>

<button class="graphBtn"
onclick="showGraph('${port.interface}')">

📈 View

</button>

</td>

</tr>

`;

    });

}

// ===============================================
// Popup
// ===============================================

function showGraph(iface) {

    currentInterface = iface;

    document.getElementById("graphTitle").textContent =
        iface;

    document.getElementById("graphModal").style.display =
        "flex";

    loadGraph("24h");

}

// ===============================================
// Load Graph
// ===============================================

function loadGraph(period) {

    currentPeriod = period;

    document
        .querySelectorAll(".graph-toolbar button")
        .forEach(btn => btn.classList.remove("active"));

    const active =
        document.getElementById("btn_" + period);

    if (active)
        active.classList.add("active");

    const img =
        document.getElementById("graphImage");

    img.style.opacity = "0.3";

    img.onload = function () {

        img.style.opacity = "1";

    };

    img.onerror = function () {

        img.style.opacity = "1";

        alert("Unable to generate graph.");

    };

    img.src =
        `/graph/${encodeURIComponent(currentInterface)}/${period}?t=${Date.now()}`;

}

// ===============================================
// Auto Refresh Graph
// ===============================================

function refreshGraph() {

    if (currentInterface == null)
        return;

    loadGraph(currentPeriod);

}

// ===============================================
// Close Popup
// ===============================================

function closeGraph() {

    document.getElementById("graphModal").style.display =
        "none";

    currentInterface = null;

}

// ===============================================
// Close if clicking outside
// ===============================================

window.onclick = function(e){

    const modal =
        document.getElementById("graphModal");

    if(e.target === modal)
        closeGraph();

}

// ===============================================

document
.getElementById("search")
.addEventListener("keyup",loadDashboard);

// ===============================================

loadDashboard();

setInterval(loadDashboard,TABLE_REFRESH);

setInterval(refreshGraph,GRAPH_REFRESH);
