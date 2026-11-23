from setuptools import setup

setup(
    name="robot_lab",
    version="1.0.0",
    packages=["robot_lab"],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/robot_lab"]),
        ("share/robot_lab", ["package.xml"]),
        ("share/robot_lab/launch", ["launch/workshop.launch.py"]),
    ],
    install_requires=["setuptools"],
    entry_points={"console_scripts": ["udp_bridge = robot_lab.bridge_node:main"]},
)
