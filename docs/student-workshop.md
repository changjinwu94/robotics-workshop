# Student Workshop Guide

<!-- section: Session map -->
## From joystick to motion

**How does an operator command become robot motion, and how can we verify what happened?** In this lab your partner will move a joystick, and you will decide which observation proves that the command reached each part of the system. Switch roles after the first break.

![Command and feedback paths across Windows and the headless Pi](figures/deployment.svg)

| Elapsed time | Activity | Evidence to collect |
|---|---|---|
| 0:00–0:35 | Compare four robots | A labeled feedback loop |
| 0:35–1:10 | Reach the headless Pi | Hostname, SSH and Git revision |
| 1:10–1:50 | Start Compose and ROS 2 | One command and one pose sample |
| 1:50–2:00 | Break | |
| 2:00–2:35 | Read the joystick | Axis indices, signs and center drift |
| 2:35–3:20 | Drive and interrupt both paths | Two different fault signatures |
| 3:20–3:30 | Break | |
| 3:30–4:05 | Record and replay | Bag, timestamps and run settings |
| 4:05–4:40 | Change and redeploy | A commit and a repeat run |

**Start with a prepared station.** You need the assigned Pi hostname, the Pi login, a wired Logitech controller and local and remote copies of the starter repository. The Installation and Setup Guide prepares all four. Keep one local VS Code window on Windows and one Remote – SSH window open to the Pi.

<!-- page -->
<!-- section: Block 1  /  35 minutes -->
## Draw the feedback loop

Imagine a USV turning toward a survey line. Its planner selects a desired heading. A heading controller compares that reference with an estimate from the sensors and adjusts differential thrust. Wind and current affect the hull. The next heading measurement lets the controller correct its error.

![Generic vehicle feedback loop with sensor return to controller and operator](figures/control-loop.svg)

| Function | Engineering question | One concrete quantity |
|---|---|---|
| Sensing | What can the hardware directly detect? | A gyro measures yaw rate in rad/s. |
| State estimation | What is the vehicle doing now? | An estimator combines gyro and heading observations to estimate yaw. |
| Planning | What reference should we follow next? | A segment of the survey line yields a desired heading. |
| Control | How much actuation will reduce error? | Left and right thrust differ to create a yaw moment. |

**Pair exercise • 10 minutes.** Draw the loop for one platform on the next page. Circle the physical plant. Mark one signal with its units and draw two return paths, one to the controller and one to the operator.

**Expected result.** Your diagram explains how a disturbance can change actual motion while the requested motion stays constant. If the diagram ends at the motor, add the sensor that would let you detect the error.

**Connect it to the turtle.** Today the human chooses the path and closes the outer loop by watching the map. The simulator integrates the velocity request and publishes its own pose. A physical vehicle would need measurements, an estimator and an actuator controller to perform those jobs.

<!-- page -->
<!-- section: Block 1  /  Platform comparison -->
## Follow the same command on four robots

| Platform and mission | Sensors and estimated state | Actuators and onboard computing | Communications and operator interface |
|---|---|---|---|
| UAV • inspect a structure | IMU, barometer and GNSS estimate attitude, height and position. | Flight controller stabilizes attitude. ESCs vary rotor speeds. A companion computer can plan a route. | Pilot radio carries stick inputs. A telemetry link returns position and health to the ground station. |
| USV • survey a waterway | GNSS, compass and IMU estimate position, heading and turn rate. | An onboard computer follows survey lines. Motor controllers set twin propeller thrusts. | Wi-Fi or radio links the boat to a shoreside map and manual controls. |
| AGV • deliver a cart | Wheel encoders, IMU and lidar estimate planar pose and reveal obstacles. | An onboard computer plans an aisle route. Wheel drives regulate speed. | Fleet Wi-Fi carries jobs and status. A dispatch console shows progress. |
| Legged robot • cross uneven ground | Joint encoders, IMU and contact sensing estimate body attitude and foot support. | An onboard computer selects footholds. Joint drives produce the torque to track the gait. | A handheld controller sets body speed. A console displays posture, contact and health. |

**Trace a left turn • 12 minutes.** Pick two platforms. For each, name the operator input, the onboard reference, the physical change that turns the vehicle, and a measurement that would confirm the turn. Explain one way the command could arrive while the turn still fails.

