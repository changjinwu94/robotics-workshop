# Installation and Setup Guide

<!-- section: Station requirements -->
## Prepare the Pi and the Windows laptop

Use this guide before the 4-hour-40-minute class, or to rebuild a station later. The student session starts with both computers on the same classroom Wi-Fi. Give each team one hostname and one controller.

| Location | Install or connect | Work performed there |
|---|---|---|
| Windows 11 laptop | VS Code, Remote – SSH, Git for Windows, OpenSSH Client, 64-bit CPython 3.11 with Tcl/Tk, pygame 2.6.1, wired Logitech USB controller | Read axes, edit GUI locally, send commands, display measured pose |
| Pi 4 host | 64-bit Ubuntu Server 22.04 LTS for Raspberry Pi, SSH, Avahi, Git, Docker Engine and Compose plugin | Headless login, remote editing, launch Compose, store bags |
| Pi container | Official Humble ROS base, turtlesim, rclpy, rosbag2, workshop ROS package | Run simulator, bridge, introspection and bag tools |

**Prepare the Windows tools.** Install VS Code, Git for Windows and 64-bit Python 3.11 from python.org with Tcl/Tk and the `py` launcher. In VS Code press **Ctrl+Shift+X**, search for Microsoft's **Remote - SSH** extension and select **Install**. [VS Code Remote – SSH](https://code.visualstudio.com/docs/remote/ssh)

### Image a fresh SD card

