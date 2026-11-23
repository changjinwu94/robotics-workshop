#!/usr/bin/env bash
# For a fresh Ubuntu Server 22.04 Pi. Use the official Docker Ubuntu apt repository.
set -euo pipefail
if [[ $(id -u) != 0 ]]; then echo "Run with sudo." >&2; exit 1; fi
source /etc/os-release
if [[ $ID != ubuntu || $VERSION_CODENAME != jammy ]]; then
  echo "This workshop installer targets Ubuntu 22.04 (jammy)." >&2
  exit 1
fi
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
key=$(mktemp)
trap 'rm -f "$key"' EXIT
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o "$key"
install -m 0644 "$key" /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<SOURCES
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $VERSION_CODENAME
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
SOURCES
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
