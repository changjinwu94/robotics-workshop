"""Tk view of operator intent, packet freshness and the simulator's reported pose."""

import json
import math
import platform
import subprocess
import time
import tkinter as tk
from dataclasses import asdict
from tkinter import ttk

from robot_lab.link import OperatorLink
from operator_app.mapping import ROOT


def git_output(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True,
                                       stderr=subprocess.DEVNULL, timeout=3).strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


class OperatorWindow:
    def __init__(self, root, reader, mapping, host):
        self.root, self.reader, self.mapping = root, reader, mapping
        self.link, self.timer = None, None
        self.host = tk.StringVar(value=host)
        self.pause_tx = tk.BooleanVar(value=False)
        self.input_text = tk.StringVar(value="Reading USB controller...")
        self.command_text = tk.StringVar()
        self.pose_text = tk.StringVar(value="No pose received")
        self.status = tk.StringVar(value="Local preview")
        self.fresh = tk.StringVar(value="OFFLINE")
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.tick()

    def _build(self):
        self.root.title("Robot operator • turtlesim")
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Label(row, text="Pi hostname").pack(side="left")
        self.entry = ttk.Entry(row, textvariable=self.host, width=26)
        self.entry.pack(side="left", padx=6)
        self.button = ttk.Button(row, text="Connect", command=self.toggle)
        self.button.pack(side="left")
        ttk.Checkbutton(frame, text="Pause command packets", variable=self.pause_tx).pack(anchor="w", pady=4)
        joy_frame = ttk.LabelFrame(frame, text="Controller input (Joy format)", padding=8)
        joy_frame.pack(fill="x", pady=(2, 4))
        ttk.Label(joy_frame, textvariable=self.input_text, font="TkFixedFont",
                  justify="left", wraplength=520).pack(anchor="w")
        for var in (self.command_text, self.status):
            ttk.Label(frame, textvariable=var, wraplength=570).pack(anchor="w", pady=2)
        self.badge = tk.Label(frame, textvariable=self.fresh, anchor="w", padx=7, pady=3)
        self.badge.pack(fill="x", pady=(8, 4))
        ttk.Label(frame, textvariable=self.pose_text).pack(anchor="w")
        self.canvas = tk.Canvas(frame, width=380, height=330, bg="#eef5f4", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=(6, 0))
        self.canvas.bind("<Configure>", lambda _: self.draw())

    def save_session(self):
        # Store the *effective* settings, including a hostname typed into the GUI.
        # The student copies this sidecar to the Pi next to the corresponding bag.
        session = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "host": self.host.get().strip(), "resolved_endpoint": list(self.link.address),
                   "local_port": self.link.socket.getsockname()[1], "session": self.link.session,
                   "command_target_hz": 20, "stale_s": 1.0, "mapping": asdict(self.mapping),
                   "controller": self.reader.name, "python": platform.python_version(),
                   "pygame": self.reader.version, "os": platform.platform(),
                   "git_commit": git_output("rev-parse", "HEAD"),
                   "git_status": git_output("status", "--porcelain")}
        folder = ROOT / "local"
        folder.mkdir(exist_ok=True)
        path = folder / "operator-session.json"
        path.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")

    def toggle(self):
        if self.link is not None:
            self.disconnect()
            return
        try:
            self.link = OperatorLink(self.host.get().strip())
            self.save_session()
        except OSError as exc:
            self.disconnect()
            self.status.set(f"Connection or session-file error: {exc}")
            return
        ip, port = self.link.address
        self.entry.state(["disabled"])
        self.button.configure(text="Disconnect")
        self.status.set(f"UDP target {ip}:{port}  |  laptop port 5006")

    def disconnect(self):
        if self.link is not None:
            try:
                self.link.send(0.0, 0.0)  # Best effort. The Pi timeout covers a lost last packet.
            except OSError:
                pass
            self.link.close()
        self.link = None
        self.pause_tx.set(False)
        self.entry.state(["!disabled"])
        self.button.configure(text="Connect")
        self.status.set("Local preview")
        self.pose_text.set("No pose received")

    def tick(self):
        sample = self.reader.read()
        v, w = 0.0, 0.0
        label = self.reader.name
        axes, buttons, hats = sample if sample is not None else ([], [], [])
        # joy_node appends two axes per hat: positive left and positive up.
        # Keep the original device axes for the velocity mapping below.
        display_axes = axes + [value for x, y in hats for value in (-x, y)]
        axis_values = ", ".join(f"{axis:.3f}" for axis in display_axes)
        button_values = ", ".join(str(button) for button in buttons)
        label += f"\naxes: [{axis_values}]\nbuttons: [{button_values}]"
        if sample is not None:
            try:
                v, w = self.mapping.velocity(axes)
            except ValueError as exc:
                label += f"\n{exc}"
        self.input_text.set(label)
        action = "PREVIEW" if not self.link else ("PAUSED" if self.pause_tx.get() else "SENDING")
        self.command_text.set(f"{action}   requested v {v:+.2f} u/s    w {w:+.2f} rad/s")
        freshness, age = "OFFLINE", 0.0
        if self.link is not None:
            try:
                if not self.pause_tx.get():
                    self.link.send(v, w)
                self.link.poll()
            except OSError as exc:
                self.status.set(f"UDP error: {exc}. Check the Pi and its hostname.")
            freshness, age = self.link.freshness()
            p = self.link.pose
            if p:
                watchdog = "TIMEOUT" if p.timed_out else "LIVE"
                self.pose_text.set(f"x {p.x:.2f} u   y {p.y:.2f} u   heading {p.theta:+.2f} rad\n"
                                   f"measured v {p.v:+.2f} u/s   w {p.w:+.2f} rad/s   "
                                   f"Pi {watchdog}   ack {p.ack}")
        self.fresh.set(f"{freshness}   {age:.1f} s since last pose" if self.link and self.link.pose
                       else f"{freshness}   awaiting first pose" if self.link else "OFFLINE")
        colors = {"FRESH": "#c6e8da", "WAITING": "#fff1c1", "STALE": "#f8cfc9", "OFFLINE": "#e2e7ea"}
        self.badge.configure(bg=colors[freshness])
        self.draw()
        self.timer = self.root.after(50, self.tick)  # Nominal 20 Hz, scheduled after each update.

    def draw(self):
        c = self.canvas
        c.delete("all")
        width, height = c.winfo_width(), c.winfo_height()
        side = min(width - 58, height - 42)
        if side <= 0:
            return
        # The usual turtlesim map spans approximately 11.1 by 11.1 world units.
        # Canvas y grows down the screen, while positive simulator y points up.
        left, top = (width - side) / 2, 13
        c.create_rectangle(left, top, left + side, top + side, outline="#789493")
        c.create_text(left, top + side + 11, anchor="w", text="(0, 0)    +x right    +y up")
        for fraction in (0.25, 0.5, 0.75):
            d = side * fraction
            c.create_line(left+d, top, left+d, top+side, fill="#d4e1df")
            c.create_line(left, top+d, left+side, top+d, fill="#d4e1df")
        if self.link is None or self.link.pose is None:
            c.create_text(width / 2, top + side / 2, text="Waiting for a measured pose")
            return
        p = self.link.pose
        x, y = left + side * p.x / 11.1, top + side * (1.0 - p.y / 11.1)
        color = "#8b9294" if self.link.freshness()[0] == "STALE" else "#086c68"
        c.create_oval(x-5, y-5, x+5, y+5, fill=color, outline=color)
        c.create_line(x, y, x + 23 * math.cos(p.theta), y - 23 * math.sin(p.theta),
                      fill=color, width=3, arrow=tk.LAST)

    def close(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
        self.disconnect()
        self.reader.close()
        self.root.destroy()
