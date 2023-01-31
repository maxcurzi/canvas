from PIL import Image  # , ImageOps
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
        self._owners = [None] * (width * height)

    def update(self):
        """Main game update step, it should be called in a loop to progress the
        game at the game's framerate."""
        pass

    def click_at(self, x, y, owner=None):
        """User inputs are clicks to the grid pixels, we add these inputs to a
        queue for later processing, and we store an identifier of who clicked
        it, for later retrieval/identification of who caused a certain effect."""
        idx = y * self.resolution[0] + x
        pixel_state = self.pixels[idx]
        self.pixels[idx] = (
            Colors.ACTIVE if pixel_state == Colors.INACTIVE else Colors.INACTIVE
        )
        self._owners[idx] = owner

    @property
    def owners_map(self):
        """Each pixel can have an owner, for example when a player clicks on the
        spaceship to shoot a rocket, the pixels composing the rocket will
        'belong' to that user."""
        om = {}
        for idx, owner in enumerate(self._owners):
            if owner is not None:
                om[idx] = owner
        return om

    @property
    def frame(self):
        return Image.fromarray(
            np.array([x.value for x in self.pixels], dtype=np.uint8).reshape(
                self.resolution
            )
        )  # .rotate(-90)

    @property
    def finished(self) -> bool:
        """Returns true if the game ended."""
        return False


a = App()
a.click_at(2, 10, "John")
b = a.frame
b.save("lolsid.png")
