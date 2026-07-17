import asyncio
import time

from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    walk_cmd
)

from database import (
    init_db,
    insert_counter,
    get_last_counter,
    insert_rate,
    update_interface
)

SWITCH_IP = "192.168.200.2"
COMMUNITY = "admin123"
POLL_INTERVAL = 60


async def walk(oid):
    engine = SnmpEngine()

    target = await UdpTransportTarget.create(
        (SWITCH_IP, 161)
    )

    results = {}

    async for (
        errorIndication,
        errorStatus,
        errorIndex,
        varBinds
    ) in walk_cmd(
        engine,
        CommunityData(COMMUNITY, mpModel=1),
        target,
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False
    ):

        if errorIndication:
            print(errorIndication)
            return {}

        if errorStatus:
            print(errorStatus.prettyPrint())
            return {}

        for name, value in varBinds:

            index = int(str(name).split(".")[-1])

            try:
                results[index] = int(value)
            except Exception:
                results[index] = str(value)

    return results


async def collect():

    init_db()

    print("=" * 50)
    print("Huawei SNMP Collector")
    print("=" * 50)

    # Discover interface names only once
    names = await walk(
        "1.3.6.1.2.1.2.2.1.2"
    )

    print(f"Discovered {len(names)} interfaces\n")

    while True:

        start = time.time()

        # Traffic counters
        rx = await walk(
            "1.3.6.1.2.1.31.1.1.1.6"
        )

        tx = await walk(
            "1.3.6.1.2.1.31.1.1.1.10"
        )

        # Interface speed (Mbps)
        speed = await walk(
            "1.3.6.1.2.1.31.1.1.1.15"
        )

        # Admin status
        admin = await walk(
            "1.3.6.1.2.1.2.2.1.7"
        )

        # Operational status
        oper = await walk(
            "1.3.6.1.2.1.2.2.1.8"
        )

        saved = 0

        for index, interface in names.items():

            if not interface.startswith("GigabitEthernet"):
                continue

            current_rx = rx.get(index, 0)
            current_tx = tx.get(index, 0)

            interface_speed = speed.get(index, 1000)

            admin_status = admin.get(index, 2)
            oper_status = oper.get(index, 2)

            update_interface(
                interface,
                index,
                interface_speed,
                admin_status,
                oper_status
            )

            previous = get_last_counter(interface)

            if previous is not None:

                prev_rx = previous[0]
                prev_tx = previous[1]

                rx_delta = current_rx - prev_rx
                tx_delta = current_tx - prev_tx

                if rx_delta < 0:
                    rx_delta = 0

                if tx_delta < 0:
                    tx_delta = 0

                rx_mbps = (
                    rx_delta * 8
                ) / POLL_INTERVAL / 1_000_000

                tx_mbps = (
                    tx_delta * 8
                ) / POLL_INTERVAL / 1_000_000

                if interface_speed > 0:
                    rx_util = (rx_mbps / interface_speed) * 100
                    tx_util = (tx_mbps / interface_speed) * 100
                else:
                    rx_util = 0
                    tx_util = 0

                insert_rate(
                    interface=interface,
                    rx_mbps=rx_mbps,
                    tx_mbps=tx_mbps,
                    rx_util=rx_util,
                    tx_util=tx_util,
                    status="UP" if oper_status == 1 else "DOWN",
                    speed=interface_speed
                )

            insert_counter(
                interface,
                current_rx,
                current_tx
            )

            saved += 1

        elapsed = time.time() - start

        print(
            f"Poll completed | "
            f"{saved} interfaces | "
            f"{elapsed:.2f}s"
        )

        sleep_time = POLL_INTERVAL - elapsed

        if sleep_time > 0:
            await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    asyncio.run(collect())
