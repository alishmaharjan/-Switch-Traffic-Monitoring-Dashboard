import sqlite3

DB = "traffic.db"


def calculate_rates(interval=60):

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT interface
        FROM traffic
    """)

    interfaces = cur.fetchall()

    results = []

    for (interface,) in interfaces:

        cur.execute("""
            SELECT rx_bytes, tx_bytes
            FROM traffic
            WHERE interface=?
            ORDER BY id DESC
            LIMIT 2
        """, (interface,))

        rows = cur.fetchall()

        if len(rows) < 2:
            continue

        newest = rows[0]
        previous = rows[1]

        rx_delta = newest[0] - previous[0]
        tx_delta = newest[1] - previous[1]

        # Handle counter reset or rollover
        if rx_delta < 0:
            rx_delta = 0

        if tx_delta < 0:
            tx_delta = 0

        rx_mbps = (rx_delta * 8) / interval / 1_000_000
        tx_mbps = (tx_delta * 8) / interval / 1_000_000

        results.append({
            "interface": interface,
            "rx_mbps": round(rx_mbps, 2),
            "tx_mbps": round(tx_mbps, 2)
        })

    conn.close()

    return results


if __name__ == "__main__":

    rates = calculate_rates()

    for rate in rates:
        print(
            f"{rate['interface']:<25} "
            f"RX: {rate['rx_mbps']:>8.2f} Mbps   "
            f"TX: {rate['tx_mbps']:>8.2f} Mbps"
        )