Use a Pi 4 power supply and a microSD card with space for the ROS image and recordings. A 32 GB card is a practical workshop choice. In Raspberry Pi Imager select Raspberry Pi 4, then the **64-bit Ubuntu Server 22.04 LTS preinstalled Raspberry Pi image**. If needed choose **Use custom** and select `ubuntu-22.04.5-preinstalled-server-arm64+raspi.img.xz` from the Ubuntu release directory. Selecting the target SD card and writing an image erases its existing contents. [Ubuntu Raspberry Pi images](https://cdimage.ubuntu.com/releases/22.04/release/)

Use Imager's OS customization if offered for this image. Set a unique hostname such as `robot-pi-01`, set the station username (examples use `robot`), enable SSH and configure the classroom SSID/country for this initial preparation. If the image does not apply these settings, complete first boot at a temporary console with the lab account and enroll the Pi on the WLAN before using SSH. Wait for cloud-init to finish.

**Pi host • first-boot console or existing SSH terminal**

~~~bash
cloud-init status --wait
uname -m
dpkg --print-architecture
cat /etc/os-release
ip -4 -br addr
~~~

**Expected result.** The Pi reports `aarch64`, `arm64` and Ubuntu 22.04. Read the IPv4 address of the connected Wi-Fi interface and record it as the DHCP fallback. A Docker bridge address belongs to a different interface.

<!-- page -->
<!-- section: Headless access -->
## Verify the hostname before deployment

Use a different number for each Pi. Set the hostname once if the Imager settings have not already done so. If `/etc/hosts` contains a `127.0.1.1` entry for the old Pi name, edit that entry to match. Keep the ordinary localhost entry intact.

**Pi host • first-boot console or existing SSH terminal**

~~~bash
sudo hostnamectl set-hostname robot-pi-01
sudo apt update
sudo apt install -y openssh-server avahi-daemon git curl ca-certificates
sudo systemctl enable --now ssh avahi-daemon
hostname
systemctl is-active ssh avahi-daemon
ip -4 -br addr
~~~

On Windows, open Visual Studio Code from Start. Choose **Terminal > New Terminal**. In the bottom **TERMINAL** panel select a local **PowerShell** profile from the dropdown beside **+**. Run the Windows lines there. If `ssh -V` fails, install **OpenSSH Client** in Windows Optional Features and reopen VS Code. [Microsoft OpenSSH](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse)

**Local VS Code terminal • Windows PowerShell on the assigned station**

~~~powershell
$Pi = "robot-pi-01.local"
[Net.Dns]::GetHostAddresses($Pi) | Where-Object AddressFamily -eq InterNetwork
Test-NetConnection $Pi -Port 22
ssh "robot@$Pi"
~~~

Confirm the first connection's host key fingerprint against the Pi console (run `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` when the displayed key type is ED25519). Log in with your assigned account. Type `hostname` in the resulting shell and `exit` to return to Windows.

**Save the verified target.** In local VS Code open the command palette, select **Remote-SSH: Open SSH Configuration File**, and choose the file in your Windows user profile, normally `%USERPROFILE%\.ssh\config`. Add the following entry. Match `HostName` and `User` to the station.

**Windows file • OpenSSH configuration**

~~~text
Host labpi
    HostName robot-pi-01.local
    User robot
~~~

Use `ssh labpi` and the VS Code host named `labpi`. The GUI uses the actual hostname from `HostName`. If your classroom DNS verifies a bare name instead of `.local`, use that form in SSH and the GUI. If only the current DHCP address works, use it temporarily in both, then check Avahi, DNS/mDNS or wireless client isolation. Recheck the address after a lease change.

<!-- page -->
<!-- section: Source installation -->
## Clone the workshop from a VS Code terminal

**Already cloned on Windows?** Keep your existing checkout. Continue with **Open the cloned folder on Windows** on the next page. If the Pi still needs its own copy, transfer the bundle and use the Pi commands below.

For a first installation, save `Robotics_Workshop_Starter.zip` in Downloads. In a **local** VS Code window choose **Terminal > New Terminal**. In the bottom **TERMINAL** panel, use the dropdown beside **+** to select **PowerShell** if needed. Run the following from Windows.

**Local VS Code terminal • Windows PowerShell, fresh installation**

~~~powershell
cd $HOME
$kit = Join-Path $HOME "workshop-kit"
Expand-Archive "$HOME\Downloads\Robotics_Workshop_Starter.zip" $kit
git clone -b main "$kit\workshop.bundle" robotics-workshop
cd robotics-workshop
git rev-parse --short HEAD
git tag --list workshop-v1
~~~

**Local VS Code terminal • Windows PowerShell, transfer the bundle to the Pi**

~~~powershell
scp "$HOME\workshop-kit\workshop.bundle" labpi:workshop.bundle
ssh labpi
~~~

**Pi host • the same terminal after SSH logs in, fresh Pi checkout**

~~~bash
cd ~
git clone -b main ~/workshop.bundle robotics-workshop
cd ~/robotics-workshop
git rev-parse --short HEAD
git tag --list workshop-v1
exit
~~~

**Expected result.** The Windows and Pi clones of the same bundle show matching short revisions, and both contain the original `workshop-v1` tag. If a project folder already exists, inspect its Git status before choosing how to update it. After `exit` you are back in Windows PowerShell.

**Configure a Git author once in each checkout.** In each machine's project terminal, set the name and email you want on your workshop commits. A commit records a snapshot. Stage files with `git add` to choose what it contains. A branch names a line of commits.

**Windows PowerShell or Pi host • from the corresponding cloned project root**

~~~bash
git config user.name "Your Name"
git config user.email "your-name@example.edu"
~~~

<!-- page -->
<!-- section: Windows workspace -->
## Open the cloned folder on Windows

### 1. Select the folder in local VS Code

Open **Start > Visual Studio Code** on Windows. Keep your Pi session available in its own window. If the lower-left corner shows **SSH: labpi**, **WSL** or a container connection, choose **File > New Window** and use a local window.

Choose **File > Open Folder...**. In the Windows folder chooser, browse to **This PC > C: > Users > your account > robotics-workshop**. Alternatively, click the address bar, paste the full folder path and press Enter. For the example Windows account it is `C:\Users\student\robotics-workshop`. Click **Select Folder**. Confirm Workspace Trust if prompted and you recognize the course folder. [VS Code folders and workspaces](https://code.visualstudio.com/docs/editing/workspaces/workspaces)

If you are already at the cloned root in Windows PowerShell, the shortcut `code -n .` opens the current folder in a new VS Code window. Use **File > Open Folder...** if Windows cannot find the `code` command. [VS Code command line](https://code.visualstudio.com/docs/configure/command-line)

### 2. Identify the project root

Press **Ctrl+Shift+E** to open **Explorer**. Look for `operator_app`, `robot_lab`, `settings`, `requirements-windows.txt` and `README.md` directly under the top folder. If you see `workshop.bundle` next to `source`, the selected folder is the extracted kit. Reopen the cloned `robotics-workshop` folder.

### 3. Start PowerShell inside that window

Choose **Terminal > New Terminal**. In the panel below the editor click **TERMINAL**. If the terminal tab names a different shell, click the arrow beside **+** and select **PowerShell** or **Windows PowerShell**. Paste each command at the prompt and press Enter. [VS Code integrated terminal](https://code.visualstudio.com/docs/terminal/basics)

**Local VS Code terminal • Windows PowerShell**

~~~powershell
Get-Location
Test-Path .\requirements-windows.txt
Test-Path .\operator_app\__main__.py
git status --short --branch
~~~

**Expected result.** A Windows path ending in `\robotics-workshop`, two `True` values and the current branch (initially `main`). If the terminal starts in another Windows folder, run `Set-Location "$HOME\robotics-workshop"`. If the prompt starts with the Pi username and hostname, use the local VS Code window. Leave this window open for the operator GUI.

<!-- page -->
<!-- section: Docker on the Pi -->
## Build the headless ROS environment

From a fresh Ubuntu Jammy installation, the included installer adds Docker's official apt signing key and Ubuntu repository, then installs Docker Engine, the CLI, Buildx and Compose. Review the script in VS Code. If Docker is already installed and `docker compose version` works, use the existing installation. On a previously managed Pi consult its owner before replacing conflicting distribution packages. [Docker Engine for Ubuntu](https://docs.docker.com/engine/install/ubuntu/)

Keep the Windows project open. In a second VS Code window press **Ctrl+Shift+P**, select **Remote-SSH: Connect to Host...**, and choose `labpi`. Once the status bar shows **SSH: labpi**, choose **File > Open Folder...**, enter `/home/robot/robotics-workshop` (adjust for the station user), then choose **Terminal > New Terminal**.

**Pi host over SSH • integrated terminal in the remote VS Code window**

~~~bash
cd ~/robotics-workshop
sudo bash tools/install_docker_ubuntu.sh
sudo usermod -aG docker "$USER"
exit
~~~

Close the remote VS Code connection after changing group membership. In the local VS Code PowerShell terminal run `ssh labpi` to obtain a fresh Pi login for the following commands. Membership in the Docker group grants host-level administrative capability. On centrally managed stations the administrator can prepare the user or run Docker commands for the class.

**Pi host over SSH • new login**

~~~bash
cd ~/robotics-workshop
docker version
docker compose version
printf 'LAB_UID=%s\nLAB_GID=%s\n' "$(id -u)" "$(id -g)" > .env
docker compose config
docker compose --progress plain build
docker compose up -d
docker compose ps
docker compose exec robot lab-env python3 /opt/lab/tools/accept_station.py
~~~

**Expected result.** A completed fresh build includes the real offscreen motion check. The final command runs on the Pi, deliberately moves the simulator, records both topics and reports two PASS results. Disconnect all operator GUIs for that check. The directory `runs` exists in the cloned repo and is mounted as `/runs`. The UID/GID settings let the host user read and edit the files.

**Troubleshoot in order.** A Docker socket permission error calls for a new SSH login. For package download errors, check internet access, DNS and free space. A Qt error belongs to the simulator image. Inspect its build log and `docker compose logs robot`. An occupied UDP port points to another process or second Compose stack using port 5005.

**Where ROS runs.** Both nodes share one container, where discovery uses localhost. Docker publishes only the Pi command port as UDP 5005 to the classroom network. `docker compose exec robot lab-env bash` loads both the base Humble environment and the workshop overlay. [Official ROS image](https://hub.docker.com/_/ros) · [Headless turtlesim example](https://github.com/livekit/ros-portal/blob/main/docs/tutorials.md)

<!-- page -->
<!-- section: Windows operator -->
## Install Python dependencies and run the GUI

Return to the local VS Code window opened on page 4. Choose **Terminal > New Terminal**. Confirm the PowerShell prompt ends in `\robotics-workshop>`. A Python virtual environment is a project folder that holds its interpreter and dependencies.

### First setup on this Windows checkout

**Local VS Code terminal • Windows PowerShell**

~~~powershell
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements-windows.txt
.\.venv\Scripts\python.exe -m tkinter
~~~

The first command should report `Python 3.11.x`. If it fails, install the 64-bit Python 3.11 runtime and launcher, then reopen VS Code. Close the small Tk test window with **X** to get the prompt back. The launch command uses the interpreter in `.venv` directly. [Python virtual environments](https://docs.python.org/3.11/library/venv.html)

**Local VS Code terminal • Windows PowerShell, installation check**

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
~~~

Expect `OK`. Plug the wired Logitech into the laptop. In the same terminal run `joy.cpl`, select the controller, test the axes in **Properties**, and close the Windows controller panel.

### Every workshop session

**Local VS Code terminal • Windows PowerShell, cloned project root**

~~~powershell
.\.venv\Scripts\python.exe -m operator_app
~~~

A separate **Robot operator • turtlesim** window opens in **Local preview** with the badge **OFFLINE**. Move the stick and check the raw axes. Once the Pi service is running, enter the station hostname, center the stick and select **Connect**. Look for **FRESH**, an advancing `ack` and a changing pose.

| What you see | What to do in VS Code |
|---|---|
| No prompt while the GUI is open | This terminal is running the app. Choose **Terminal > New Terminal** for another PowerShell prompt. Close the GUI with **X** to return to the original prompt. |
| `No module named pygame` | Use the pip command above from the same project and relaunch with the relative `.venv` interpreter. |
| Wrong forward/turn axis or sign | In Explorer click **settings > operator.json**. Edit the mapping, press **Ctrl+S**, close the GUI and rerun the launch command in its original terminal. |

On connection the GUI writes the effective settings to `local/operator-session.json`. Copy that file to the experiment folder before the next connection. For an empty GUI map, compare the Pi command and pose streams. A changing `/turtle1/cmd_vel` verifies the forward path on UDP 5005. If `/turtle1/pose` changes too, check the return path on UDP 5006 using page 4 of the Instructor Preparation Guide. [pygame joystick API](https://www.pygame.org/docs/ref/joystick.html) · [pygame 2.6.1](https://pypi.org/project/pygame/2.6.1/)

<!-- page -->
<!-- section: Sharing and repeat installation -->
## Publish history and preserve a run

Create an empty GitHub repository for the course and choose its visibility. Keep its HTTPS or SSH clone URL at hand. For an HTTPS remote, use Git Credential Manager or the course's approved sign-in when prompted. From the original Windows clone, point the offline bundle's `origin` at that repository and upload the prepared history. [GitHub import guide](https://docs.github.com/en/repositories/creating-and-managing-repositories/adding-locally-hosted-code-to-github)

In the local terminal below, run the first line, then paste the repository URL when PowerShell asks for it and press Enter.

**Local VS Code terminal • Windows PowerShell in the cloned repository**

~~~powershell
$CourseRepo = Read-Host "Paste the empty course repository clone URL"
git remote set-url origin $CourseRepo
git push -u origin main
git push origin workshop-v1
~~~

After the student's Block 7 commit, `git push -u origin lab/lower-speed` shares the exercise branch. A collaborator with access can clone the course URL in place of the bundle. On an existing Pi clone, use the next commands to fetch its branches and tags. Keep each team's experimental revision in its run folder.

**Pi host over SSH • repository root, only for an existing GitHub course remote**

~~~bash
read -rp "Course repository clone URL: " course_repo
git remote set-url origin "$course_repo"
git fetch origin --tags
git log --oneline --all -4
~~~

### Repeat the same experiment later

Open `operator.json` and `pi-commit.txt` from the run. On each machine make a fresh clone, then `git switch --detach` followed by that machine's recorded revision on the same command line. Restore the recorded mapping, hostname and bridge parameters. Start from the recorded pose. Keep code, bag, CSV and notes together when moving the run to other storage.

For an exact Pi software environment, preserve the built image in advance. The following uses a named image tag. The `docker save` command can create a large archive. Keep it with the runs you wish to reproduce.

**Pi host over SSH • repository root**

~~~bash
cid=$(docker compose ps -q robot)
img=$(docker inspect --format '{{.Image}}' "$cid")
docker tag "$img" robotics-workshop:class-image
docker save -o runs/class-image.tar robotics-workshop:class-image
~~~

On the new Pi load it with `docker load -i runs/class-image.tar`. Add `image: robotics-workshop:class-image` to the `robot` service beside `build:`, then start with `docker compose up -d --no-build`. Compare the running image ID with the run record. Actual recorded inputs can be replayed. Repeating a human maneuver introduces normal timing variation.

<!-- page -->
<!-- section: Source map -->
## Find the code behind each interface

Open the same repository in the two VS Code windows. Use the local checkout when editing operator code and use the SSH checkout when editing the bridge or container. The diagram files and Markdown guides are editable.

**Project tree • relative to the cloned repository**

~~~text
robotics-workshop/
  operator_app/
    __main__.py     gui.py        joystick.py      mapping.py
  robot_lab/
    bridge_node.py  transport.py  control.py       protocol.py
    link.py
  settings/operator.json
  launch/workshop.launch.py
  package.xml       setup.py      setup.cfg        resource/robot_lab
  Dockerfile        compose.yaml  docker/lab-env
  requirements-windows.txt
  tools/
    install_docker_ubuntu.sh      verify_headless.py
    station_check.py              accept_station.py
    new_run.sh                    inspect_bag.py
  tests/            docs/         runs/
~~~

| Follow a command | Class or file to open |
|---|---|
| Read USB axes and convert them to body speed | `JoystickReader` in `joystick.py` and `Mapping` in `mapping.py` |
| Schedule an update, send a request and mark a missing reply | `OperatorWindow` in `gui.py` and `OperatorLink` in `link.py` |
| Validate messages, learn the sender and decide when to stop | `Command` / `PosePacket` in `protocol.py`, `BridgeTransport` and `CommandGate` |
| Publish Twist and subscribe to measured pose | `UdpBridge` in `bridge_node.py`, started by `launch/workshop.launch.py` |
| Read recorder timestamps and match a response | `OnsetComparison` in `tools/inspect_bag.py` |

**Try a source trace.** Start at `OperatorWindow.tick`. Find the call that sends `v` and `w`. On the Pi side find the assignment to `msg.linear.x` and `msg.angular.z`. Trace the return through `on_pose` and `telemetry_tick` back to `OperatorWindow.draw`.

<!-- page -->
<!-- section: Optional extension and references -->
## Where a serial device would fit

The wired joystick enumerates as a USB game controller. Windows exposes axes and buttons, which pygame reads locally. A UART instead moves serial bytes between a transmitter and a receiver using agreed electrical levels and timing. A USB-to-UART adapter exposes a serial port to the computer. A bridge would parse device frames before creating ROS messages.

### Optional adapter loopback after class

Use a labeled USB-to-TTL serial adapter by itself. With it unplugged, join its own TXD to its own RXD, leave its power pin unconnected, then plug it into Windows. Identify its COM port under **Device Manager → Ports**. Use a serial terminal (for example PuTTY in Serial mode) at 115200 baud, 8 data bits, no parity, 1 stop bit and no flow control. Turn local echo off.

Type a few characters. With the jumper fitted, the receiver should display the characters you transmitted. Unplug the adapter before removing the jumper, reconnect, then type again. With local echo off the characters should disappear. If they still appear, check the terminal's local echo and selected COM port. This independent exercise uses no GPIO pins and adds no time to the core session.

### Upstream references

- The ROS 2 Humble lessons introduce nodes, topics, services and simulator conventions. [Introducing turtlesim](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Introducing-Turtlesim/Introducing-Turtlesim.html)
- The Humble recording tutorial covers topic selection, bag inspection and playback. [Recording and playing back data](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data/Recording-And-Playing-Back-Data.html)
- The Qt platform layer provides the backend used by the simulator's GUI. The optional Pi screen is replaced by the offscreen backend in the workshop image. [Qt platform abstraction](https://doc.qt.io/qt-5/qpa.html)
- Git bundles transfer repository objects and named references for offline cloning. [Git bundle manual](https://git-scm.com/docs/git-bundle)
- Windows firewall rules can be scoped to a protocol, local port, source address and active profile. [Microsoft firewall rule reference](https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallrule)
- The Ubuntu guide describes preparing storage and first boot on a Raspberry Pi. [Ubuntu on Raspberry Pi](https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi)

**Commissioning record.** Use page 7 of the Instructor Preparation Guide to distinguish the delivered software tests from the checks performed on your actual Windows laptop, Raspberry Pi 4 and classroom network.
