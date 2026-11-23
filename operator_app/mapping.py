"""Map two centered joystick axes to signed body velocities."""

import json
import math
from dataclasses import dataclass
from pathlib import Path

from robot_lab.protocol import MAX_V, MAX_W

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Mapping:
    forward_axis: int
    turn_axis: int
    forward_sign: int
    turn_sign: int
    deadband: float
    max_v: float
    max_w: float

    def __post_init__(self):
        axes = (self.forward_axis, self.turn_axis)
        if any(type(i) is not int or i < 0 for i in axes) or axes[0] == axes[1]:
            raise ValueError("select two distinct non-negative axis indices")
        if any(type(s) is not int or s not in (-1, 1) for s in (self.forward_sign, self.turn_sign)):
            raise ValueError("axis signs must be -1 or 1")
        for value, limit, name in [(self.max_v, MAX_V, "max_v"), (self.max_w, MAX_W, "max_w")]:
            if type(value) not in (int, float) or not 0 < value <= limit:
                raise ValueError(f"{name} must be positive and at most {limit}")
        if type(self.deadband) not in (int, float) or not 0 <= self.deadband < 1:
            raise ValueError("deadband must be in [0, 1)")

    def scale(self, raw):
        # Remove the central interval, then stretch the rest back to full scale.
        magnitude = max(0.0, min(abs(raw), 1.0) - self.deadband)
        return math.copysign(magnitude / (1.0 - self.deadband), raw)

    def velocity(self, axes):
        if max(self.forward_axis, self.turn_axis) >= len(axes):
            raise ValueError("selected axis missing; inspect raw axes and edit settings/operator.json")
        v = self.max_v * self.forward_sign * self.scale(axes[self.forward_axis])
        w = self.max_w * self.turn_sign * self.scale(axes[self.turn_axis])
        return v, w


def load_settings(path=ROOT / "settings" / "operator.json"):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data["host"], str) or not data["host"].strip():
        raise ValueError("host must contain the Pi hostname")
    return data["host"], Mapping(**data["mapping"])
