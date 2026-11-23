"""Keep USB input on the laptop where the Logitech controller is plugged in."""

import os


class JoystickReader:
    def __init__(self):
        # Tk owns the visible window. SDL still needs an event pump to refresh axes.
        os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        import pygame
        self.pg = pygame
        pygame.display.init()
        pygame.display.set_mode((1, 1), flags=pygame.HIDDEN)
        pygame.joystick.init()
        self.device = None
        self.name = "No controller"
        self.version = pygame.version.ver

    def read(self):
        """Return all normalized axes. None means disconnected and maps to zero."""
        for event in self.pg.event.get():
            if event.type == self.pg.JOYDEVICEREMOVED and self.device is not None:
                if event.instance_id == self.device.get_instance_id():
                    self.device = None
        try:
            if self.device is None and self.pg.joystick.get_count():
                self.device = self.pg.joystick.Joystick(0)
            if self.device is not None:
                self.name = self.device.get_name()
                return [self.device.get_axis(i) for i in range(self.device.get_numaxes())]
        except self.pg.error:
            self.device = None
        self.name = "No controller"
        return None

    def close(self):
        self.pg.quit()