**Expected result.** For a USV you might describe unequal thrust, a yaw moment, then a changing compass heading. For an AGV, unequal wheel speeds can produce a turn. Wheel slip can make encoder estimates disagree with lidar motion.

**Write your own trace.** Use this space to sketch a second platform. Label the commanded quantity and the measurement, with units.

| Selected platform | Your notes |
|---|---|
| Physical cause of the turn | ______________________________ |
| Independent evidence of motion | ______________________________ |

**If the team gets stuck.** Start with the yaw moment on the free-body diagram. Work backward to an actuator that can produce it, then forward to an independent measurement.

<!-- page -->
<!-- section: Block 2  /  35 minutes -->
## Open the right machine

A hostname is a name for a machine. DHCP assigns its current IP address. A port selects a service at that address. SSH uses TCP port 22 and gives you a terminal on the Pi without attaching a screen. A path names a file or folder on whichever machine owns that terminal.

**Windows PowerShell • local VS Code**

Use the hostname on the station card. Filter for an IPv4 answer because the workshop UDP socket uses IPv4.

~~~powershell
$Pi = "robot-pi-01.local"
[Net.Dns]::GetHostAddresses($Pi) | Where-Object AddressFamily -eq InterNetwork
Test-NetConnection $Pi -Port 22
ssh "robot@$Pi"
~~~

**Pi host over SSH • start at home**

~~~bash
pwd
hostname
ls
cd ~/robotics-workshop
git status --short --branch
git log -3 --oneline
git rev-parse --short HEAD
~~~

**Read the shell.** A terminal runs commands one line at a time. In Bash, `~` means your home folder. `pwd` prints your location, `ls` lists its contents and `cd` changes folders.

**What to observe.** The first shell shows the Pi's home folder. The hostname matches your station, and Git shows the starter history. Write down the short revision. Use `exit` to leave the SSH shell when you want PowerShell back.

**Open the editor.** In VS Code on Windows, press Ctrl+Shift+P, choose **Remote-SSH: Connect to Host**, select `labpi` from the setup guide, then **Open Folder** and select `/home/robot/robotics-workshop`. In its new terminal run `hostname`. Open a second, local VS Code window at `$HOME\robotics-workshop` for the GUI.

**If the name fails.** Ask for the current Wi-Fi address on the station card. From a Pi console run `ip -4 -br addr` and read the connected Wi-Fi interface. Put that address in `$Pi` temporarily and repeat the Windows tests. If the address works, check the station spelling and mDNS. If TCP 22 also fails by address, check SSH service and wireless client isolation with the instructor.

<!-- page -->
<!-- section: Block 3  /  40 minutes -->
## Start the container and inspect ROS

A Docker image contains the installed software. Compose starts a running instance called `robot`. The Pi host provides the network and disk. Inside this container, `/udp_bridge` publishes a velocity command and subscribes to simulator pose. A ROS node is a running participant. A topic is a named stream whose publishers and subscribers agree on a message type.

**Pi host over SSH • repository root**

~~~bash
cd ~/robotics-workshop
docker compose up -d
docker compose ps
docker compose logs --tail 15 robot
docker compose exec robot lab-env bash
~~~

**Pi container • shell just opened**

~~~bash
ros2 node list
ros2 topic list -t
ros2 topic info /turtle1/cmd_vel --verbose
ros2 interface show geometry_msgs/msg/Twist
ros2 topic echo /turtle1/cmd_vel --once
ros2 topic echo /turtle1/pose --once
~~~

| Topic | Publisher → subscriber | Fields to inspect |
|---|---|---|
| `/turtle1/cmd_vel` | UDP bridge → turtlesim | `linear.x` in world units/s and `angular.z` in rad/s |
| `/turtle1/pose` | turtlesim → UDP bridge | `x`, `y`, `theta`, `linear_velocity` and `angular_velocity` |

**Expected result.** With the sticks idle or the GUI disconnected, both commanded components are zero. A freshly started turtle is around (5.54, 5.54) with heading 0. A changed pose can be left over from a previous run. Qt draws the simulator offscreen. The Windows map will display its measured position.

**If a topic is missing.** Check the two node names and the container logs. If `ros2` or the package is missing, leave with `exit` and re-enter through `lab-env` so the shell loads ROS and the workshop package. Stop continuous topic output with Ctrl+C. The detached Compose service keeps running.

**Break • 10 minutes.** Leave the Pi stack running and switch to the local Windows window.

