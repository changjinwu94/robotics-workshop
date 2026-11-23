"""Version 1 of the classroom protocol. One UTF-8 JSON object per IPv4 UDP datagram."""

import json
import math
import re
from dataclasses import asdict, dataclass

MAX_BYTES = 768
MAX_V = 3.0  # turtlesim world units per second
MAX_W = 4.0  # radians per second


class PacketError(ValueError):
    """The datagram cannot be used as a command or as fresh pose evidence."""


def _seq(value):
    if type(value) is not int or not 0 <= value < 2**53:
        raise PacketError("sequence must be a non-negative integer below 2**53")
    return value


def _number(value):
    if type(value) not in (int, float) or abs(value) > 1e9 or not math.isfinite(value):
        raise PacketError("expected a finite number in the workshop range")
    return float(value)


def _object(data, kind):
    if len(data) > MAX_BYTES:
        raise PacketError("oversized UDP datagram")
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise PacketError("invalid UTF-8 JSON") from exc
    if not isinstance(obj, dict) or type(obj.get("ver")) is not int or obj["ver"] != 1:
        raise PacketError("unrecognized protocol version")
    if obj.get("type") != kind:
        raise PacketError("wrong message type")
    session = obj.get("session")
    if not isinstance(session, str) or not re.fullmatch(r"[0-9a-f]{32}", session):
        raise PacketError("session must be 32 lowercase hex digits")
    _seq(obj.get("seq"))
    return obj


@dataclass(frozen=True)
class Command:
    """One requested body-frame velocity. Positive w turns counterclockwise."""

    session: str
    seq: int
    v: float
    w: float

    @classmethod
    def decode(cls, data):
        obj = _object(data, "cmd")
        v, w = _number(obj.get("v")), _number(obj.get("w"))
        if abs(v) > MAX_V or abs(w) > MAX_W:
            raise PacketError("velocity exceeds bridge limits")
        return cls(obj["session"], obj["seq"], v, w)


@dataclass(frozen=True)
class PosePacket:
    """A simulator measurement plus the last command sequence accepted by the Pi."""

    session: str
    seq: int
    ack: int
    x: float
    y: float
    theta: float
    v: float
    w: float
    timed_out: bool

    @classmethod
    def decode(cls, data):
        obj = _object(data, "pose")
        if type(obj.get("timed_out")) is not bool:
            raise PacketError("timed_out must be a boolean")
        values = [_number(obj.get(k)) for k in ("x", "y", "theta", "v", "w")]
        return cls(obj["session"], obj["seq"], _seq(obj.get("ack")), *values, obj["timed_out"])


def encode(packet):
    kind = "cmd" if isinstance(packet, Command) else "pose"
    envelope = {"ver": 1, "type": kind, **asdict(packet)}
    return json.dumps(envelope, allow_nan=False, separators=(",", ":")).encode("utf-8")
