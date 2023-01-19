#!/usr/bin/env python
""" Simple space invaders clone, to be used as a backend game for Canvas.
TODO: Remove hardcoded values
TODO: Output color/color palette along the image, to reproduce within Canvas.
"""
import pygame
from enum import Enum, auto
from PIL import Image, ImageOps
import random
from collections import deque
from itertools import product
import os
import argparse
from datetime import datetime

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


class Team(Enum):
    HUMANS = auto()
    ALIENS = auto()
    SHIELDS = auto()


class Colors(Enum):
    COLOR_KEY = (0, 0, 0)  # Transparency color key
    BLACK = (0, 0, 0)
    HUMAN = (0, 255, 200)
    ALIEN = (255, 255, 255)
    SHIELD = (255, 255, 0)
    ENEMY_ROCKET = (255, 0, 0)
    FRIENDLY_ROCKET = (0, 255, 255)
    HEALTH_BAR = (255, 0, 255)


class Game:
    def __init__(
        self, width: int = 64, height: int = 64, framerate: int = 60, use_defaults=True
    ) -> None:
        pygame.init()

        self.resolution = (width, height)
        self.screen = pygame.display.set_mode((width, height))
        self.framerate = framerate
        self.clock = pygame.time.Clock()

        self.human = Game.Human(1, height - 8)
        self.aliens = pygame.sprite.Group()
        self.shields = pygame.sprite.Group()
        self.human_rockets = pygame.sprite.Group()
        self.enemies_rockets = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()

        self.all_sprites.add(self.human)

        self.pixel_inputs = pygame.sprite.Group()

        if use_defaults:
            self.defaults()

    def click_at(self, x, y, owner=None):
        """User inputs are clicks to the grid pixels, we add these inputs to a
        queue for later processing, and we store an identifier of who clicked
        it, for later retrieval/identification of who caused a certain effect."""
        click_sprite = Game.UserInput(x, y, owner)
        self.pixel_inputs.add(click_sprite)

    @property
    def owners_map(self):
        """Each pixel can have an owner, for example when a player clicks on the
        spaceship to shoot a rocket, the pixels composing the rocket will
        'belong' to that user."""
        om = {}
        for entity in [*self.human_rockets, *self.enemies_rockets, *self.shields]:
            x, y, w, h = entity.rect
            for dx, dy in product(range(w), range(h)):
                om[(x + dx, y + dy)] = entity.owner
        return om

    @property
    def frame(self):
        return Image.fromarray(pygame.surfarray.array3d(self.screen)).rotate(-90)

    def defaults(self):
        alien_locations = [
            (1, 2),
            (13, 2),
            (25, 2),
            (37, 2),
            (1, 13),
            (13, 13),
            (25, 13),
            (37, 13),
        ]

        for (x, y) in alien_locations:
            alien = Game.Alien(x, y)
            self.aliens.add(alien)
            self.all_sprites.add(alien)

    def winner(self):
        if len(self.aliens) == 0:
            return Team.HUMANS
        if self.human.health <= 0:
            return Team.ALIENS
        return None

    def draw(self):
        # Draw all sprites
        self.screen.fill(Colors.BLACK.value)
        self._purge_sprites_off_screen()
        for entity in self.all_sprites:
            if isinstance(entity, Game.Alien) or isinstance(entity, Game.Human):
                # Draw health bar
                self.screen.fill(Colors.HEALTH_BAR.value, entity.health_bar.rect)
            if isinstance(entity, Game.Alien):
                # Draw rocket bar
                self.screen.fill(Colors.ENEMY_ROCKET.value, entity.rocket_bar.rect)
            if isinstance(entity, Game.Human):
                # Draw rocket bar
                self.screen.fill(Colors.FRIENDLY_ROCKET.value, entity.rocket_bar.rect)
            # Draw actual sprite
            self.screen.blit(entity.surf, entity.rect)

    def _purge_sprites_off_screen(self):
        for entity in [*self.human_rockets, *self.enemies_rockets, *self.shields]:
            x, y, w, h = entity.rect
            if not (0 <= x < self.resolution[0] and 0 <= y < self.resolution[1]):
                # Remove entity from the groups (the removal silently continues if the entity doesn't exist)
                self.human_rockets.remove(entity)
                self.enemies_rockets.remove(entity)
                self.shields.remove(entity)

    def _handle_pixel_inputs(self):
        # Check if user clicked on Alien
        for user_input in self.pixel_inputs:
            alien_clicked = pygame.sprite.spritecollide(
                user_input, self.aliens, dokill=False
            )
            if len(alien_clicked) > 0:
                alien_clicked[0].enqueue_rocket(user_input.owner)
                self.pixel_inputs.remove(user_input)
                print(f"Clicked on Alien {user_input.rect.x},{user_input.rect.y}")

        # Check if user clicked on Human
        human_clicked_by = pygame.sprite.spritecollide(
            self.human, self.pixel_inputs, dokill=False
        )

        for user_input in human_clicked_by:
            print(f"Clicked on Human {user_input.rect.x},{user_input.rect.y}")
            self.human.enqueue_rocket(user_input.owner)
            self.pixel_inputs.remove(user_input)

        # Check if user clicked on Shield, ignore it. But if not, place shield
        for user_input in self.pixel_inputs:
            shield_clicked_by = pygame.sprite.spritecollide(
                user_input, self.shields, dokill=False
            )
            if len(shield_clicked_by) > 0:
                self.pixel_inputs.remove(user_input)

        for user_input in self.pixel_inputs:
            print(f"Placed a Shield {user_input.rect.x},{user_input.rect.y}")
            shield = Game.Shield(
                user_input.rect.x, user_input.rect.y, owner=user_input.owner
            )
            self.shields.add(shield)
            self.all_sprites.add(shield)
        self.pixel_inputs = pygame.sprite.Group()

    def _handle_collisions(self):
        for alien in self.aliens:
            if (
                len(pygame.sprite.spritecollide(alien, self.human_rockets, dokill=True))
                > 0
            ):
                alien.health -= 2
        for alien in self.aliens:
            collided = pygame.sprite.spritecollide(alien, self.shields, dokill=True)
            if len(collided) > 0:
                alien.health -= 0
        for shield in self.shields:
            if (
                len(
                    pygame.sprite.spritecollide(shield, self.human_rockets, dokill=True)
                )
                > 0
            ) or (
                len(
                    pygame.sprite.spritecollide(
                        shield, self.enemies_rockets, dokill=True
                    )
                )
                > 0
            ):
                shield.health -= 1
        if (
            len(
                pygame.sprite.spritecollide(
                    self.human, self.enemies_rockets, dokill=True
                )
            )
            > 0
        ):
            self.human.health -= 1
        if len(pygame.sprite.spritecollide(self.human, self.aliens, dokill=True)) > 0:
            self.human.health = 0

    def _shoot_rockets(self):
        if self.human.t % self.human.shoot_dt == 0 and len(self.human.rocket_queue) > 0:
            owner = self.human.rocket_queue.popleft()
            rocket = Game.Rocket(
                self.human.rect.x + 5, self.human.rect.y - 1, owner=owner
            )
            self.human_rockets.add(rocket)
            self.all_sprites.add(rocket)

        for alien in self.aliens:
            if (
                alien.alive()
                and (alien.t % alien.shoot_dt == 0)
                and len(alien.rocket_queue) > 0
            ):
                owner = alien.rocket_queue.popleft()

                rocket = Game.Rocket(
                    alien.rect.x + 5, alien.rect.y + 5, friendly=False, owner=owner
                )
                self.enemies_rockets.add(rocket)
                self.all_sprites.add(rocket)

    def update(self):
        self._handle_pixel_inputs()
        self.all_sprites.update()
        self._handle_collisions()
        self._shoot_rockets()
        self.draw()
        pygame.display.flip()
        self.clock.tick(self.framerate)

    class MeterBar:
        THICKNESS = 1

        def __init__(self, len) -> None:
            self.meter_bar = pygame.Surface((len, self.THICKNESS))
            self.rect = self.meter_bar.get_rect()

        @property
        def x(self):
            return self.rect.x

        @x.setter
        def x(self, value):
            self.rect.x = value

        @property
        def y(self):
            return self.rect.y

        @y.setter
        def y(self, value):
            self.rect.y = value

        @property
        def width(self):
            return self.rect.width

        @width.setter
        def width(self, value):
            self.rect.width = max(0, value)

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

    class Alien(pygame.sprite.Sprite):
        """Space invader alien. It can shoot rockets and has a healthbar
        indicator and a rocket indicator.
        """

        def __init__(self, x0, y0, owner=None):
            pygame.sprite.Sprite.__init__(self)
            self.surf = pygame.image.load("alien.png").convert()
            self.surf.set_colorkey(Colors.COLOR_KEY.value)
            self.rect = self.surf.get_rect()
            self.x0 = x0
            self.y0 = y0
            self.rect.x = x0
            self.rect.y = y0

            self.health = 7
            self.health_bar = Game.MeterBar(self.health)
            self.health_bar.x = x0 + 2
            self.health_bar.y = y0 - 2

            self.rocket_queue = deque()
            self.rocket_bar = Game.MeterBar(len(self.rocket_queue))
            self.rocket_bar.x = x0 + 3
            self.rocket_bar.y = y0 + 3

            self.owner = owner
            self.update_rate = 1
            self.shoot_dt = 10
            self.t = 0
            self.dx = 1
            self.xmargin = 15  # TODO

        def update(self):
            super().update(self)
            if self.health <= 0:
                self.kill()
            self.t += 1
            if self.t % self.update_rate == 0:
                # Move
                self.rect.x += self.dx
                self.health_bar.x += self.dx
                self.health_bar.width = self.health
                self.rocket_bar.x += self.dx
                # Rocket bar intention is to span between the alien's two eyes.
                # When drawn behind the alien it results in one or two 'red' (or
                # whatever color the rocket bar is) eyes
                self.rocket_bar.width = min(len(self.rocket_queue), 5)
                if (self.dx > 0 and self.rect.x - self.x0 >= self.xmargin) or (
                    self.dx < 0 and self.rect.x - self.x0 <= 0
                ):
                    self.dx = -self.dx
                    self.rect.y += 1
                    self.health_bar.y += 1
                    self.rocket_bar.y += 1

        def enqueue_rocket(self, owner=None):
            self.rocket_queue.append(owner)

    class Human(pygame.sprite.Sprite):
        def __init__(self, x0, y0, owner=None):
            pygame.sprite.Sprite.__init__(self)
            self.surf = pygame.image.load("human.png").convert()
            self.surf.set_colorkey(Colors.COLOR_KEY.value)
            self.surf.fill(Colors.HUMAN.value, special_flags=pygame.BLEND_MULT)

            self.rect = self.surf.get_rect()
            self.rect.x = x0
            self.rect.y = y0

            self.health = 11
            self.health_bar = Game.MeterBar(self.health)
            self.health_bar.x = x0
            self.health_bar.y = y0 + 6

            self.rocket_queue = deque()
            self.rocket_bar = Game.MeterBar(len(self.rocket_queue))
            self.rocket_bar.x = x0 + 2
            self.rocket_bar.y = y0 + 3

            self.owner = owner
            self.move_dt = 3
            self.shoot_dt = 7
            self.t = 0
            self.dx = 1
            self.xmargin = 52

        def enqueue_rocket(self, owner=None):
            self.rocket_queue.append(owner)

        def update(self):
            super().update(self)
            self.t += 1
            if self.t % self.move_dt == 0:
                # Move
                self.rect.x += self.dx
                self.health_bar.x += self.dx
                self.health_bar.width = self.health
                self.rocket_bar.x += self.dx
                # Rocket bar intention is to span within the player ship's empty gap.
                self.rocket_bar.width = min(len(self.rocket_queue), 7)
                if (self.dx > 0 and self.rect.x >= self.xmargin) or (
                    self.dx < 0 and self.rect.x <= 0
                ):
                    self.dx = -self.dx

    class Shield(pygame.sprite.Sprite):
        SHAPE = [3, 2]

        def __init__(self, x0, y0, owner=None):
            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)

            self.surf = pygame.Surface(self.SHAPE)
            self.surf.fill(Colors.SHIELD.value)

            self.rect = self.surf.get_rect()
            self.rect.x = x0 - 1
            self.rect.y = y0
            self.health = 1
            self.owner = owner

        def update(self):
            super().update(self)
            if self.health <= 0:
                self.kill()

    class Rocket(pygame.sprite.Sprite):
        SHAPE = [1, 2]

        def __init__(self, x0, y0, owner=None, friendly=True):
            pygame.sprite.Sprite.__init__(self)
            self.surf = pygame.Surface(self.SHAPE)
            color = (
                Colors.FRIENDLY_ROCKET.value if friendly else Colors.ENEMY_ROCKET.value
            )
            self.surf.fill(color)
            self.friendly = friendly

            self.rect = self.surf.get_rect()
            self.rect.x = x0
            self.rect.y = y0
            self.health = 1
            self.owner = owner

        def update(self):
            super().update(self)
            self.rect.y = self.rect.y - 1 if self.friendly else self.rect.y + 1


def run_random_game(framerate):
    """
    Runs a game where the game is clicked at random  interval on random pixels.

    :param framerate: Set game framerate
    """
    game = Game(framerate=framerate, use_defaults=True)
    t = 0
    game.update()
    while game.winner() == None:
        print(game.owners_map)
        t += 1
        if t % random.randint(5, 8) == 0:
            game.click_at(
                random.randint(0, 63), random.randint(0, 63), "Random" + str(t)
            )
        game.update()
    return game.winner(), game.frame


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--framerate",
        type=int,
        help="Game framerate (directly affects game speed)",
        default=60,
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
    if args.dummy:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    while True:
        winner, screenshot = run_random_game(args.framerate)
        print("Winner: " + str(winner))
        if args.screenshot:
            try:
                os.mkdir("screenshots")
            except FileExistsError:
                pass
            ImageOps.mirror(screenshot).save(
                "screenshots/" + str(datetime.now().strftime("%Y%m%d_%H%M%S")) + ".png"
            )
