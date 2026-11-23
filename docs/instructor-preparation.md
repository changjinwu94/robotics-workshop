# Instructor Preparation Guide

<!-- section: Before the session -->
## Commission one station per team

Reserve the full 280 minutes for student activities. Image the Pis, install dependencies and build the containers beforehand. Pair one laptop, one wired Logitech and one Pi 4. An instructor can run the class from the Windows maps, even when no Pi has a monitor.

| Station card | Fill in before class |
|---|---|
| Team / controller model / mode switch | __________________________________________ |
| Unique Pi hostname / verified Windows name | __________________________________________ |
| Pi username / current Wi-Fi IPv4 fallback | __________________________________________ |
| Git tag / actual short Pi and Windows revisions | __________________________________________ |
| Control axes and signs / centered drift | __________________________________________ |
| Windows profile / Pi station acceptance folder | __________________________________________ |

### Preparation checklist

- [ ] Flash Ubuntu Server 22.04 LTS 64-bit for Raspberry Pi. Give each Pi a unique hostname and verify SSH. Note its current DHCP Wi-Fi address.
- [ ] Test Windows name resolution, TCP 22 and **actual UDP in both directions** from the assigned laptop. Verify that the classroom Wi-Fi permits device-to-device traffic on the same SSID. An internet-only guest WLAN can block it.
- [ ] Clone the Git bundle on both machines. Check that the same baseline tag is available. Configure Git author identity before the first student commit.
- [ ] Preinstall VS Code, Remote – SSH, Windows Python and pygame. Open the Pi project remotely once so VS Code Server is already installed. Use the Windows VS Code rehearsal on page 3 to open the cloned folder in a second window and launch the GUI from its integrated PowerShell terminal.
- [ ] Build the ARM64 image and run the real station acceptance on the next page. Rehearse using the joystick, both fault exercises, recording and isolated replay.
- [ ] Put the three PDFs and offline bundle within reach. Assign operator and observer roles. Keep a spare data-capable USB cable/controller and a way to read the Pi's IP from its console or DHCP lease list.

**Release a station to the class** when the paired laptops and Pis have passed the local checks on pages 2–4. Record actual outputs, station identity and the date. The delivered test record is on page 7.

<!-- page -->
<!-- section: Pi rehearsal -->
## Verify headless motion and recording

The Dockerfile starts the real Humble turtlesim binary with both display variables removed and Qt's `offscreen` platform selected. A ROS subscriber observes two poses while publishing forward velocity. The build fails if the turtle fails to move by 0.15 world units within 35 seconds. The acceptance tool then checks the running stack through UDP and records a real ROS bag on the station.

**Pi host over SSH • repository root, all operator GUIs disconnected**

~~~bash
cd ~/robotics-workshop
uname -m
dpkg --print-architecture
docker compose --progress plain build
docker compose up -d
docker compose ps
docker compose exec robot lab-env python3 /opt/lab/tools/accept_station.py
~~~

**Expected evidence.** The Pi reports `aarch64` and `arm64`. A fresh image build prints `PASS  real headless turtlesim moved by at least 0.15 u`. A cached build may simply show the layer as cached. The running check reports measured travel, stationary pose samples after command loss, nonzero message counts for both topics and the recorder-time interval. Copy the printed `/runs/station-check-…` path onto the station card. The host sees it under `runs/`.

**Pi host over SSH • if commissioning fails**

~~~bash
docker compose logs --tail 50 robot
docker compose exec robot lab-env bash
~~~

**Pi container • narrow the failing interface**

~~~bash
printenv QT_QPA_PLATFORM
ros2 node list
ros2 topic list -t
ros2 topic echo /turtle1/pose --once
ros2 param get /udp_bridge telemetry_enabled
~~~

**If the check fails.** A missing pose points to simulator startup or ROS discovery. For a Qt error, confirm the image installed `ros-humble-turtlesim` and the platform prints `offscreen`. For a socket bind error, close the other stack on that Pi. If a bag will not write, check `runs/` ownership and `LAB_UID`/`LAB_GID`. For a recorder timeout inspect its saved `record.log`. Repeat commissioning after correcting the cause.

<!-- page -->
<!-- section: Windows VS Code rehearsal -->
## Rehearse the local Windows setup

Ask a partner to start from the Windows desktop. Give them the name of the cloned folder and watch them complete this sequence before demonstrating the Pi.

| Action to demonstrate | What the student should see |
|---|---|
| 1. Open **Start > Visual Studio Code**. If a remote window opens, choose **File > New Window**. | A local window for the laptop. The Pi window can stay open separately. |
| 2. Choose **File > Open Folder...**. Browse to the user profile's `robotics-workshop` folder and click **Select Folder**. | On the example account the full path is `C:\Users\student\robotics-workshop`. Use each student's own profile on other PCs. |
| 3. Open **Explorer** (Ctrl+Shift+E). | `requirements-windows.txt` and `operator_app` appear directly inside the top folder. A view showing only `source` and `workshop.bundle` means the extracted kit was opened. |
| 4. Choose **Terminal > New Terminal**. Select **PowerShell** from the dropdown beside **+** if needed. | The **TERMINAL** tab is open below the editor. The local prompt starts with `PS` and contains a Windows path. |
| 5. Check the folder and launch the application with the commands below. | The two path checks print `True`. The operator window shows **Local preview** and **OFFLINE**. |

