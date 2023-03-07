"""Monochromatic pixel placement app."""
from enum import Enum

import numpy as np
from PIL import Image


class Colors(Enum):
    """Colors for the game."""

    COLOR_KEY = (0, 0, 0)
    ACTIVE = 96  # (102, 102, 102)
    INACTIVE = 189  # (255, 255, 204)


class App:
    """Monochromatic pixel placement app."""

    def __init__(
        self,
        width: int = 64,
        height: int = 64,
    ) -> None:
        self._resolution = (width, height)
        self.pixels = [Colors.INACTIVE] * (width * height)
        self._owners = {}

    def update(self):
        """Main game update step, it should be called in a loop to progress the
        game at the game's framerate."""

    def click_at(self, x_pos, y_pos, owner=None):
        """User clicks x,y coordinates and we toggle that pixel's color"""
        idx = y_pos * self._resolution[0] + x_pos
        pixel_state = self.pixels[idx]
        self.pixels[idx] = (
            Colors.ACTIVE if pixel_state == Colors.INACTIVE else Colors.INACTIVE
        )
        self._owners[(y_pos, x_pos)] = owner

    @property
    def owners_map(self):
        """Each pixel can have an owner, that's the last user that clicked on it"""
        return self._owners

    @property
    def frame(self):
        """Returns current app frame"""
        return Image.fromarray(
            np.array([x.value for x in self.pixels], dtype=np.uint8).reshape(
                self._resolution
            )
        )

    @property
    def finished(self) -> bool:
        """Returns true if the game ended."""
        return False

    @property
    def resolution(self):
        """Returns current app resolution in pixels"""
        return self._resolution
