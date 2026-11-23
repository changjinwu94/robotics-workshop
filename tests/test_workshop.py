"""Portable contract tests. All network traffic stays on an ephemeral loopback port."""

import csv
import io
import json
import socket
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from operator_app.mapping import Mapping, load_settings
from robot_lab.control import CommandGate
from robot_lab.link import OperatorLink
from robot_lab.protocol import Command, PacketError, PosePacket, encode
from tools.inspect_bag import CMD, POSE, Sample, export

SESSION = "a" * 32
PEER = ("127.0.0.1", 49120)


def pose(session=SESSION, seq=1):
    return PosePacket(session, seq, 0, 5.54, 5.54, 0.0, 0.0, 0.0, False)


class WireTests(unittest.TestCase):
    def test_round_trip(self):
        for data in [Command(SESSION, 12, 1.0, -0.8), pose()]:
            self.assertEqual(data, type(data).decode(encode(data)))

    def test_bad_commands(self):
        base = json.loads(encode(Command(SESSION, 2, 1.0, 0.0)))
        for key, invalid in [("w", float("nan")), ("v", True), ("w", 100),
                             ("seq", -1), ("seq", True), ("ver", True), ("session", "bad")]:
            with self.subTest(key=key, invalid=invalid), self.assertRaises(PacketError):
                Command.decode(json.dumps({**base, key: invalid}).encode())

    def test_size_type_and_encoding(self):
        for data in (b"{" + b" " * 1000, b"[]", b"\xff", encode(pose())):
            with self.assertRaises(PacketError):
                Command.decode(data)

    def test_pose_requires_ack_and_boolean(self):
        obj = json.loads(encode(pose()))
        for field, value in (("ack", None), ("timed_out", 0)):
            with self.assertRaises(PacketError):
                PosePacket.decode(json.dumps({**obj, field: value}).encode())


class ControlTests(unittest.TestCase):
    def test_timeout_boundaries(self):
        gate = CommandGate()
        self.assertEqual(gate.velocity(10), (0, 0))
        gate.accept(Command(SESSION, 1, 2.0, 0.5), PEER, 10)
        self.assertEqual(gate.velocity(10.499), (2.0, 0.5))
        self.assertEqual(gate.velocity(10.5), (0, 0))

    def test_reorder_does_not_refresh(self):
        gate = CommandGate()
        gate.accept(Command(SESSION, 5, 1, 0), PEER, 0)
        for seq in (4, 5):
            self.assertFalse(gate.accept(Command(SESSION, seq, 1, 0), PEER, 0.49))
        self.assertTrue(gate.expired(0.5))
        self.assertTrue(gate.accept(Command(SESSION, 6, 1, 0), PEER, 0.51))

    def test_peer_handoff_only_after_expiry(self):
        gate = CommandGate()
        gate.accept(Command(SESSION, 4, 1, 0), PEER, 1)
        new = Command("b"*32, 0, 0, 1)
        second = (PEER[0], 49121)
        self.assertFalse(gate.accept(new, second, 1.2))
        self.assertTrue(gate.accept(new, second, 1.51))
        self.assertEqual(gate.peer, second)

    def test_shipped_settings_load(self):
        host, mapping = load_settings()
        self.assertTrue(host)
        self.assertIsInstance(mapping, Mapping)

    def test_deadband_scale_and_axes(self):
        mapping = Mapping(1, 0, -1, -1, 0.12, 2.0, 2.0)
        self.assertEqual(mapping.velocity([0.12, -0.12]), (0, 0))
        self.assertEqual(mapping.velocity([1, -1]), (2, -2))
        self.assertAlmostEqual(mapping.velocity([0, -0.56])[0], 1.0)
        with self.assertRaises(ValueError):
            mapping.velocity([0])


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(self.server.close)
        self.server.bind(("127.0.0.1", 0))
        self.server.settimeout(1)
        self.now = 1.0
        self.link = OperatorLink("localhost", self.server.getsockname()[1], 0, lambda: self.now)
        self.addCleanup(self.link.close)

    def test_bidirectional_and_independent_freshness(self):
        self.assertEqual(self.link.freshness()[0], "WAITING")
        self.link.send(1.0, -0.5)
        raw, learned_endpoint = self.server.recvfrom(768)
        cmd = Command.decode(raw)
        self.assertEqual((cmd.v, cmd.w, cmd.seq), (1.0, -0.5, 0))
        self.assertEqual(learned_endpoint[1], self.link.socket.getsockname()[1])
        self.server.sendto(encode(pose(cmd.session, 3)), learned_endpoint)
        self.link.poll()
        self.assertEqual(self.link.freshness(), ("FRESH", 0.0))
        self.now = 2.01
        self.link.send(1.0, -0.5)
        self.server.sendto(encode(pose(cmd.session, 2)), learned_endpoint)
        self.server.sendto(encode(pose("c"*32, 9)), learned_endpoint)
        self.link.poll()
        self.assertEqual(self.link.freshness()[0], "STALE")
        self.server.sendto(encode(pose(cmd.session, 4)), learned_endpoint)
        self.link.poll()
        self.assertEqual(self.link.freshness()[0], "FRESH")

    def test_no_first_pose_becomes_stale(self):
        self.now = 2.0
        self.assertEqual(self.link.freshness()[0], "STALE")


class BagAnalysisTests(unittest.TestCase):
    def test_onset_and_csv(self):
        samples = [Sample(100, CMD, 0, 0), Sample(200, POSE, 0, 0, 5, 5, 0),
                   Sample(300, CMD, 1, 0), Sample(350, POSE, 0, 0, 5, 5, 0),
                   Sample(1500300, POSE, 1, 0, 5.02, 5, 0)]
        with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()) as stdout:
            path = Path(d) / "samples.csv"
            self.assertTrue(export(samples, path))
            self.assertIn("1.5 ms", stdout.getvalue())
            with path.open() as stream:
                self.assertEqual(list(csv.DictReader(stream))[-1]["x_u"], "5.02")

    def test_no_stationary_baseline(self):
        with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
            self.assertFalse(export([Sample(10, CMD, 1, 0)], Path(d) / "samples.csv"))