**Local VS Code terminal • Windows PowerShell**

~~~powershell
Get-Location
Test-Path .\requirements-windows.txt
Test-Path .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -m operator_app
~~~

**If a check fails.** A missing requirements file points to the wrong folder. A missing interpreter in the correct folder calls for first-time Python setup on page 6 of the Installation and Setup Guide. A Pi, WSL or container prompt calls for switching to the local Windows window.

**Show what happens while the GUI runs.** Leave the GUI open. Show that its terminal is occupied, then choose **Terminal > New Terminal** for a second Windows prompt. Have the observer use the second terminal while the operator moves the physical stick. Close the GUI with **X**, then relaunch from its original terminal.

**Station evidence.** Ask the observer to read the local project path, the changing raw axis and the fresh or offline indicator aloud. For a connected run, carry on to the classroom Wi-Fi rehearsal on the next page.

<!-- page -->
<!-- section: Windows and Wi-Fi rehearsal -->
## Prove the round trip on the classroom SSID

Leave the GUI running. Use a second local VS Code terminal for these checks.

**Local VS Code terminal • second Windows PowerShell prompt**

~~~powershell
$Pi = "robot01.local"
[Net.Dns]::GetHostAddresses($Pi) | Where-Object AddressFamily -eq InterNetwork
Test-NetConnection $Pi -Port 22
Get-NetConnectionProfile
joy.cpl
~~~

Close the controller panel. In the open GUI enter the station hostname, center the stick and click **Connect**. Check that `ack` advances, forward and left move the turtle, and releasing the stick stops it. Record the controller model and mode. Allow at least 0.5 s between operator sessions.

| Symptom to reproduce | Passing observation | First diagnostic |
|---|---|---|
| Pause outgoing commands with a small stick input | Measured motion stops. FRESH and Pi TIMEOUT appear together. | Pi command becomes zero and the last accepted sequence stops increasing. |
| Turn telemetry off on the Pi | GUI becomes STALE while command and pose continue in ROS. | Restore `telemetry_enabled` and watch the next live pose arrive. |
| Unplug the joystick with packets enabled | The GUI reports no controller and sends zeros. | `ack` continues to advance. Reconnect and identify the axes again. |

### Windows receives no telemetry

Check the Pi command and pose topics and the telemetry parameter. If all three are working, check the Windows socket with the GUI connected.

**Local VS Code terminal • second Windows PowerShell prompt**

~~~powershell
Get-NetUDPEndpoint -LocalPort 5006
~~~

For an approved **Private** network, a lab administrator can allow UDP 5006 from the current Pi. Use the station's verified name in this separate administrator shell.

**Windows PowerShell (Administrator) • scoped firewall rule**

~~~powershell
$Pi = "robot01.local"
$addresses = [Net.Dns]::GetHostAddresses($Pi)
$ipv4 = $addresses | Where-Object AddressFamily -eq InterNetwork
$source = @($ipv4)[0].IPAddressToString
New-NetFirewallRule -DisplayName "Robotics lab telemetry" -Profile Private `
  -Direction Inbound -Action Allow -Protocol UDP -LocalPort 5006 `
  -RemoteAddress $source
~~~

**Expected result.** Reconnect, confirm the age drops below a second and record the current Pi address used to scope the rule. If name lookup is the original failure, use the DHCP address from the station card. Update the rule if that address changes. On a shared laptop, remove the temporary rule after the workshop using `Remove-NetFirewallRule -DisplayName "Robotics lab telemetry"` in elevated PowerShell.

<!-- page -->
<!-- section: Teaching plan -->
## Pace the room by observable results

| Time | Instructor moves | Check before moving on |
|---|---|---|
| 0:00–0:35 | Spend 8 min on a USV yaw example, 10 min drawing the loop, 12 min comparing robots and 5 min sharing. | A student can name a reference, actuator and independent observation. |
| 0:35–1:10 | Use 10 min to open the Windows folder and PowerShell, 12 min for SSH and the Pi window, and 13 min for paths and Git. | Each partner identifies the terminal machine and reads its Git revision. |
| 1:10–1:50 | Spend 10 min on host/image/container, 15 min inspecting typed topics and 15 min tracing zero command and pose. | Each pair has seen a Twist and a Pose in the live graph. |
| 1:50–2:00 | Break. Keep Compose detached and switch roles. | |
| 2:00–2:35 | Allow 8 min for USB and local GUI launch, 12 min to identify axes, 10 min for mapping and 5 min to save calibration. | Center reads zero. Forward and left have the intended signs. |
| 2:35–3:20 | Allow 12 min to connect/drive, 12 min per fault and 9 min to discuss. | Pairs explain why a fresh map can show a stopped robot and a stale map can hide motion. |
| 3:20–3:30 | Break. Verify telemetry is enabled. | |
| 3:30–4:05 | Use 5 min for reset and metadata, 8 min to record, 10 min to inspect and 12 min to replay. | Students read actual timestamps and explain the source of replayed pose. |
| 4:05–4:40 | Predict for 5 min, edit/commit for 10 min, repeat/compare for 12 min and reserve 8 min for exit tickets. | A second run identifies a new Windows revision and contains measured evidence. |