<!-- page -->
<!-- section: Block 4  /  35 minutes -->
## Calibrate the joystick in local preview

Plug the wired Logitech into Windows. For controllers with an X/D mode switch, select one mode and keep it fixed throughout the experiment. Open the Windows controller panel, pick the device, and move one axis at a time in **Properties**.

**Windows PowerShell • local repository**

~~~powershell
joy.cpl
cd "$HOME\robotics-workshop"
.\.venv\Scripts\python.exe -m operator_app
~~~

Page 12 identifies each GUI measurement. Leave the GUI in **Local preview**. Read the raw axis labels. Record the two channels that move when you push forward and when you push left. Note the sign and the largest value observed while centered. A normalized axis is roughly -1 to +1.

| Action | Observe | Desired result after mapping |
|---|---|---|
| Release both axes | Raw center drift | Both requested values read zero. |
| Push forward only | Index and sign of changing axis | Positive `v`, near-zero `w` |
| Push left only | Index and sign of changing axis | Positive `w`, near-zero `v` |
| Push halfway, then fully | Requested speed | Magnitude increases toward the configured maximum. |

**How the map works.** A deadband of 0.12 suppresses center drift. Outside it the code scales the remaining travel back to 0–1. With a raw forward value of -0.56, sign -1 and maximum 2.0 u/s, the request is (0.56 - 0.12) / (1 - 0.12) × 2.0 = 1.0 u/s. Here `u` means one turtlesim world unit.

**If the wrong quantity moves.** In the local VS Code window edit `settings/operator.json`. Set `forward_axis` and `turn_axis` from your observations. Set each sign to +1 or -1 (JSON uses `1` for positive one). Save, close the GUI and relaunch it. If there are no raw axes, check `joy.cpl` and reconnect the USB plug. With the controller absent the GUI requests zero.

**Keep a known baseline.** If you changed the mapping to fit your hardware, commit the calibrated settings before recording. Configure your Git author as described in the setup guide.

**Windows PowerShell • local repository**

~~~powershell
git diff -- settings/operator.json
git add settings/operator.json
git commit -m "Calibrate joystick axes for this station"
~~~

<!-- page -->
<!-- section: Block 5  /  45 minutes -->
## Drive and diagnose both directions

In the local GUI, enter the verified Pi hostname and select **Connect** with the stick centered. The **FRESH** badge and an advancing `ack` show that return packets are arriving. Push forward briefly, release, then turn left in place. Heading 0 points along +x. A positive turn rotates counterclockwise.

**Pi container • open a second shell if needed**

~~~bash
ros2 topic echo /turtle1/cmd_vel
~~~

Watch `linear.x` and `angular.z` respond. Press Ctrl+C and repeat with `ros2 topic echo /turtle1/pose` to see the measured position and heading. On the GUI, the requested values come from the joystick. The map and measured velocities come from the Pi.

| Fault exercise | Pi evidence | Windows evidence |
|---|---|---|
| A. Hold a small forward input and select **Pause command packets**. | The bridge publishes zeros after 0.50 s without an accepted command, at the next 20 Hz tick. Measured pose settles. | The request remains visible as **PAUSED**. Pose stays **FRESH**, `ack` stops advancing and Pi reports **TIMEOUT**. |
| B. Resume command packets. Interrupt only the return path with the command below. Use a gentle turn. | Command and pose topics continue changing. | After 1.0 s the badge reads **STALE** and the last map marker stays fixed. Actual motion can continue. |

**Pi container • fault B, pause the return path**

~~~bash
ros2 param set /udp_bridge telemetry_enabled false
~~~

Observe the stale display and center the stick.

**Pi container • restore the return path**

~~~bash
ros2 param set /udp_bridge telemetry_enabled true
~~~

**Expected result.** The next accepted pose makes the map fresh again. Write down which signal stopped first for each fault. If the first connection never becomes fresh, compare the Pi command topic while moving the stick. A changing command narrows the investigation to pose publication or the return path. The instructor guide includes the Windows firewall check.

<!-- page -->
<!-- section: Block 5  /  Interface reference -->
## Read a packet like a drawing

UDP sends a datagram to a destination address and port. It does not guarantee delivery or order. Each JSON object fits into one UTF-8 datagram. The Pi accepts a new command only if it passes type, range, session and sequence checks. One active laptop controls each Pi.

