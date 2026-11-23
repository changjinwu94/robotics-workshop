"""Exercise the real bridge and simulator with UDP. Center/reset the turtle first."""

import argparse
import math
import time

from robot_lab.link import OperatorLink


def sample(link, duration_s, velocity):
    """When velocity is None the command cable is logically unplugged; RX stays open."""
    poses, previous = [], None
    deadline = time.monotonic() + duration_s
    while time.monotonic() < deadline:
        if velocity is not None:
            link.send(*velocity)
        try:
            link.poll()
        except ConnectionRefusedError:
            pass  # May occur until the ROS node has bound its port.
        if link.pose and link.pose.seq != previous:
            poses.append(link.pose)
            previous = link.pose.seq
        time.sleep(0.05)
    return poses


def check(host):
    link = OperatorLink(host, local_port=0)
    try:
        initial = sample(link, 1.5, (0.0, 0.0))
        if not initial or initial[-1].timed_out:
            raise RuntimeError("no live pose; check launch, UDP port and other operators")
        driven = sample(link, 1.4, (1.0, 0.35))
        if not driven or not any(p.v > 0.4 and p.w > 0.1 for p in driven):
            raise RuntimeError("pose did not report the requested motion")
        travel = math.hypot(driven[-1].x-initial[-1].x, driven[-1].y-initial[-1].y)
        if travel < 0.25:
            raise RuntimeError("insufficient displacement; reset the turtle away from the wall")
        silence = sample(link, 1.35, None)
        stopped = [p for p in silence if p.timed_out and abs(p.v) < 0.01 and abs(p.w) < 0.01]
        if len(stopped) < 2:
            raise RuntimeError("command loss did not yield fresh stationary pose feedback")
        drift = math.hypot(stopped[-1].x-stopped[0].x, stopped[-1].y-stopped[0].y)
        if drift > 0.02:
            raise RuntimeError("position changed after the watchdog stop")
        print(f"PASS  displacement {travel:.3f} u; {len(stopped)} stopped feedback packets")
    finally:
        link.close()  # The command watchdog covers normal shutdown as well as loss.


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    check(parser.parse_args().host)
