import pygame
from enum import Enum, auto
from PIL import Image
import random


class Team(Enum):
    HUMANS = auto()
    ALIENS = auto()
    SHIELDS = auto()


class Game:
    def __init__(self, width: int, height: int, framerate: int = 60) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.player: Game.Human = Game.Human((0, 255, 0), 1, 56)
        self.aliens: pygame.sprite.Group = pygame.sprite.Group()
        self.shields: pygame.sprite.Group = pygame.sprite.Group()
        self.all_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.player_rockets: pygame.sprite.Group = pygame.sprite.Group()
        self.enemies_rockets: pygame.sprite.Group = pygame.sprite.Group()
        self.resolution = (width, height)
        self.clock = pygame.time.Clock()
        self.all_sprites.add(self.player)
        self.framerate = framerate

    def _draw_aliens(self):
        for alien in self.aliens:
            self.screen.blit(alien.surf, alien.rect)
        pass

    def _draw_player(self):
        self.screen.blit(self.player.surf, self.player.rect)

    def _draw_shields(self):
        pass

    def winner(self):
        if len(self.aliens) == 0:
            return Team.HUMANS
        if self.player.health <= 0:
            return Team.ALIENS
        return None

    def draw(self):
        # Draw all sprites
        self.screen.fill((0, 0, 0))
        for entity in self.all_sprites:
            self.screen.blit(entity.surf, entity.rect)
            if isinstance(entity, Game.Alien) or isinstance(entity, Game.Human):
                # Draw health bar
                self.screen.fill((255, 0, 255), entity.hb_rect)

    def _handle_collisions(self):
        for alien in self.aliens:
            if (
                len(
                    pygame.sprite.spritecollide(alien, self.player_rockets, dokill=True)
                )
                > 0
            ):
                alien.health -= 3
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

    def _handle_actions(self):
        pass

    def update(self, clicked_pixels: list | None = None):
        self.all_sprites.update()
        self._handle_collisions()
        self.draw()
        window_width, window_height = pygame.display.get_surface().get_size()
        # pygame.display.set_mode((640, 640))
        pygame.display.flip()
        self.clock.tick(self.framerate)
        pass

    class Alien(pygame.sprite.Sprite):
        # Constructor. Pass in the color of the block,
        # and its x and y position
        def __init__(self, color, x0, y0, owner=None):
            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)
            self.surf = pygame.image.load("games/invaders/alien.png").convert()
            # self.surf.fill(color)
            self.surf.set_colorkey((0, 0, 0))
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
            # self.health_bar.fill((255, 0, 255))
            self.owner = owner
            self.update_rate = 1
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
                if (self.dx > 0 and self.rect.x - self.x0 >= 15) or (
                    self.dx < 0 and self.rect.x - self.x0 <= 0
                ):
                    self.dx = -self.dx
                    self.rect.y += 1
                    self.hb_rect.y += 1

    class Human(pygame.sprite.Sprite):
        # Constructor. Pass in the color of the block,
        # and its x and y position
        def __init__(self, color, x0, y0, owner=None):
            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)
            self.surf = pygame.image.load("games/invaders/human.png").convert()
            # self.surf.fill(color)
            self.surf.set_colorkey((0, 0, 0))
            self.surf.fill((0, 255, 200), special_flags=pygame.BLEND_MULT)

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
            self.owner = owner
            self.update_rate = 3
            self.t = 0
            self.dx = 1

        def update(self):
            super().update(self)
            self.t += 1
            if self.t % self.update_rate == 0:
                # Move
                self.rect.x += self.dx
                self.hb_rect.x += self.dx
                self.hb_rect.width = max(0, self.health)
                if (self.dx > 0 and self.rect.x >= 52) or (
                    self.dx < 0 and self.rect.x <= 0
                ):
                    self.dx = -self.dx

    class Shield(pygame.sprite.Sprite):
        # Constructor. Pass in the color of the block,
        # and its x and y position
        def __init__(self, color, x0, y0, owner=None):
            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)

            # Create an image of the block, and fill it with a color.
            # This could also be an image loaded from the disk.
            self.surf = pygame.Surface([3, 2])
            self.surf.fill((255, 255, 0))
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
        def __init__(self, color, x0, y0, owner=None, friendly=True):
            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)

            # Create an image of the block, and fill it with a color.
            # This could also be an image loaded from the disk.
            self.surf = pygame.Surface([1, 2])
            color = (0, 255, 255) if friendly else (255, 0, 0)
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


def start_game():
    game = Game(64, 64, 600)
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
    aliens = []
    for (x, y) in alien_locations:
        alien = Game.Alien((255, 255, 0), x, y)
        aliens.append(alien)
        game.aliens.add(alien)
        game.all_sprites.add(alien)

    t = 0
    while game.winner() == None:
        game.update()
        t += 1
        if t % random.randint(5, 80) == 0:
            shield = Game.Shield(
                (255, 0, 255), random.randint(1, 60), random.randint(12, 50)
            )
            game.shields.add(shield)
            game.all_sprites.add(shield)
        if t % random.randint(5, 80) == 0:
            rocket = Game.Rocket(
                (255, 0, 255), game.player.rect.x + 5, game.player.rect.y - 1
            )
            game.player_rockets.add(rocket)
            game.all_sprites.add(rocket)

        if t % random.randint(4, 50) == 0:
            al = aliens[random.randint(0, len(alien_locations) - 1)]
            if al.alive():
                rocket = Game.Rocket(
                    (255, 0, 0), al.rect.x + 5, al.rect.y + 5, friendly=False
                )
                game.enemies_rockets.add(rocket)
                game.all_sprites.add(rocket)
        im = Image.fromarray(pygame.surfarray.array3d(game.screen)).rotate(-90)
        im.save("Screenshot.png")
    print("Winner: " + str(game.winner()))


if __name__ == "__main__":
    while True:
        start_game()
