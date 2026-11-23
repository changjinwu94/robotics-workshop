#!/usr/bin/env bash
# Use on the Pi host, in the repository root. The bag goes into this run folder.
set -euo pipefail
if [[ $# != 1 || ! $1 =~ ^[[:alnum:]][[:alnum:]_-]*$ ]]; then
  echo "Usage: bash tools/new_run.sh arc01" >&2
  exit 2
fi
folder="runs/$1"
mkdir "$folder"  # Fails clearly if the name already exists; never overwrite evidence.
git rev-parse HEAD > "$folder/pi-commit.txt"
git status --porcelain > "$folder/pi-status.txt"
git diff --binary HEAD > "$folder/pi-tracked.patch"
docker compose config > "$folder/compose.yaml"
container_id=$(docker compose ps -q robot)
docker inspect --format '{{.Image}}' "$container_id" > "$folder/image-id.txt"
{
  date -u --iso-8601=seconds
  hostname
  uname -a
  cat /etc/os-release
  docker version --format '{{.Server.Version}}'
  docker compose version
} > "$folder/pi-platform.txt"
docker compose exec -T robot lab-env ros2 param dump /udp_bridge > "$folder/bridge-params.yaml"
docker compose exec -T robot lab-env dpkg-query -W ros-humble-turtlesim \
  ros-humble-rclpy ros-humble-rosbag2 'libqt5gui5*' > "$folder/packages.txt"
cat > "$folder/notes.txt" <<'NOTES'
Operator / team:
Controller model and switch position:
Starting pose and reset procedure:
Maneuver and approximate timing:
Observation:
NOTES
echo "Run folder ready: $folder. Copy the Windows operator-session.json and fill notes.txt."
