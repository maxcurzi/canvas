from ..invaders import Game, Team
import pygame
import pytest


@pytest.fixture
def default_setup():
    game = Game()
    yield game


@pytest.fixture
def one_alien_above_human():
    game: Game = Game(use_defaults=False)
    alien = Game.Alien(0, 0)
    alien.dx = 0  # Doesn't move
    game.aliens.add(alien)
    human = Game.Human(0, 50)
    human.dx = 0  # Doesn't move
    game.human = human
    yield game


@pytest.fixture
def one_alien_not_above_human(one_alien_above_human):
    game: Game = one_alien_above_human
    for alien in game.aliens:
        alien.rect.x = game.human.rect.x + 20
    yield game


def test_window_size():
    _ = Game(64, 70)
    assert pygame.display.get_window_size() == (64, 70)
    _ = Game(120, 40)
    assert pygame.display.get_window_size() == (120, 40)


def test_event_sprites(default_setup):
    """Tests that all pixel inputs are consumed after every update"""
    game: Game = default_setup
    inputs = len(game.pixel_inputs)
    assert inputs == 0
    game.click_at(10, 11)
    game.click_at(12, 20)
    assert len(game.pixel_inputs) == 2
    game.update()
    assert len(game.pixel_inputs) == 0


def test_no_win(default_setup):
    game: Game = default_setup
    assert game.winner() == None
    game.update()
    assert game.winner() == None


def test_humans_win(default_setup):
    game: Game = default_setup
    for alien in game.aliens:
        alien.health = 0
    game.update()
    assert game.winner() == Team.HUMANS


def test_aliens_win(default_setup):
    game: Game = default_setup
    game.human.health = 0
    game.update()
    assert game.winner() == Team.ALIENS


def test_rocket_hits_alien(one_alien_above_human):
    game: Game = one_alien_above_human
    game.human.enqueue_rocket()
    initial_health = 0
    al = None
    # Get first alien's info
    for alien in game.aliens:
        al = alien
        initial_health = alien.health
        break

    # Run game until rocket hits alien
    successful_hit = False
    for _ in range(64):
        game.update()
        if len(game.human_rockets) == 0:
            assert al is not None and al.health < initial_health
            successful_hit = True
    assert successful_hit


def test_rocket_no_hit(one_alien_not_above_human):
    game: Game = one_alien_not_above_human
    game.human.enqueue_rocket()
    initial_health = 0
    al = None
    # Get first alien's info
    for alien in game.aliens:
        al = alien
        initial_health = alien.health
        break

    # Run game until rocket disappears
    successful_disappearance = False
    for _ in range(64):
        game.update()
        if len(game.human_rockets) == 0:
            assert al is not None and al.health == initial_health
            successful_disappearance = True
    assert successful_disappearance


def test_click_on_human(one_alien_above_human):
    game: Game = one_alien_above_human
    game.human.t = 1
    game.human.shoot_dt = 10
    assert len(game.human.rocket_queue) == 0
    # Click top left
    game.click_at(game.human.rect.x, game.human.rect.y)
    # Click bottom right
    game.click_at(
        game.human.rect.x + game.human.rect.width - 1,
        game.human.rect.y + game.human.rect.height - 1,
    )
    # Click away (shouldn't be counted)
    game.click_at(
        game.human.rect.x + game.human.rect.width,
        game.human.rect.y + game.human.rect.height,
    )
    game.update()
    assert len(game.human.rocket_queue) == 2


def test_click_on_alien(one_alien_above_human):
    game: Game = one_alien_above_human
    al = None
    for alien in game.aliens:
        al = alien
        break
    assert al is not None
    al.t = 1
    al.shoot_dt = 10
    # Click top left
    game.click_at(al.rect.x, al.rect.y)
    # Click bottom right
    game.click_at(
        al.rect.x + al.rect.width - 1,
        al.rect.y + al.rect.height - 1,
    )
    # Click away (shouldn't be counted)
    game.click_at(
        al.rect.x + al.rect.width,
        al.rect.y + al.rect.height,
    )
    game.update()
    assert len(al.rocket_queue) == 2
