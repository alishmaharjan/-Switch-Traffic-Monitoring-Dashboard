import asyncio

from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    walk_cmd
)


SWITCH_IP = "192.168.200.2"
COMMUNITY = "admin123"


async def snmp_walk(oid):

    engine = SnmpEngine()

    target = await UdpTransportTarget.create(
        (SWITCH_IP, 161)
    )

    async for (
        errorIndication,
        errorStatus,
        errorIndex,
        varBinds
    ) in walk_cmd(
        engine,
        CommunityData(
            COMMUNITY,
            mpModel=1
        ),
        target,
        ContextData(),
        ObjectType(
            ObjectIdentity(oid)
        ),
        lexicographicMode=False
    ):

        if errorIndication:
            print(errorIndication)
            break

        elif errorStatus:
            print(errorStatus.prettyPrint())
            break

        else:
            for name, value in varBinds:
                print(
                    name.prettyPrint(),
                    "=",
                    value.prettyPrint()
                )


async def main():

    print("\nIncoming traffic counters\n")
    
    await snmp_walk(
        "1.3.6.1.2.1.31.1.1.1.6"
    )


    print("\nOutgoing traffic counters\n")

    await snmp_walk(
        "1.3.6.1.2.1.31.1.1.1.10"
    )


asyncio.run(main())