| Direction | Socket path | Nominal pace |
|---|---|---|
| Command | Windows IPv4 UDP 5006 → resolved Pi IPv4 UDP 5005 | GUI targets 20 Hz |
| Feedback | Pi UDP 5005 → observed Windows source address and port | Bridge targets 10 Hz when fresh poses are available |

| JSON field | Command packet | Pose packet |
|---|---|---|
| `ver`, `type` | Integer `1`, string `"cmd"` | Integer `1`, string `"pose"` |
| `session` | New 32-character lowercase hex ID on each connection | Echoes the active command session |
| `seq` | Increasing command sequence, starting at zero | Independent increasing telemetry sequence |
| `v`, `w` | Requested forward u/s and yaw rad/s, limited to magnitudes 3 and 4 | Simulator-reported forward u/s and yaw rad/s |
| `ack` | — | Sequence number of the last accepted command |
| `x`, `y`, `theta` | — | World coordinates in u and heading in radians |
| `timed_out` | — | Boolean reporting the Pi command watchdog state |

**Example decoded command • JSON file format**

~~~json
{"ver":1,"type":"cmd","session":"0123456789abcdef0123456789abcdef",
 "seq":24,"v":1.0,"w":0.0}
~~~

**Trace one reply.** The Pi takes the source endpoint from the received datagram. Windows uses that same bound socket to receive the reply. Each machine measures elapsed time with its own monotonic clock. A frozen or invalid pose cannot refresh the GUI. If a second GUI opens on the same laptop, the fixed local port may already be in use.

**Break • 10 minutes.** Center the stick, resume command packets and restore telemetry. Leave the GUI connected for the recording.

<!-- page -->
<!-- section: Block 6  /  35 minutes -->
## Record one repeatable maneuver

Use `arc01` for a fresh run. If it already exists, choose an unused name and change it in every command, including the Windows copy. Center the stick, restore telemetry and keep the GUI connected. The pose and velocity topics both need samples while the turtle is idle.

**Pi host over SSH • repository root**

~~~bash
bash tools/new_run.sh arc01
docker compose exec robot lab-env bash
~~~

**Pi container • reset the starting state and begin recording**

~~~bash
ros2 service call /reset std_srvs/srv/Empty '{}'
ros2 topic echo /turtle1/pose --once
ros2 bag record -s sqlite3 -o /runs/arc01/bag \
  /turtle1/cmd_vel /turtle1/pose
~~~

Wait for both subscription messages. Hold neutral for two seconds, drive forward for one second, add a gentle left turn for one second, then release and wait two seconds. Keep away from the wall. Stop the recorder with Ctrl+C and wait for the shell prompt so SQLite and metadata are finalized.

**Windows PowerShell • new local terminal in the repository**

~~~powershell
scp .\local\operator-session.json labpi:robotics-workshop/runs/arc01/operator.json
~~~

**Pi host over SSH • remote VS Code window**

Open `runs/arc01/notes.txt` and enter the starting pose, controller mode, maneuver and observation. The GUI writes the effective mapping and Windows Git revision on connection. Copy its sidecar before connecting to another station or run.

**Pi container • inspect the captured evidence**

~~~bash
ros2 bag info /runs/arc01/bag
python3 /opt/lab/tools/inspect_bag.py /runs/arc01/bag \
  /runs/arc01/samples.csv
~~~

**Expected result.** Both topics have nonzero counts. The script prints a motion command, a compatible measured velocity and their recorder-time interval. Open `runs/arc01/samples.csv` in remote VS Code. Find one later pose with changed `x`, `y` or `theta`. If no onset matched, record again with a longer neutral lead-in and a clear forward input.

<!-- page -->
<!-- section: Block 6  /  Replay and interpretation -->
## Compare timestamps, then replay

The CSV preserves the integer recorder timestamp in nanoseconds and elapsed seconds from the first captured sample. `Twist` and `turtlesim/Pose` have no header timestamp. Their recorded interval includes sampling, scheduling and delivery to the recorder. It can differ from physical response time.

| Illustrative row | Time after bag start | What the row means |
|---|---|---|
| Command | 2.000 s | Forward request changes from zero to 1.0 u/s. |
| Pose | 2.018 s | First observed positive measured velocity after the request. |
| Later pose | 2.115 s | Compare position with the idle sample to confirm translation. |

