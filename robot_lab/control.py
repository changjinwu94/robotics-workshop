"""Control decisions that can be exercised without ROS, USB or a GUI."""

class CommandGate:
    """One laptop controls one turtle. Both the address and session identify the sender."""

    def __init__(self, timeout_s=0.5):
        self.timeout_s = timeout_s
        self.peer = None
        self.command = None
        self.received_at = None

    def expired(self, now):
        return self.received_at is None or now - self.received_at >= self.timeout_s

    def accept(self, command, peer, now):
        if self.command is not None:
            same_sender = peer == self.peer and command.session == self.command.session
            if same_sender and command.seq <= self.command.seq:
                return False  # Old/duplicate packets must never extend the watchdog.
            if not same_sender and not self.expired(now):
                return False
        self.peer, self.command, self.received_at = peer, command, now
        return True

    def velocity(self, now):
        if self.expired(now):
            return 0.0, 0.0
        return self.command.v, self.command.w
