# Introductory Robotics Systems and Deployment Workshop

A 280-minute hands-on lab for graduate mechanical engineering students. A wired Logitech controller on Windows commands a headless ROS 2 Humble turtle on a Raspberry Pi 4. The Windows map uses the pose measured by the simulator.

## Start here

Open [Installation and Setup Guide](docs/installation-and-setup.md) to prepare a station. Teach from the [Student Workshop Guide](docs/student-workshop.md). Use the [Instructor Preparation Guide](docs/instructor-preparation.md) to commission each pair and record the checks. The [printable PDFs](docs/pdf/) are included alongside the editable Markdown sources and figures.

The ZIP includes an offline Git bundle with a real main branch and the tag `workshop-v1`. Clone the bundle on each machine using the setup guide. The expanded source tree in the ZIP is a reading copy. Run all commands from a cloned repository.

## Project tree

```text
robotics-workshop/
  operator_app/
    __main__.py         Windows command-line entry point
    gui.py              Tk numerics, map, controls and session sidecar
    joystick.py         USB game-controller input with pygame
    mapping.py          axis selection, signs, deadband and scaling
  robot_lab/
    bridge_node.py      ROS node, control timer and pose subscription
    control.py          command timeout and sender ownership
    link.py             Windows UDP socket and freshness timer
    protocol.py         common JSON messages and validation
    transport.py        Pi UDP socket and learned return endpoint
  settings/operator.json
  launch/workshop.launch.py
  package.xml           ROS dependencies and package metadata
  resource/robot_lab    ament package index marker
  setup.py / setup.cfg  Python entry point and ROS install layout
  Dockerfile / compose.yaml / docker/lab-env
  requirements-windows.txt
  tools/
    install_docker_ubuntu.sh   Docker installation on fresh Jammy
    verify_headless.py         real turtlesim image-build motion check
    station_check.py           movement and command-loss check
    accept_station.py          ROS recording and station acceptance
    new_run.sh                 run directory and Pi provenance
    inspect_bag.py             timestamp comparison and CSV export
  tests/                portable contract tests and Tk loopback exercise
  docs/                 three editable guides and diagram sources
  runs/                 host-mounted experiment folders, ignored by Git
```

## Everyday commands

**Pi host over SSH, repository root**

```bash
docker compose up -d --build
docker compose ps
docker compose exec robot lab-env bash
```

**Pi container, from that shell**

```bash
ros2 topic echo /turtle1/pose --once
```

**Windows PowerShell, local repository root**

```powershell
.\.venv\Scripts\python.exe -m operator_app
```

Type the station's verified hostname into the GUI and connect with the stick centered. UDP commands travel from Windows port 5006 to Pi port 5005. Feedback returns over the same sockets. The bridge publishes at 20 Hz and zeros commands after 0.50 s of silence. The GUI marks a pose stale after 1.0 s. Telemetry targets 10 Hz.

## Validation

**Windows PowerShell, repository root after Python setup**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m tests.gui_loopback
```

The second command opens an actual Tk window and exercises both UDP directions with synthetic inputs. **Pi host over SSH, with operator windows disconnected**, use the following command to commission the real stack. It resets and moves the simulated turtle and writes a uniquely named bag under `runs/`.

```bash
docker compose exec robot lab-env python3 /opt/lab/tools/accept_station.py
```

The instructor guide names the environment used for the delivered checks and includes a sign-off table for the Windows, Pi 4, joystick and classroom Wi-Fi checks. Experiment bags stay alongside the recorded Windows and Pi revisions and settings. The baseline tag rebuilds the source. Preserve the built image as described in the setup guide when the exact package set matters.
