"""Translate UDP commands into Twist and return fresh turtlesim Pose measurements."""

import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from turtlesim.msg import Pose

from robot_lab.transport import BridgeTransport


class UdpBridge(Node):
    def __init__(self):
        super().__init__("udp_bridge")
        self.declare_parameter("telemetry_enabled", True)
        self.link = BridgeTransport()
        self.publisher = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)
        self.subscription = self.create_subscription(Pose, "/turtle1/pose", self.on_pose, 10)
        self.pose = None
        self.pose_number = 0
        self.sent_pose_number = 0
        self.pose_at = 0.0
        # Keep command loss independent of UTC adjustments, ROS playback time and
        # the Windows clock. velocity is republished every 50 ms even during silence.
        steady = Clock(clock_type=ClockType.STEADY_TIME)
        self.create_timer(0.05, self.control_tick, clock=steady)
        self.create_timer(0.10, self.telemetry_tick, clock=steady)
        self.get_logger().info("Listening for workshop UDP commands on port 5005")

    def on_pose(self, pose):
        self.pose, self.pose_at = pose, time.monotonic()
        self.pose_number += 1

    def control_tick(self):
        msg = Twist()
        msg.linear.x, msg.angular.z = self.link.control()
        self.publisher.publish(msg)  # Includes startup, command loss and repeated zeros.

    def telemetry_tick(self):
        if not self.get_parameter("telemetry_enabled").value:
            return
        if self.pose_number == self.sent_pose_number or time.monotonic() - self.pose_at > 0.4:
            return  # A cached pose cannot make a stopped simulator look healthy.
        p = self.pose
        if self.link.send_pose(p.x, p.y, p.theta, p.linear_velocity, p.angular_velocity):
            self.sent_pose_number = self.pose_number

    def destroy_node(self):
        self.link.close()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UdpBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
