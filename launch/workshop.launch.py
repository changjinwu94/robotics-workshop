"""Launch two nodes together. Qt draws the internal turtle canvas offscreen."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package="turtlesim", executable="turtlesim_node", name="turtlesim",
             additional_env={"QT_QPA_PLATFORM": "offscreen"}, output="screen"),
        Node(package="robot_lab", executable="udp_bridge", name="udp_bridge", output="screen"),
    ])
