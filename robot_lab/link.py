"""One bound socket sends commands and receives pose from the same Pi port."""

import socket
import time
import uuid

from robot_lab.protocol import Command, MAX_BYTES, PacketError, PosePacket, encode


class OperatorLink:
    def __init__(self, host, remote_port=5005, local_port=5006, clock=time.monotonic):
        address = socket.getaddrinfo(host, remote_port, family=socket.AF_INET,
                                     type=socket.SOCK_DGRAM)[0][4]
        self.clock = clock
        self.started = clock()
        self.address = address
        self.session = uuid.uuid4().hex
        self.seq = 0
        self.pose = None
        self.received_at = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.socket.bind(("", local_port))
            self.socket.connect(address)  # Filters return datagrams to this IPv4 Pi endpoint.
            self.socket.setblocking(False)
        except OSError:
            self.socket.close()
            raise

    def send(self, v, w):
        self.socket.send(encode(Command(self.session, self.seq, v, w)))
        self.seq += 1

    def poll(self):
        """Drain queued feedback. Only a newer, valid pose resets the Windows timer."""
        for _ in range(64):
            try:
                data = self.socket.recv(MAX_BYTES + 1)
            except BlockingIOError:
                return
            try:
                packet = PosePacket.decode(data)
            except PacketError:
                continue
            if packet.session != self.session or (self.pose and packet.seq <= self.pose.seq):
                continue
            self.pose, self.received_at = packet, self.clock()

    def freshness(self):
        base = self.started if self.received_at is None else self.received_at
        age = max(0.0, self.clock() - base)
        if age >= 1.0:
            return "STALE", age
        return ("WAITING" if self.pose is None else "FRESH"), age

    def close(self):
        self.socket.close()
