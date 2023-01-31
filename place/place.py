"""Monochromatic pixel placement app."""
from PIL import Image
import numpy as np
from enum import Enum


class Colors(Enum):
    COLOR_KEY = (0, 0, 0)
    ACTIVE = 96  # (102, 102, 102)
    INACTIVE = 189  # (255, 255, 204)


class App:
    def __init__(
        self,
        width: int = 64,
        height: int = 64,
    ) -> None:
        self.resolution = (width, height)
        self.pixels = [Colors.INACTIVE] * (width * height)
        self._owners = {}

    def update(self):
        """Main game update step, it should be called in a loop to progress the
        game at the game's framerate."""
        pass

    def click_at(self, x, y, owner=None):
        """User clicks x,y coordinates and we toggle that pixel's color"""
        idx = y * self.resolution[0] + x
        pixel_state = self.pixels[idx]
        self.pixels[idx] = (
            Colors.ACTIVE if pixel_state == Colors.INACTIVE else Colors.INACTIVE
        )
        self._owners[(y, x)] = owner

    @property
    def owners_map(self):
        """Each pixel can have an owner, that's the last user that clicked on it"""
        return self._owners

    @property
    def frame(self):
        return Image.fromarray(
            np.array([x.value for x in self.pixels], dtype=np.uint8).reshape(
                self.resolution
            )
        )

    @property
    def finished(self) -> bool:
        """Returns true if the game ended."""
        return False
