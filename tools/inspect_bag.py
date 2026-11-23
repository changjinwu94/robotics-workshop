"""Export recorder timestamps and match a command onset to a measured velocity.

Use in the ROS container. Both topics lack a Header. All comparisons therefore use
bag recorder timestamps from the same clock, not joystick or actuator timestamps.
"""

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

CMD = "/turtle1/cmd_vel"
POSE = "/turtle1/pose"


@dataclass
class Sample:
    ns: int
    topic: str
    v: float
    w: float
    x: object = ""
    y: object = ""
    theta: object = ""


def read_bag(path):
    import rosbag2_py
    from geometry_msgs.msg import Twist
    from rclpy.serialization import deserialize_message
    from turtlesim.msg import Pose
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(path), storage_id="sqlite3"),
                rosbag2_py.ConverterOptions("", ""))
    while reader.has_next():
        name, data, ns = reader.read_next()
        if name == CMD:
            msg = deserialize_message(data, Twist)
            yield Sample(ns, name, msg.linear.x, msg.angular.z)
        elif name == POSE:
            msg = deserialize_message(data, Pose)
            yield Sample(ns, name, msg.linear_velocity, msg.angular_velocity,
                         msg.x, msg.y, msg.theta)


class OnsetComparison:
    """Match the first idle-to-motion edge with the first compatible pose sample."""

    def __init__(self):
        self.saw_idle = False
        self.command = None
        self.response = None
        self.pose_before = None

    def observe(self, row):
        if self.command is None:
            if row.topic == POSE:
                self.pose_before = row
            elif abs(row.v) <= 0.05 and abs(row.w) <= 0.05:
                self.saw_idle = True
            elif self.saw_idle:
                self.command = row
        elif self.response is None and row.topic == POSE and row.ns >= self.command.ns:
            c = self.command
            # Classify the principal component of the first command. The teaching
            # maneuver starts forward; the turn-only case also works.
            requested, measured = (c.v, row.v) if abs(c.v) >= abs(c.w) else (c.w, row.w)
            if abs(measured) > 0.05 and requested * measured > 0:
                self.response = row


def export(rows, csv_path):
    comp = OnsetComparison()
    origin = None
    counts = {CMD: 0, POSE: 0}
    with Path(csv_path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["bag_time_ns", "elapsed_s", "topic", "v_u_s", "w_rad_s",
                         "x_u", "y_u", "theta_rad"])
        for row in rows:
            if origin is None:
                origin = row.ns
            writer.writerow([row.ns, f"{(row.ns-origin)/1e9:.6f}", row.topic,
                             row.v, row.w, row.x, row.y, row.theta])
            counts[row.topic] += 1
            comp.observe(row)
    print(f"Rows: {counts[CMD]} commands, {counts[POSE]} poses")
    if comp.command and comp.response:
        a, b = comp.command, comp.response
        print(f"Command {a.ns} ns  v={a.v:.3f} w={a.w:.3f}")
        print(f"Pose    {b.ns} ns  v={b.v:.3f} w={b.w:.3f} x={b.x:.3f} y={b.y:.3f}")
        print(f"Recorder interval {(b.ns-a.ns)/1e6:.1f} ms")
        return True
    print("No matched onset. Record an idle interval, drive forward, then release.")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bag")
    parser.add_argument("csv")
    parser.add_argument("--require-motion", action="store_true")
    args = parser.parse_args()
    matched = export(read_bag(args.bag), args.csv)
    if args.require_motion and not matched:
        raise SystemExit(1)
