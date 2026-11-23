"""Launch turtlesim and the UDP bridge using the configured Qt display."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package="turtlesim", executable="turtlesim_node", name="turtlesim",
             output="screen"),
        Node(package="robot_lab", executable="udp_bridge", name="udp_bridge", output="screen"),
    ])