**If a station falls behind.** Have the pair inspect axes in local preview while you repair connectivity. For a failed station, pair its observer with a commissioned Pi. Keep one active operator per Pi. Continue timing and Git exercises against a bag recorded during rehearsal.

**Debrief prompt.** “If the GUI says forward but the map is frozen, name your next measurement.” Expect a sequence such as inspecting Pi command, then Pi pose, then the returning packet or freshness timer. Ask what each observation rules out.

<!-- page -->
<!-- section: Recording and recovery -->
## Keep a usable rehearsal run

Record one maneuver by following Student Guide pages 11–12. Capture it using the paired Windows GUI after the station acceptance has completed. It gives students a recoverable data set if a joystick fails during class.

| Artifact under `runs/arc01/` | What to check |
|---|---|
| `bag/metadata.yaml` and `*.db3` | Both topics have nonzero counts after the recorder closes cleanly. |
| `samples.csv` | A stationary interval precedes a positive command. A later pose reports motion and position changes across subsequent samples. |
| `pi-commit.txt` / `pi-status.txt` / `pi-tracked.patch` | Revision and worktree evidence identify the Pi source. Commit any untracked source needed for the experiment. |
| `compose.yaml` / `image-id.txt` / `packages.txt` | Resolved service settings, built image identity and installed ROS/Qt package versions. |
| `bridge-params.yaml` / `pi-platform.txt` | Telemetry enabled, real platform and Docker versions. |
| `operator.json` / `notes.txt` | Effective hostname/endpoint, Windows revision, mapping, Python/pygame versions, controller and maneuver. |

### If playback or timestamps look wrong

- Two pose sources during replay suggest a running simulator. Disconnect the GUI, stop the live Compose service and start the isolated playback shell from the student guide.
- If the player reports missing metadata, check that recording finished with Ctrl+C. Inspect the original bag directory and `ros2 bag info` before copying it.
- A zero or long recorder interval can reflect sampling or delivery order. Open nearby CSV rows. Describe command, measured velocity and position separately.
- A fresh `ack` proves the bridge accepted packets. Confirm actual motion from position/heading changes, especially near a wall.

### End-of-class assessment

Ask each student to show one signal at each interface. Have them classify a fault from the two observed flags, return to a known-good Git revision and name what they would need to repeat the experiment. Collect the observed time interval and the two revisions alongside the run name. Bags on the Pi survive `docker compose stop` and `docker compose down` through the host bind mount.

<!-- page -->
<!-- section: Validation record -->
## Distinguish software checks from station checks

| Delivered check | Environment and result |
|---|---|
| Wire format, range checks, deadband, command ownership/timeout, feedback freshness and CSV matching | Passed 13 automated checks on Debian 13 x86_64, CPython 3.12.14. Includes real IPv4 loopback datagrams. CSV input was synthetic. |
| GUI and both loss modes | Tk 9.0 on a virtual Linux desktop. Actual GUI, map and UDP transport passed with synthetic stick and pose, including recovery. |
| Qt offscreen mechanism | Qt 5.15.15 on Linux x86_64 created a widget and pixmap, painted and delivered five timer callbacks without a display. |
| Windows 11, local VS Code and USB Logitech | Awaiting station validation. Use page 3 to verify the local folder, integrated PowerShell launch and physical controller. Target CPython 3.11 x64 and pygame 2.6.1. Check axis signs and unplug/replug. |
| Pi 4 ARM64, Docker, real ROS 2 Humble | Awaiting station validation. The image build includes a real display-free motion check. The running-station script exercises actual UDP, ROS topics, recording and deserialization. |
| Classroom WLAN, DHCP/mDNS, firewall and rosbag replay | Awaiting paired-station validation. Record the real station evidence below. |

**Version records.** The image uses `ros:humble-ros-base-jammy` and installed Humble apt packages. Their resolved versions depend on build date. Keep the on-station `packages.txt` and image ID with the bag. For exact environment recovery, archive the built image as described in the setup guide.

| Instructor sign-off | Observed result / date / initials |
|---|---|
| Windows versions, local VS Code launch, USB model/mode and raw signs | __________________________________ |
| Pi 4 model/ARM64, Ubuntu version, Docker/Compose | __________________________________ |
| Hostname and actual two-way UDP on classroom Wi-Fi | __________________________________ |
| Headless motion check and station bag path | __________________________________ |
| Two fault modes, fresh recovery and isolated replay | __________________________________ |

**Background reading.** Course procedures are adapted to Humble. The installation guide lists upstream sources for ROS, Docker, Qt, pygame, SSH and Git. Use the program outputs and the named hardware when signing off a station.
