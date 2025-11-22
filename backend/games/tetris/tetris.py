#!/usr/bin/env python
""" Tetris game for Canvas backend.
Controls: Click on piece to rotate, click away from piece to move it by one pixel.
"""
import argparse
import os
import random
from collections import deque
from datetime import datetime
from enum import Enum, auto
from itertools import product

import numpy as np
import pygame
from PIL import Image, ImageOps


class Colors(Enum):
    """Colors for the game. Uses single integer values for compatibility."""

    COLOR_KEY = 0  # Transparency color key
    BLACK = 0
    WHITE = 255
    CYAN = 51      # Light blue for L piece
    BLUE = 68       # Blue for I piece
    ORANGE = 69     # Orange for L piece
    YELLOW = 70     # Yellow for Square (O piece)
    GREEN = 71      # Green for one piece
    RED = 73        # Red for the other piece
    PURPLE = 72     # Not used anymore
    GRID = 50


class TetrominoType(Enum):
    """Tetromino shapes"""
    I = auto()
    O = auto()
    T = auto()
    S = auto()
    Z = auto()
    J = auto()
    L = auto()


class Game:
    def __init__(
        self,
        width: int = 64,
        height: int = 64,
        framerate: float = 10,
        use_defaults=True,
    ) -> None:
        pygame.init()  # pylint:disable=no-member

        self._resolution = (width, height)
        self.screen = pygame.display.set_mode((width, height))
        self.framerate = framerate
        self.clock = pygame.time.Clock()

        # Game area (leave space for UI)
        self.game_width = 10
        self.game_height = 20
        self.cell_size = min(width // (self.game_width + 4), height // self.game_height)
        self.game_offset_x = (width - self.game_width * self.cell_size) // 2
        self.game_offset_y = (height - self.game_height * self.cell_size) // 2

        # Game state
        self.board = [[Colors.BLACK.value for _ in range(self.game_width)] for _ in range(self.game_height)]
        self.current_piece = None
        self.next_piece_type = random.choice(list(TetrominoType))
        self.score = 0
        self.lines_cleared = 0
        self.game_over = False
        self.drop_timer = 0
        self.drop_speed = 30  # frames between automatic drops

        self.pixel_inputs = pygame.sprite.Group()
        self.changed_pixels = set()  # Track which pixels changed
        self.last_frame = None
        
        # For compatibility with wsserver
        class PixelWrapper:
            def __init__(self, value):
                self.value = value
        
        self.pixels = [PixelWrapper(Colors.BLACK.value) for _ in range(width * height)]

        if use_defaults:
            self._spawn_piece()

    def update(self):
        """Main game update step, it should be called in a loop to progress the
        game at the game's framerate."""
        if self.game_over:
            self._draw()
            pygame.display.flip()
            self.clock.tick(self.framerate)
            return

        self._handle_pixel_inputs()
        
        # Automatic drop
        self.drop_timer += 1
        if self.drop_timer >= self.drop_speed:
            self.drop_timer = 0
            if not self._move_piece(0, 1):
                self._lock_piece()
                self._clear_lines()
                self._spawn_piece()
                if not self._is_valid_position(self.current_piece):
                    self.game_over = True

        self._draw()
        pygame.display.flip()
        self.clock.tick(self.framerate)

    def click_at(self, x, y, owner=None):
        """User inputs are clicks to the grid pixels, we add these inputs to a
        queue for later processing, and we store an identifier of who clicked
        it, for later retrieval/identification of who caused a certain effect."""
        click_sprite = Game.UserInput(x, y, owner)
        self.pixel_inputs.add(click_sprite)

    @property
    def owners_map(self):
        """Each pixel can have an owner, for example when a player clicks on the
        piece to rotate it, the pixels composing the piece will
        'belong' to that user."""
        owners_map = {}
        if self.current_piece and hasattr(self.current_piece, 'owner'):
            for px, py in self.current_piece.get_pixels():
                screen_x = self.game_offset_x + px * self.cell_size
                screen_y = self.game_offset_y + py * self.cell_size
                for dx in range(self.cell_size):
                    for dy in range(self.cell_size):
                        if (screen_y + dy < self.screen.get_height() and 
                            screen_x + dx < self.screen.get_width()):
                            owners_map[(screen_y + dy, screen_x + dx)] = self.current_piece.owner
        return owners_map

    @property
    def frame(self):
        """Returns the current game frame as a numpy array."""
        # Capture the actual pygame screen content like invaders does
        return Image.fromarray(np.flipud(pygame.surfarray.array3d(self.screen))).rotate(
            -90
        )

    @property
    def resolution(self) -> tuple[int, int]:
        """Returns the game resolution as a tuple (width, height)."""
        return self._resolution

    @property
    def finished(self) -> bool:
        """Returns true if the game ended."""
        return self.game_over

    def _spawn_piece(self):
        """Spawn a new piece at the top of the board."""
        self.current_piece = Game.Tetromino(self.next_piece_type, self.game_width // 2, 0)
        self.next_piece_type = random.choice(list(TetrominoType))

    def _is_valid_position(self, piece, dx=0, dy=0):
        """Check if piece position is valid."""
        for px, py in piece.get_pixels():
            new_x = px + dx
            new_y = py + dy
            if (new_x < 0 or new_x >= self.game_width or 
                new_y >= self.game_height or
                (new_y >= 0 and self.board[new_y][new_x] != Colors.BLACK.value)):
                return False
        return True

    def _move_piece(self, dx, dy):
        """Move piece if valid."""
        if self._is_valid_position(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False

    def _rotate_piece(self):
        """Rotate piece if valid."""
        original_shape = self.current_piece.shape
        self.current_piece.rotate()
        if not self._is_valid_position(self.current_piece):
            self.current_piece.shape = original_shape

    def _lock_piece(self):
        """Lock piece in place on the board."""
        for px, py in self.current_piece.get_pixels():
            if 0 <= py < self.game_height and 0 <= px < self.game_width:
                self.board[py][px] = self.current_piece.color.value

    def _clear_lines(self):
        """Clear completed lines."""
        lines_to_clear = []
        for y in range(self.game_height):
            if all(self.board[y][x] != Colors.BLACK.value for x in range(self.game_width)):
                lines_to_clear.append(y)

        for y in lines_to_clear:
            del self.board[y]
            self.board.insert(0, [Colors.BLACK.value for _ in range(self.game_width)])

        self.lines_cleared += len(lines_to_clear)
        self.score += len(lines_to_clear) * 100

    def _handle_pixel_inputs(self):
        """User inputs are invisible pixels drawn in the game. We check if
        they collide with the current piece to determine action."""
        if not self.current_piece:
            self.pixel_inputs = pygame.sprite.Group()
            return
            
        # Create a temporary sprite for the current piece for collision detection
        piece_sprite = Game.TetrominoSprite(self.current_piece, self.game_offset_x, self.game_offset_y, self.cell_size)
        
        # Check if user clicked on current piece
        for user_input in self.pixel_inputs:
            piece_clicked = pygame.sprite.spritecollide(
                user_input, [piece_sprite], dokill=False
            )
            if len(piece_clicked) > 0:
                self.current_piece.owner = user_input.owner
                self._rotate_piece()
                self.pixel_inputs.remove(user_input)
        
        # For remaining clicks, move piece one pixel towards click direction
        for user_input in self.pixel_inputs:
            self.current_piece.owner = user_input.owner
            # Move based on click position relative to piece center
            piece_center_x = self.game_offset_x + (self.current_piece.x + 1) * self.cell_size
            if user_input.rect.x < piece_center_x:
                self._move_piece(-1, 0)
            elif user_input.rect.x > piece_center_x:
                self._move_piece(1, 0)
            # Always move down if clicking below piece
            if user_input.rect.y > self.game_offset_y + self.current_piece.y * self.cell_size:
                self._move_piece(0, 1)
        
        self.pixel_inputs = pygame.sprite.Group()

    def _draw(self):
        """Draw the game."""
        self.screen.fill(Colors.BLACK.value)
        
        # Draw board
        for y in range(self.game_height):
            for x in range(self.game_width):
                if self.board[y][x] != Colors.BLACK.value:
                    rect = pygame.Rect(
                        self.game_offset_x + x * self.cell_size,
                        self.game_offset_y + y * self.cell_size,
                        self.cell_size,
                        self.cell_size
                    )
                    # Convert single color value to RGB for pygame
                    color_rgb = self._color_to_rgb(self.board[y][x])
                    pygame.draw.rect(self.screen, color_rgb, rect)
                    pygame.draw.rect(self.screen, self._color_to_rgb(Colors.GRID.value), rect, 1)
        
        # Draw current piece
        if self.current_piece:
            for px, py in self.current_piece.get_pixels():
                if 0 <= px < self.game_width and 0 <= py < self.game_height:
                    rect = pygame.Rect(
                        self.game_offset_x + px * self.cell_size,
                        self.game_offset_y + py * self.cell_size,
                        self.cell_size,
                        self.cell_size
                    )
                    color_rgb = self._color_to_rgb(self.current_piece.color.value)
                    pygame.draw.rect(self.screen, color_rgb, rect)
                    pygame.draw.rect(self.screen, self._color_to_rgb(Colors.GRID.value), rect, 1)
        
        # Update pixels array for compatibility with wsserver
        frame_data = self.frame
        frame_array = np.array(frame_data).flatten()
        for i in range(min(len(self.pixels), len(frame_array))):
            self.pixels[i].value = int(frame_array[i])  # Ensure regular Python int
        
        # Detect changes from last frame
        if hasattr(self, 'last_frame') and self.last_frame is not None:
            changed_indices = np.where(frame_array != self.last_frame)[0]
            self.changed_pixels.update(changed_indices)
            
            # Always mark at least one pixel as changed to ensure broadcasts
            if len(changed_indices) == 0:
                self.changed_pixels.add(0)  # Mark top-left pixel as changed
        else:
            # First frame, mark all pixels as changed
            self.changed_pixels.update(range(len(frame_array)))
        
        self.last_frame = frame_array
        
        # Draw game border
        border_rect = pygame.Rect(
            self.game_offset_x - 2,
            self.game_offset_y - 2,
            self.game_width * self.cell_size + 4,
            self.game_height * self.cell_size + 4
        )
        pygame.draw.rect(self.screen, Colors.WHITE.value, border_rect, 2)
        
        # Draw board
        for y in range(self.game_height):
            for x in range(self.game_width):
                if self.board[y][x] != Colors.BLACK.value:
                    rect = pygame.Rect(
                        self.game_offset_x + x * self.cell_size,
                        self.game_offset_y + y * self.cell_size,
                        self.cell_size,
                        self.cell_size
                    )
                    pygame.draw.rect(self.screen, self.board[y][x], rect)
                    pygame.draw.rect(self.screen, Colors.GRID.value, rect, 1)
        
        # Draw current piece
        if self.current_piece:
            for px, py in self.current_piece.get_pixels():
                if 0 <= px < self.game_width and 0 <= py < self.game_height:
                    rect = pygame.Rect(
                        self.game_offset_x + px * self.cell_size,
                        self.game_offset_y + py * self.cell_size,
                        self.cell_size,
                        self.cell_size
                    )
                    pygame.draw.rect(self.screen, self.current_piece.color.value, rect)
                    pygame.draw.rect(self.screen, Colors.GRID.value, rect, 1)
        


    class UserInput(pygame.sprite.Sprite):
        """User inputs are 'clicked' pixels, here represented as a 1x1 pixel
        transparent sprite. We can then leverage pygame collision detection to
        determine later what did the player clicked."""

        def __init__(self, x, y, owner=None) -> None:
            super().__init__()
            self.surf = pygame.Surface([1, 1])
            self.surf.set_colorkey(Colors.COLOR_KEY.value)
            self.surf.fill(Colors.COLOR_KEY.value)
            self.rect = self.surf.get_rect()
            self.rect.x = x
            self.rect.y = y
            self.owner = owner

        def update(self):
            super().update(self)

    class TetrominoSprite(pygame.sprite.Sprite):
        """Sprite representation of a tetromino for collision detection."""

        def __init__(self, tetromino, offset_x, offset_y, cell_size) -> None:
            super().__init__()
            self.tetromino = tetromino
            self.offset_x = offset_x
            self.offset_y = offset_y
            self.cell_size = cell_size
            
            # Create surface for the piece
            max_width = max(len(row) for row in tetromino.shape)
            max_height = len(tetromino.shape)
            self.surf = pygame.Surface((max_width * cell_size, max_height * cell_size))
            self.surf.set_colorkey(Colors.COLOR_KEY.value)
            self.surf.fill(Colors.COLOR_KEY.value)
            
            # Draw the piece shape
            for y, row in enumerate(tetromino.shape):
                for x, cell in enumerate(row):
                    if cell:
                        rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
                        pygame.draw.rect(self.surf, tetromino.color.value, rect)
            
            self.rect = self.surf.get_rect()
            self.rect.x = offset_x + tetromino.x * cell_size
            self.rect.y = offset_y + tetromino.y * cell_size

    def _color_to_rgb(self, color_value):
        """Convert single color value to RGB tuple for pygame."""
        color_map = {
            Colors.BLACK.value: (0, 0, 0),
            Colors.WHITE.value: (255, 255, 255),
            Colors.CYAN.value: (0, 255, 255),      # Light blue for L piece
            Colors.BLUE.value: (0, 0, 255),        # Blue for I piece
            Colors.ORANGE.value: (255, 165, 0),     # Orange for J piece
            Colors.YELLOW.value: (255, 255, 0),     # Yellow for Square (O piece)
            Colors.GREEN.value: (0, 255, 0),       # Green for T and Z pieces
            Colors.RED.value: (255, 0, 0),         # Red for S piece
            Colors.PURPLE.value: (255, 192, 203),   # Pink/purple for T piece
            Colors.GRID.value: (50, 50, 50),
        }
        return color_map.get(color_value, (0, 0, 0))

    def get_changed_pixels(self):
        """Get all changed pixel indices and clear the tracking"""
        changed = self.changed_pixels.copy()
        self.changed_pixels.clear()
        return changed

    class Tetromino:
        """Tetromino piece."""
        
        SHAPES = {
            TetrominoType.I: [[1, 1, 1, 1]],
            TetrominoType.O: [[1, 1], [1, 1]],
            TetrominoType.T: [[0, 1, 0], [1, 1, 1]],
            TetrominoType.S: [[0, 1, 1], [1, 1, 0]],
            TetrominoType.Z: [[1, 1, 0], [0, 1, 1]],
            TetrominoType.J: [[1, 0, 0], [1, 1, 1]],
            TetrominoType.L: [[0, 0, 1], [1, 1, 1]],
        }
        
        COLORS = {
            TetrominoType.I: Colors.BLUE,      # I is blue
            TetrominoType.O: Colors.YELLOW,     # Square is yellow
            TetrominoType.T: Colors.PURPLE,    # T is pink/purple
            TetrominoType.S: Colors.RED,        # S is red
            TetrominoType.Z: Colors.GREEN,      # Z is green
            TetrominoType.J: Colors.ORANGE,     # J is orange
            TetrominoType.L: Colors.CYAN,       # L is light blue
        }
        
        def __init__(self, piece_type, x, y):
            self.type = piece_type
            self.shape = [row[:] for row in self.SHAPES[piece_type]]
            self.color = self.COLORS[piece_type]
            self.x = x
            self.y = y
            self.owner = None
        
        def rotate(self):
            """Rotate the piece 90 degrees clockwise."""
            self.shape = [list(row) for row in zip(*self.shape[::-1])]
        
        def get_pixels(self):
            """Get the pixel positions of the piece."""
            pixels = []
            for y, row in enumerate(self.shape):
                for x, cell in enumerate(row):
                    if cell:
                        pixels.append((self.x + x, self.y + y))
            return pixels


def run_random_game(framerate):
    """
    Runs a game where the game is clicked at random intervals on random pixels.

    :param framerate: Set game framerate
    """
    game = Game(framerate=framerate, use_defaults=True)
    t = 0
    game.update()
    while not game.game_over:
        t += 1
        if t % random.randint(5, 15) == 0:
            game.click_at(
                random.randint(0, 63), random.randint(0, 63), "Random" + str(t)
            )
        game.update()
    return game.game_over, game.frame


def main(args):
    """Main function, runs forever one game after another"""
    if args.dummy:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    while True:
        game_over, screenshot = run_random_game(args.framerate)
        if args.screenshot:
            try:
                os.mkdir("screenshots")
            except FileExistsError:
                pass
            ImageOps.mirror(screenshot).save(
                "screenshots/" + str(datetime.now().strftime("%Y%m%d_%H%M%S")) + ".png"
            )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--framerate",
        type=int,
        help="Game framerate (directly affects game speed)",
        default=10,
    )
    parser.add_argument(
        "-d",
        "--dummy",
        help="Use dummy video device (use when no video device is available)",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--screenshot",
        help="Saves final frame screenshot with timestamp",
        action="store_true",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    main(args)