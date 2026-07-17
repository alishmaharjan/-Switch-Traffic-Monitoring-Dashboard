from flask import (
    Flask,
    jsonify,
    render_template,
    send_file,
    abort
)

from database import get_thruk_ports
from rrd_manager import generate_graph

import os

app = Flask(__name__)


# =====================================================
# Dashboard
# =====================================================

@app.route("/")
def index():
    return render_template("dashboard.html")


# =====================================================
# Interface API
# =====================================================

@app.route("/api/interfaces")
def interfaces():

    rows = get_thruk_ports()

    interfaces = []

    total_rx = 0
    total_tx = 0

    ports_up = 0
    ports_down = 0

    for row in rows:

        row = dict(row)

        rx = float(row["rx_mbps"] or 0)
        tx = float(row["tx_mbps"] or 0)

        total_rx += rx
        total_tx += tx

        if row["status"] == "UP":
            ports_up += 1
        else:
            ports_down += 1

        interfaces.append({

            "interface": row["interface"],

            "host": row["host"],

            "service": row["service"],

            "status": row["status"],

            "state": row["state"],

            "speed": int(row["speed"] or 0),

            "rx_mbps": round(rx, 3),

            "tx_mbps": round(tx, 3),

            "rx_util": round(float(row["rx_util"] or 0), 2),

            "tx_util": round(float(row["tx_util"] or 0), 2),

            "last_update": row["last_update"]

        })

    return jsonify({

        "summary": {

            "total_ports": len(interfaces),

            "ports_up": ports_up,

            "ports_down": ports_down,

            "total_rx": round(total_rx, 2),

            "total_tx": round(total_tx, 2)

        },

        "interfaces": interfaces

    })


# =====================================================
# RRD Graph API
# =====================================================

@app.route("/graph/<path:interface>/<period>")
def graph(interface, period):

    try:

        filename = generate_graph(interface, period)

        if not os.path.exists(filename):
            abort(404)

        return send_file(
            filename,
            mimetype="image/png",
            max_age=0
        )

    except Exception as e:

        print(e)

        abort(500)


# =====================================================
# Health Check
# =====================================================

@app.route("/health")
def health():

    return jsonify({

        "status": "ok"

    })


# =====================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )
