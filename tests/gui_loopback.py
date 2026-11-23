"""Exercise the actual Tk operator and UDP transport with a synthetic stick and pose.

From the repo root: python -m tests.gui_loopback
Needs Tk and a desktop display. Uses no ROS, pygame, Pi, or physical USB controller.
Close other workshop GUIs first. Uses the normal local IPv4 UDP ports 5005 and 5006.
"""

import math
import tempfile
import time
import tkinter as tk
from pathlib import Path
from unittest.mock import patch

from operator_app.gui import OperatorWindow
from operator_app.mapping import Mapping
from robot_lab.transport import BridgeTransport


class TestStick:
    name = "Synthetic two-axis input"
    version = "test fixture"

    def read(self):
        return [-0.5, -0.7]

    def close(self):
        pass


def check():
    root = tk.Tk()
    bridge = BridgeTransport(("127.0.0.1", 5005))
    last = time.monotonic()
    x, y, theta = 5.5, 5.5, 0.0
    history = []
    with tempfile.TemporaryDirectory() as d, patch("operator_app.gui.ROOT", Path(d)):
        ui = OperatorWindow(root, TestStick(), Mapping(1, 0, -1, -1, 0.12, 2.0, 2.0), "localhost")
        ui.toggle()

        def run(seconds, feedback):
            nonlocal x, y, theta, last
            until = time.monotonic() + seconds
            while time.monotonic() < until:
                root.update()
                now = time.monotonic()
                v, w = bridge.control()
                dt = now - last
                x += v * math.cos(theta) * dt
                y += v * math.sin(theta) * dt
                theta += w * dt
                last = now
                if feedback:
                    bridge.send_pose(x, y, theta, v, w)
                history.append((v, w))
                time.sleep(0.02)

        try:
            run(0.35, True)
            assert ui.fresh.get().startswith("FRESH") and x > 5.6
            assert Path(d, "local", "operator-session.json").is_file()
            ui.pause_tx.set(True)
            run(0.80, True)
            assert history[-1] == (0.0, 0.0)
            assert "Pi TIMEOUT" in ui.pose_text.get() and ui.fresh.get().startswith("FRESH")
            ui.pause_tx.set(False)
            run(1.30, False)
            assert history[-1][0] > 0 and ui.fresh.get().startswith("STALE")
            run(0.25, True)
            assert ui.fresh.get().startswith("FRESH") and "Pi LIVE" in ui.pose_text.get()
            print("PASS  Tk, real UDP both ways, motion, command timeout, stale return, recovery")
        finally:
            ui.close()
            bridge.close()


if __name__ == "__main__":
    check()
