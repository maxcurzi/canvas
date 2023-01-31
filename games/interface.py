"""Common interface for games to be run within Canvas.
Any game could be a Canvas game as long as it implements this interface.
Example use in the Canvas backend:

from apps.interface import CanvasApp
from invaders.invaders import Game as SpaceInvaders

class CanvasInvaders(SpaceInvaders, CanvasApp):
    pass

A = CanvasInvaders()
while True:
    A.update()
    print(A.owners_map) # Or do something with it
    A.click_at(10, 60, "Some_owner") # Add user inputs
"""
from abc import ABC, abstractmethod
from PIL.Image import Image


class InterfaceError(Exception):
    pass


class CanvasApp(ABC):
    @abstractmethod
    def update(self):
        """Main 'tick' method that advances the game logic. Typically called in
        a loop.
        """
        pass

    @abstractmethod
    def click_at(self, x, y, owner=None):
        """User inputs are clicks to the grid pixels, we add these inputs to a
        queue for later processing, and we store an identifier of who clicked
        it, for later retrieval/identification of who caused a certain effect."""
        pass

    @property
    @abstractmethod
    def owners_map(self):
        """Each pixel can have an owner, for example when a player clicks on the
        spaceship to shoot a rocket, the pixels composing the rocket will
        'belong' to that user."""
        pass

    @property
    @abstractmethod
    def frame(self) -> Image:
        """Returns current app frame"""
        pass

    @property
    @abstractmethod
    def finished(self) -> bool:
        """Returns true if the game ended."""
        pass
