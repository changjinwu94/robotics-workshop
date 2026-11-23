"""Start on Windows, from a local checkout of the workshop repository."""

import argparse
import tkinter as tk

from operator_app.gui import OperatorWindow
from operator_app.joystick import JoystickReader
from operator_app.mapping import load_settings

def main():
    host, mapping = load_settings()
    parser = argparse.ArgumentParser(description="USB gamepad to turtlesim operator GUI")
    parser.add_argument("--host", default=host, help="classroom Pi hostname or current DHCP address")
    args = parser.parse_args()
    reader = JoystickReader()
    root = tk.Tk()
    OperatorWindow(root, reader, mapping, args.host)
    root.mainloop()

if __name__ == "__main__":
    main()