For this illustration the observed interval is 18 ms. Enter your own pair of timestamps and interval in `notes.txt`. A pose may arrive before the recorder writes the associated command, so the automated match is a first compatible observation. Inspect nearby rows if timing looks unusual.

**Prepare for playback.** Center the stick and disconnect the GUI. Leave the live container shell with `exit`. Stop the service so neither the bridge nor turtlesim can publish during observation.

**Pi host over SSH • repository root**

~~~bash
docker compose stop robot
docker compose run --rm --no-deps robot bash
~~~

**Pi container • isolated replay shell**

Start an observer before the player. Its explicit message type lets it subscribe before the topic appears. The file holds one recorded pose. Let playback reach the end.

~~~bash
timeout 45 ros2 topic echo /turtle1/pose turtlesim/msg/Pose \
  --once > /tmp/replayed-pose.txt &
observer=$!
ros2 bag play /runs/arc01/bag --delay 2
wait "$observer"
cat /tmp/replayed-pose.txt
exit
~~~

**Pi host over SSH • return to the live lab**

~~~bash
docker compose up -d
~~~

**Expected result.** The player publishes the two saved streams in recorded order and timing as closely as scheduling permits. The recorded pose stream supplies the observations during playback. To repeat the experiment, restore both source revisions, mapping and image, reset the simulated pose, reconnect and perform the maneuver into a new bag. Timing and human inputs can vary.

<!-- page -->
<!-- section: Block 7  /  35 minutes -->
## Change one value and test the prediction

Predict the full-forward command if you reduce `max_v` from 2.0 to 1.0 u/s and leave the turn scale unchanged. Capture the calibrated revision first. Close the GUI so its next launch will reload the edited settings.

**Windows PowerShell • local repository**

~~~powershell
git status --short --branch
git switch -c lab/lower-speed
code settings/operator.json
~~~

In the local file, set `max_v` to `1.0`. Save it. Inspect the diff and commit this one change. If your baseline already used 1.0, pick another positive value below 3.0 and record it.

**Windows PowerShell • same repository**

~~~powershell
git diff -- settings/operator.json
git add settings/operator.json
git commit -m "Reduce full-forward speed for the comparison run"
git show --stat --oneline HEAD
.\.venv\Scripts\python.exe -m operator_app
~~~

Reconnect by hostname. Repeat the recording exercise as `arc02`, using the same reset, controller and maneuver. Copy the newly written operator sidecar. Compare the two peak commanded velocities and the subsequent changes in position. If only a Windows mapping changed, restarting the GUI deploys it. For a change to the bridge source, rebuild on the Pi.

**Pi host over SSH • only after a Pi source change**

~~~bash
docker compose up -d --build
docker compose exec robot lab-env ros2 topic echo /turtle1/pose --once
~~~

**Recover the earlier behavior.** On your exercise branch, `git revert --no-edit HEAD` creates a new commit that undoes your mapping change. Restart the GUI and check the original maximum. To inspect the distributed baseline separately, use `git show workshop-v1:settings/operator.json`. For publishing your branch to the course GitHub repository, use the setup guide.

**Exit ticket.** Show your partner the two topic samples, both fault signatures, the bag interval and the one-line mapping diff. Point to the Windows and Pi commits in a run folder. Explain what additional evidence you would want before claiming that a physical wheel or propeller followed its command.

<!-- page -->
<!-- section: Field reference  /  Windows operator -->
## Locate each measurement on the GUI

The screenshot shows the workshop GUI during a loopback check with synthetic input and pose. On a classroom laptop, enter your Pi hostname in the first field. The controller name and axis readings come from the attached Logitech.

![Workshop operator window with requested velocities, freshness badge, measured pose and heading arrow](figures/operator-window.png)

| Display | How to read it |
|---|---|
| Raw axes and requested velocities | A0 and A1 are dimensionless stick readings. SENDING means the GUI is trying to transmit the mapped values. PAUSED keeps the requested values visible. |
| FRESH / STALE and age | Windows measures time since its last accepted pose. The badge and color describe the return path. |
| Measured v, w, Pi LIVE / TIMEOUT and ack | The simulator reports velocity. The bridge reports its command watchdog and last accepted command number. |
| Map marker and arrow | Position comes from x and y. Heading is the arrow direction. Gray marks the last received pose during a stale interval. |

**Read this frame.** The requested turn is positive and the arrow points up and right. The receipt of command 24 and a recent pose show evidence in both directions. To prove translation, compare the current position with a second sample.
