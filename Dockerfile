FROM ros:humble-ros-base-jammy

# The official image provides the ROS apt repository for Jammy on ARM64 and AMD64.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions ros-humble-turtlesim ros-humble-ros2launch \
    ros-humble-rosbag2 ros-humble-rosbag2-storage-default-plugins \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work/src/robot_lab
COPY package.xml setup.py setup.cfg ./
COPY resource ./resource
COPY launch ./launch
COPY robot_lab ./robot_lab
WORKDIR /work
RUN . /opt/ros/humble/setup.sh && colcon build --packages-select robot_lab

COPY tools /opt/lab/tools
COPY docker/lab-env /usr/local/bin/lab-env
RUN chmod 755 /usr/local/bin/lab-env
ENV QT_QPA_PLATFORM=offscreen ROS_LOCALHOST_ONLY=1
RUN /usr/local/bin/lab-env python3 /opt/lab/tools/verify_headless.py
ENTRYPOINT ["/usr/local/bin/lab-env"]
CMD ["ros2", "launch", "robot_lab", "workshop.launch.py"]
