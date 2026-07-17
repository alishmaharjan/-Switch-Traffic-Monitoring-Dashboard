import logging
import re
import socket
import time

from database import (
    init_db,
    update_thruk_port
)

from rrd_manager import (
    update_rrd,
    generate_graph
)

# -----------------------------------------------------
# Configuration
# -----------------------------------------------------

SOCKET = "/var/cache/naemon/live"

POLL_INTERVAL = 30

QUERY = """GET services
Columns: host_name description state plugin_output
Filter: host_name = Office-huawei-switch
Filter: description ~~ Traffic

"""

# -----------------------------------------------------
# Logging
# -----------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("ThrukCollector")

# -----------------------------------------------------
# Livestatus
# -----------------------------------------------------

def livestatus():

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    client.settimeout(10)

    client.connect(SOCKET)

    client.sendall(QUERY.encode())

    data = b""

    while True:

        chunk = client.recv(8192)

        if not chunk:
            break

        data += chunk

    client.close()

    return data.decode()


# -----------------------------------------------------
# Parse one service
# -----------------------------------------------------

def parse(line):

    try:

        fields = line.split(";", 3)

        if len(fields) < 4:
            return None

        host = fields[0]
        service = fields[1]
        state = int(fields[2])
        output = fields[3]

        interface = service.replace(" Traffic", "")

        status = "UP" if " UP " in output else "DOWN"

        rx = float(
            re.search(r"RX=([\d.]+)", output).group(1)
        )

        tx = float(
            re.search(r"TX=([\d.]+)", output).group(1)
        )

        speed = int(
            re.search(r"Speed=(\d+)", output).group(1)
        )

        rx_util = float(
            re.search(r"RX Util=([\d.]+)", output).group(1)
        )

        tx_util = float(
            re.search(r"TX Util=([\d.]+)", output).group(1)
        )

        return {

            "interface": interface,

            "host": host,

            "service": service,

            "state": state,

            "status": status,

            "speed": speed,

            "rx": rx,

            "tx": tx,

            "rx_util": rx_util,

            "tx_util": tx_util

        }

    except Exception:

        logger.exception("Unable to parse service line")

        return None


# -----------------------------------------------------
# One polling cycle
# -----------------------------------------------------

def collect_once():

    logger.info("Collecting data from Thruk")

    data = livestatus()

    saved = 0

    for line in data.splitlines():

        if not line.strip():
            continue

        port = parse(line)

        if port is None:
            continue

        update_thruk_port(

            port["interface"],
            port["host"],
            port["service"],
            port["state"],
            port["status"],
            port["speed"],
            port["rx"],
            port["tx"],
            port["rx_util"],
            port["tx_util"]

        )

        update_rrd(

            port["interface"],
            port["rx"],
            port["tx"]

        )

        generate_graph(

            port["interface"]

        )

        saved += 1

        logger.info(
            "%-12s %-4s RX=%8.2f Mbps TX=%8.2f Mbps",
            port["interface"],
            port["status"],
            port["rx"],
            port["tx"]
        )

    logger.info(
        "Polling complete. Saved %d interfaces.",
        saved
    )


# -----------------------------------------------------
# Main Loop
# -----------------------------------------------------

def main():

    init_db()

    logger.info("=" * 60)
    logger.info("Huawei Thruk Collector Started")
    logger.info("Polling Interval : %d seconds", POLL_INTERVAL)
    logger.info("=" * 60)

    try:

        while True:

            start = time.time()

            try:

                collect_once()

            except Exception:

                logger.exception("Polling failed")

            elapsed = time.time() - start

            logger.info(
                "Completed in %.2f seconds",
                elapsed
            )

            sleep_time = max(0, POLL_INTERVAL - elapsed)

            time.sleep(sleep_time)

    except KeyboardInterrupt:

        logger.info("Collector stopped by user.")


# -----------------------------------------------------

if __name__ == "__main__":

    main()
