import os
import subprocess

RRD_DIR = "rrd"
GRAPH_DIR = "static/graphs"

os.makedirs(GRAPH_DIR, exist_ok=True)


def sanitize(name):
    return name.replace("/", "_").replace(" ", "_")


def generate_graph(interface):

    name = sanitize(interface)

    rrd = os.path.join(RRD_DIR, f"{name}.rrd")
    png = os.path.join(GRAPH_DIR, f"{name}.png")

    if not os.path.exists(rrd):
        print(f"RRD not found: {rrd}")
        return None

    cmd = [
        "rrdtool",
        "graph",
        png,

        "--start", "-24h",
        "--end", "now",

        "--title", interface,
        "--vertical-label", "Mbps",

        "--width", "700",
        "--height", "220",

        f"DEF:rx={rrd}:rx:AVERAGE",
        f"DEF:tx={rrd}:tx:AVERAGE",

        "LINE2:rx#00AA00:RX",
        "LINE2:tx#0000FF:TX",

        "GPRINT:rx:MAX:Max\\:%6.2lf Mbps",
        "GPRINT:rx:AVERAGE:Avg\\:%6.2lf Mbps",
        "GPRINT:rx:LAST:Last\\:%6.2lf Mbps\\n",

        "GPRINT:tx:MAX:Max\\:%6.2lf Mbps",
        "GPRINT:tx:AVERAGE:Avg\\:%6.2lf Mbps",
        "GPRINT:tx:LAST:Last\\:%6.2lf Mbps\\n"
    ]

    subprocess.run(cmd, check=True)

    return png


if __name__ == "__main__":
    generate_graph("GE0/0/22")
