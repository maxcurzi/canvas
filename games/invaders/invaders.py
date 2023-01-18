import pygame
from enum import Enum, auto
from PIL import Image, ImageOps
import random
from collections import deque


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

        self.player: Game.Human = Game.Human(1, 56)
        self.alienslist = []
        self.aliens: pygame.sprite.Group = pygame.sprite.Group()
        self.shields: pygame.sprite.Group = pygame.sprite.Group()
        self.player_rockets: pygame.sprite.Group = pygame.sprite.Group()
        self.enemies_rockets: pygame.sprite.Group = pygame.sprite.Group()
        self.all_sprites: pygame.sprite.Group = pygame.sprite.Group()

        self.all_sprites.add(self.player)
        if use_defaults:
            self.defaults()

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
            self.alienslist.append(alien)
            self.aliens.add(alien)
            self.all_sprites.add(alien)

    def winner(self):
        if len(self.aliens) == 0:
            return Team.HUMANS
        if self.player.health <= 0:
            return Team.ALIENS
        return None

    def draw(self):
        # Draw all sprites
        self.screen.fill(Colors.BLACK.value)
        for entity in self.all_sprites:
            if isinstance(entity, Game.Alien) or isinstance(entity, Game.Human):
                # Draw health bar
                self.screen.fill(Colors.HEALTH_BAR.value, entity.hb_rect)
            if isinstance(entity, Game.Alien):
                # Draw rocket bar
                self.screen.fill(Colors.ENEMY_ROCKET.value, entity.rb_rect)
            if isinstance(entity, Game.Human):
                # Draw rocket bar
                self.screen.fill(Colors.FRIENDLY_ROCKET.value, entity.rb_rect)
            # Draw actual sprite
            self.screen.blit(entity.surf, entity.rect)

    def _handle_collisions(self):
        for alien in self.aliens:
            if (
                len(
                    pygame.sprite.spritecollide(alien, self.player_rockets, dokill=True)
                )
                > 0
            ):
                alien.health -= 2
        for alien in self.aliens:
            if len(pygame.sprite.spritecollide(alien, self.shields, dokill=True)) > 0:
                alien.health -= 1
        for shield in self.shields:
            if (
                len(
                    pygame.sprite.spritecollide(
                        shield, self.player_rockets, dokill=True
                    )
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
                    self.player, self.enemies_rockets, dokill=True
                )
            )
            > 0
        ):
            self.player.health -= 1
        if len(pygame.sprite.spritecollide(self.player, self.aliens, dokill=True)) > 0:
            self.player.health = 0

    def _shoot_rockets(self):
        if (
            self.player.t % self.player.shoot_rate == 0
            and len(self.player.rocket_queue) > 0
        ):
            owner = self.player.rocket_queue.popleft()
            rocket = Game.Rocket(self.player.rect.x + 5, self.player.rect.y - 1)
            self.player_rockets.add(rocket)
            self.all_sprites.add(rocket)

        for alien in self.alienslist:
            if (
                alien.alive()
                and (alien.t % alien.shoot_rate == 0)
                and len(alien.rocket_queue) > 0
            ):
                owner = alien.rocket_queue.popleft()

                rocket = Game.Rocket(alien.rect.x + 5, alien.rect.y + 5, friendly=False)
                self.enemies_rockets.add(rocket)
                self.all_sprites.add(rocket)

    def update(self, clicked_pixels: list | None = None):
        self.all_sprites.update()
        self._handle_collisions()
        self._shoot_rockets()
        self.draw()
        window_width, window_height = pygame.display.get_surface().get_size()
        pygame.display.flip()
        self.clock.tick(self.framerate)
        return Image.fromarray(pygame.surfarray.array3d(self.screen)).rotate(-90)

    class Alien(pygame.sprite.Sprite):
        # Constructor. Pass in the color of the block,
        # and its x and y position
        def __init__(self, x0, y0, owner=None):
            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)
            self.surf = pygame.image.load("games/invaders/alien.png").convert()
            self.surf.set_colorkey(Colors.COLOR_KEY.value)
            self.rect = self.surf.get_rect()
            self.x0 = x0
            self.y0 = y0
            self.rect.x = x0
            self.rect.y = y0

            self.health = 7
            self.health_bar = pygame.Surface((self.health, 1))
            self.hb_rect = self.health_bar.get_rect()
            self.hb_rect.x = x0 + 2
            self.hb_rect.y = y0 - 2

            self.rocket_queue = deque()
            self.rocket_bar = pygame.Surface((len(self.rocket_queue), 1))
            self.rb_rect = self.health_bar.get_rect()
            self.rb_rect.x = x0 + 3
            self.rb_rect.y = y0 + 3

            self.owner = owner
            self.update_rate = 1
            self.shoot_rate = 10
            self.t = 0
            self.dx = 1

        def update(self):
            super().update(self)
            if self.health <= 0:
                self.kill()
            self.t += 1
            if self.t % self.update_rate == 0:
                # Move
                self.rect.x += self.dx
                self.hb_rect.x += self.dx
                self.hb_rect.width = max(0, self.health)
                self.rb_rect.x += self.dx
                self.rb_rect.width = min(max(0, len(self.rocket_queue)), 5)
                if (self.dx > 0 and self.rect.x - self.x0 >= 15) or (
                    self.dx < 0 and self.rect.x - self.x0 <= 0
                ):
                    self.dx = -self.dx
                    self.rect.y += 1
                    self.hb_rect.y += 1
                    self.rb_rect.y += 1

        def enqueue_rocket(self, owner=None):
            self.rocket_queue.append(owner)

    class Human(pygame.sprite.Sprite):
        # Constructor. Pass in the color of the block,
        # and its x and y position
        def __init__(self, x0, y0, owner=None):
            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)
            self.surf = pygame.image.load("games/invaders/human.png").convert()
            # self.surf.fill(color)
            self.surf.set_colorkey(Colors.COLOR_KEY.value)
            self.surf.fill(Colors.HUMAN.value, special_flags=pygame.BLEND_MULT)

            # Fetch the rectangle object that has the dimensions of the image
            # Update the position of this object by setting the values of rect.x and rect.y
            self.rect = self.surf.get_rect()
            self.rect.x = x0
            self.rect.y = y0

            self.health = 11
            self.health_bar = pygame.Surface((self.health, 1))
            self.hb_rect = self.health_bar.get_rect()
            self.hb_rect.x = x0
            self.hb_rect.y = y0 + 6

            self.rocket_queue = deque()
            self.rocket_bar = pygame.Surface((len(self.rocket_queue), 1))
            self.rb_rect = self.rocket_bar.get_rect()
            self.rb_rect.x = x0 + 2
            self.rb_rect.y = y0 + 3

            self.owner = owner
            self.move_rate = 3
            self.shoot_rate = 7
            self.t = 0
            self.dx = 1

        def enqueue_rocket(self, owner=None):
            self.rocket_queue.append(owner)

        def update(self):
            super().update(self)
            self.t += 1
            if self.t % self.move_rate == 0:
                # Move
                self.rect.x += self.dx
                self.hb_rect.x += self.dx
                self.hb_rect.width = max(0, self.health)
                self.rb_rect.x += self.dx
                self.rb_rect.width = min(max(0, len(self.rocket_queue)), 7)
                if (self.dx > 0 and self.rect.x >= 52) or (
                    self.dx < 0 and self.rect.x <= 0
                ):
                    self.dx = -self.dx

    class Shield(pygame.sprite.Sprite):
        # Constructor. Pass in the color of the block,
        # and its x and y position
        def __init__(self, x0, y0, owner=None):
            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)

            # Create an image of the block, and fill it with a color.
            # This could also be an image loaded from the disk.
            self.surf = pygame.Surface([3, 2])
            self.surf.fill(Colors.SHIELD.value)
            # self.surf.fill(color)

            # Fetch the rectangle object that has the dimensions of the image
            # Update the position of this object by setting the values of rect.x and rect.y
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
        # Constructor. Pass in the color of the block,
        # and its x and y position
        def __init__(self, x0, y0, owner=None, friendly=True):
            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)

            # Create an image of the block, and fill it with a color.
            # This could also be an image loaded from the disk.
            self.surf = pygame.Surface([1, 2])
            color = (
                Colors.FRIENDLY_ROCKET.value if friendly else Colors.ENEMY_ROCKET.value
            )
            self.surf.fill(color)
            self.friendly = friendly

            # Fetch the rectangle object that has the dimensions of the image
            # Update the position of this object by setting the values of rect.x and rect.y
            self.rect = self.surf.get_rect()
            self.rect.x = x0
            self.rect.y = y0
            self.health = 1
            self.owner = owner

        def update(self):
            super().update(self)
            self.rect.y = self.rect.y - 1 if self.friendly else self.rect.y + 1


def random_game():
    game = Game(framerate=30, use_defaults=True)
    t = 0
    im = game.update()
    while game.winner() == None:
        t += 1
        if t % random.randint(5, 80) == 0:
            shield = Game.Shield(random.randint(1, 60), random.randint(12, 50))
            game.shields.add(shield)
            game.all_sprites.add(shield)
        if t % random.randint(5, 80) == 0:
            game.player.enqueue_rocket()

        if t % random.randint(4, 50) == 0:
            al = game.alienslist[random.randint(0, len(game.alienslist) - 1)]
            if al.alive():
                al.enqueue_rocket()
        im = game.update()
    ImageOps.mirror(im).save("Screenshot.png")
    print("Winner: " + str(game.winner()))


if __name__ == "__main__":
    while True:
        random_game()
