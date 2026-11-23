"""Commission a real station. Run in the live ROS container with all GUIs disconnected."""

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
TOPICS = ["/turtle1/cmd_vel", "/turtle1/pose"]


def finish(process):
    """Let rosbag2 close SQLite and write metadata before opening the recording."""
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        raise RuntimeError("rosbag2 did not finish within 15 seconds")


def main():
    out = Path(tempfile.mkdtemp(prefix="station-check-", dir="/runs"))
    bag = str(out / "bag")
    print(f"Saving station evidence under {out}", flush=True)
    for filename, args in [
        ("initial-pose.txt", ["topic", "echo", TOPICS[1], "--once"]),
        ("reset.txt", ["service", "call", "/reset", "std_srvs/srv/Empty", "{}"]),
    ]:
        with (out / filename).open("w") as stream:
            subprocess.run(["ros2", *args], stdout=stream, timeout=18, check=True)
    with (out / "record.log").open("w") as log:
        proc = subprocess.Popen(["ros2", "bag", "record", "-s", "sqlite3", "-o", bag, *TOPICS],
                                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            for topic in TOPICS:
                for _ in range(12):
                    if proc.poll() is not None:
                        raise RuntimeError(f"recorder exited; see {out}/record.log")
                    info = subprocess.check_output(["ros2", "topic", "info", topic, "--verbose"],
                                                   text=True, timeout=8)
                    if "Node name: rosbag2_recorder" in info:
                        break
                    time.sleep(0.5)
                else:
                    raise RuntimeError(f"recorder did not subscribe to {topic}")
            subprocess.run([sys.executable, str(TOOLS / "station_check.py")], check=True, timeout=20)
        finally:
            finish(proc)
    subprocess.run(["ros2", "bag", "info", bag], check=True)
    subprocess.run([sys.executable, str(TOOLS / "inspect_bag.py"), bag,
                    str(out / "samples.csv"), "--require-motion"], check=True)
    print("PASS  real ROS motion, command timeout, fresh pose, SQLite recording and timestamps")


if __name__ == "__main__":
    main()
