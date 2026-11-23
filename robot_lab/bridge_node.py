"""Translate UDP commands into Twist and return fresh turtlesim Pose measurements."""

import socket
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from turtlesim.msg import Pose

from robot_lab.control import CommandGate
from robot_lab.protocol import Command, MAX_BYTES, PacketError, PosePacket, encode


class UdpBridge(Node):
    def __init__(self):
        super().__init__("udp_bridge")
        self.declare_parameter("telemetry_enabled", True)
        self.gate = CommandGate(timeout_s=0.5)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("0.0.0.0", 5005))
        self.socket.setblocking(False)
        self.publisher = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)
        self.subscription = self.create_subscription(Pose, "/turtle1/pose", self.on_pose, 10)
        self.pose = None
        self.pose_number = 0
        self.sent_pose_number = 0
        self.pose_at = 0.0
        self.tx_sequence = 0
        # A steady scheduler and local monotonic receipt times keep both watchdogs
        # independent of UTC adjustments, ROS playback time and the Windows clock.
        steady = Clock(clock_type=ClockType.STEADY_TIME)
        self.create_timer(0.05, self.control_tick, clock=steady)
        self.create_timer(0.10, self.telemetry_tick, clock=steady)
        self.get_logger().info("Listening for workshop UDP commands on port 5005")

    def on_pose(self, pose):
        self.pose, self.pose_at = pose, time.monotonic()
        self.pose_number += 1

    def control_tick(self):
        # Limit work per tick so a burst of datagrams cannot starve zero publication.
        for _ in range(64):
            try:
                data, peer = self.socket.recvfrom(MAX_BYTES + 1)
            except BlockingIOError:
                break
            try:
                cmd = Command.decode(data)
            except PacketError:
                continue
            self.gate.accept(cmd, peer, time.monotonic())
        msg = Twist()
        msg.linear.x, msg.angular.z = self.gate.velocity(time.monotonic())
        self.publisher.publish(msg)  # Includes startup, silence, and repeated zeros.

    def telemetry_tick(self):
        now = time.monotonic()
        if self.gate.peer is None or not self.get_parameter("telemetry_enabled").value:
            return
        if self.pose_number == self.sent_pose_number or now - self.pose_at > 0.4:
            return  # A cached pose cannot make a stopped simulator look healthy.
        p, cmd = self.pose, self.gate.command
        packet = PosePacket(cmd.session, self.tx_sequence, cmd.seq, p.x, p.y,
                            p.theta, p.linear_velocity, p.angular_velocity,
                            self.gate.expired(now))
        self.tx_sequence += 1
        try:
            self.socket.sendto(encode(packet), self.gate.peer)
        except OSError:
            return  # UDP can lose feedback. Retry with the next measurement.
        self.sent_pose_number = self.pose_number

    def destroy_node(self):
        self.socket.close()
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
