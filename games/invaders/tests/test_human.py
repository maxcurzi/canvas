from ..invaders import Game
import pygame
import pytest

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"


@pytest.fixture
def setup_human():
    x = 10
    y = 20
    human = Game.Human(x0=x, y0=y, owner="test_owner")
    yield human


@pytest.fixture
def setup_group(setup_human):
    human = setup_human
    group = pygame.sprite.Group()
    group.add(human)
    yield group


def test_human_alive_in_group(setup_human):
    human = setup_human
    assert not setup_human.alive()  # Not in a group, should be dead
    group = pygame.sprite.Group()
    group.add(human)
    assert human.alive()


@pytest.mark.depends(on=["test_human_alive_in_group"])
def test_human_dead_after_kill(setup_group):
    group = setup_group
    assert len(group) > 0, "Wrong setup"
    for human in group:
        assert human.alive()
        human.kill()
        assert not human.alive()


def test_enqueue_rockets(setup_human):
    human: Game.Human = setup_human
    assert len(human.rocket_queue) == 0, "Wrong setup"
    human.enqueue_rocket("Test owner")
    rocket = human.rocket_queue.pop()
    assert rocket == "Test owner"
