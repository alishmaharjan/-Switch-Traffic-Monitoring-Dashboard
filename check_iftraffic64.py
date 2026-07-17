#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os
import time

CACHE_DIR = "/tmp/check_iftraffic64"


def snmp_get(host, community, oid):

    cmd = [
        "snmpget",
        "-v2c",
        "-c", community,
        "-Ovq",
        host,
        oid
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("UNKNOWN - SNMP Error")
        sys.exit(3)

    return result.stdout.strip()


def read_cache(ifindex):

    os.makedirs(CACHE_DIR, exist_ok=True)

    filename = os.path.join(
        CACHE_DIR,
        f"{ifindex}.cache"
    )

    if not os.path.exists(filename):
        return None

    with open(filename) as f:
        data = f.read().strip().split(",")

    return (
        float(data[0]),
        int(data[1]),
        int(data[2])
    )


def write_cache(ifindex, rx, tx):

    os.makedirs(CACHE_DIR, exist_ok=True)

    filename = os.path.join(
        CACHE_DIR,
        f"{ifindex}.cache"
    )

    with open(filename, "w") as f:

        f.write(
            f"{time.time()},{rx},{tx}"
        )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("-H", required=True)
    parser.add_argument("-C", required=True)
    parser.add_argument("-i", required=True, type=int)

    parser.add_argument(
        "-w",
        "--warning",
        default=80,
        type=float
    )

    parser.add_argument(
        "-c",
        "--critical",
        default=95,
        type=float
    )

    args = parser.parse_args()

    idx = args.i

    rx_oid = f"1.3.6.1.2.1.31.1.1.1.6.{idx}"
    tx_oid = f"1.3.6.1.2.1.31.1.1.1.10.{idx}"
    status_oid = f"1.3.6.1.2.1.2.2.1.8.{idx}"
    speed_oid = f"1.3.6.1.2.1.31.1.1.1.15.{idx}"
    name_oid = f"1.3.6.1.2.1.2.2.1.2.{idx}"

    interface = snmp_get(args.H, args.C, name_oid)

    rx = int(snmp_get(args.H, args.C, rx_oid))
    tx = int(snmp_get(args.H, args.C, tx_oid))
    status = int(snmp_get(args.H, args.C, status_oid))
    speed = int(snmp_get(args.H, args.C, speed_oid))

    previous = read_cache(idx)

    rx_mbps = 0.0
    tx_mbps = 0.0
    rx_util = 0.0
    tx_util = 0.0

    if previous:

        old_time, old_rx, old_tx = previous

        interval = time.time() - old_time

        if interval > 0:

            rx_delta = max(0, rx - old_rx)
            tx_delta = max(0, tx - old_tx)

            rx_mbps = (rx_delta * 8) / interval / 1_000_000
            tx_mbps = (tx_delta * 8) / interval / 1_000_000

            if speed > 0:

                rx_util = (rx_mbps / speed) * 100
                tx_util = (tx_mbps / speed) * 100

    write_cache(idx, rx, tx)

    max_util = max(rx_util, tx_util)

    if status != 1:

        state = "CRITICAL"
        exitcode = 2

    elif max_util >= args.critical:

        state = "CRITICAL"
        exitcode = 2

    elif max_util >= args.warning:

        state = "WARNING"
        exitcode = 1

    else:

        state = "OK"
        exitcode = 0

    oper = "UP" if status == 1 else "DOWN"

    print(

        f"{state} - {interface} {oper} "

        f"RX={rx_mbps:.2f}Mbps "

        f"TX={tx_mbps:.2f}Mbps "

        f"Speed={speed}Mbps "

        f"RX Util={rx_util:.2f}% "

        f"TX Util={tx_util:.2f}% "

        "| "

        f"rx={rx_mbps:.2f};{args.warning};{args.critical};0;{speed} "

        f"tx={tx_mbps:.2f};{args.warning};{args.critical};0;{speed} "

        f"rx_util={rx_util:.2f}%;{args.warning};{args.critical};0;100 "

        f"tx_util={tx_util:.2f}%;{args.warning};{args.critical};0;100"

    )

    sys.exit(exitcode)


if __name__ == "__main__":
    main()
