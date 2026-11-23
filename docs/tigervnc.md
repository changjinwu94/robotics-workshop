# See the workshop turtle in TigerVNC

On the Pi, stop any separate VNC demo using port 5901. From the workshop
checkout run:

```bash
docker compose -f compose.yaml -f compose.vnc.yaml up -d --build robot
docker compose -f compose.yaml -f compose.vnc.yaml logs -f robot
```

This recreates the workshop service, so the turtle resets. The UDP bridge
remains on port 5005 and recordings still go to `runs/`. Wait for the turtle
to spawn. Ctrl+C exits the log view.

On Windows, open a local PowerShell terminal and enter your assigned Pi
hostname (such as `robot01.local`, `robot02.local`, or `robot03.local`) and
SSH username when prompted. If the hostname does not resolve, enter the
Pi's current DHCP address.

```powershell
$PiHost = Read-Host "Assigned Pi hostname or IP address"
$PiUser = Read-Host "Pi SSH username"
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:5901:127.0.0.1:5901 "${PiUser}@${PiHost}"
```

Leave the tunnel open. Open TigerVNC Viewer and connect to
`127.0.0.1::5901`. The VNC port on the Pi is published only on loopback.
Use the SSH tunnel for access. In the operator GUI, connect to your Pi as
usual. When the GUI shows a fresh pose, move the joystick and watch the
same turtle in both windows.

To switch back to headless mode on the Pi:

```bash
docker compose -f compose.yaml up -d --build robot
```
