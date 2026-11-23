"""Image build check: run real Humble turtlesim with no display and verify motion."""

import math
import os
from pathlib import Path
import subprocess
import time

import rclpy
from ament_index_python.packages import get_package_prefix
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose


def main():
    env = os.environ.copy()
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    env["QT_QPA_PLATFORM"] = "offscreen"
    program = Path(get_package_prefix("turtlesim")) / "lib/turtlesim/turtlesim_node"
    rclpy.init(args=[])
    node = rclpy.create_node("headless_image_check")
    samples = []
    node.create_subscription(Pose, "/turtle1/pose", samples.append, 10)
    pub = node.create_publisher(Twist, "/turtle1/cmd_vel", 10)
    move = Twist()
    move.linear.x = 0.7
    with subprocess.Popen([str(program)], env=env) as turtle:
        try:
            until = time.monotonic() + 35
            while time.monotonic() < until:
                if turtle.poll() is not None:
                    raise RuntimeError(f"headless turtlesim exited with status {turtle.returncode}")
                rclpy.spin_once(node, timeout_sec=0.1)
                if samples:
                    pub.publish(move)
                    last, first = samples[-1], samples[0]
                    if math.hypot(last.x - first.x, last.y - first.y) >= 0.15:
                        print("PASS  real headless turtlesim moved by at least 0.15 u", flush=True)
                        return
            raise RuntimeError("no headless pose change within 35 seconds")
        finally:
            turtle.terminate()
            try:
                turtle.wait(timeout=4)
            except subprocess.TimeoutExpired:
                turtle.kill()
            node.destroy_node()
            rclpy.shutdown()


if __name__ == "__main__":
    main()
