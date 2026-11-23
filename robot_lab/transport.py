"""UDP and watchdog implementation shared by the ROS bridge and its loopback test."""

import socket
import time

from robot_lab.control import CommandGate
from robot_lab.protocol import Command, MAX_BYTES, PacketError, PosePacket, encode


class BridgeTransport:
    def __init__(self, bind=("0.0.0.0", 5005), clock=time.monotonic):
        self.clock = clock
        self.gate = CommandGate(timeout_s=0.5)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(bind)
        self.socket.setblocking(False)
        self.tx_sequence = 0

    def control(self):
        # Bound work per tick so a burst of datagrams cannot starve zero publication.
        for _ in range(64):
            try:
                data, peer = self.socket.recvfrom(MAX_BYTES + 1)
            except BlockingIOError:
                break
            try:
                cmd = Command.decode(data)
            except PacketError:
                continue
            self.gate.accept(cmd, peer, self.clock())
        return self.gate.velocity(self.clock())

    def send_pose(self, x, y, theta, v, w):
        if self.gate.peer is None:
            return False  # The return address is learned from the first valid command.
        cmd = self.gate.command
        packet = PosePacket(cmd.session, self.tx_sequence, cmd.seq, x, y, theta,
                            v, w, self.gate.expired(self.clock()))
        self.tx_sequence += 1
        try:
            self.socket.sendto(encode(packet), self.gate.peer)
        except OSError:
            return False
        return True

    def close(self):
        self.socket.close()
