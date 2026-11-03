"""Geometry and elapsed time behavior, including negative screen origins."""
import math

import pytest
from PyQt6.QtCore import QPoint, QRect, QSize

from pet.ball import Ball
from pet.full_pet import FullPet
from pet.simple_pet import SimplePet
from utils.geometry import clamp_position, nearest_rect


def test_negative_screen_clamp_and_removed_monitor():
    left = QRect(-1920, -200, 1920, 1080)
    primary = QRect(0, 0, 1920, 1080)
    point = QPoint(-500, 300)
    assert nearest_rect(point, [primary, left]) == left
    assert nearest_rect(point, [primary]) == primary
    assert clamp_position(QPoint(-1, 1000), QSize(48, 48), left) == QPoint(-48, 832)
    assert clamp_position(point, QSize(48, 48), primary) == QPoint(0, 300)
    assert clamp_position(QPoint(100, 100), QSize(500, 500), QRect(-10, -20, 20, 20)) == QPoint(-10, -20)


@pytest.mark.parametrize("diagonal", [False, True])
def test_simple_movement_independent_of_tick_rate(qt_app, monkeypatch, diagonal):
    import pet.simple_pet as module
    monkeypatch.setattr(module, "movement_bounds", lambda *_: QRect(-2000, -2000, 5000, 5000))
    positions = []
    for step in (0.016, 0.033, 0.05):
        pet = SimplePet("fox")
        pet.position = QPoint(0, 0)
        pet._walk_target = QPoint(1500, 1500 if diagonal else 0)
        pet._walk_timer = 10000
        pet.change_state("walk")
        remaining = 1.0
        while remaining > 1e-9:
            dt = min(step, remaining)
            pet.get_next_position(dt)
            remaining -= dt
        positions.append(pet.position)
    for position in positions:
        assert abs(math.hypot(position.x(), position.y()) - 2 / 0.033) < 1.5
    assert max(p.x() for p in positions) - min(p.x() for p in positions) <= 1


def test_full_movement_independent_of_tick_rate(qt_app, db, monkeypatch):
    import pet.full_pet as module
    monkeypatch.setattr(module, "movement_bounds", lambda *_: QRect(-2000, -2000, 5000, 5000))
    positions = []
    for step in (0.016, 0.033, 0.05):
        pet = FullPet(db=db)
        pet.position = QPoint(-500, 0)
        pet.start_walking()
        pet.velocity = QPoint(2, 0)
        pet.walk_distance = 10000
        remaining = 1.0
        while remaining > 1e-9:
            dt = min(step, remaining)
            pet.get_next_position(dt)
            remaining -= dt
        positions.append(pet.position.x())
        pet.cleanup()
    assert max(positions) - min(positions) <= 1
    assert abs(positions[0] - (-500 + 2 / 0.033)) <= 1


def test_ball_physics_uses_elapsed_time_and_bounds(qt_app):
    positions = []
    for step in (0.008, 0.016, 0.05):
        ball = Ball()
        ball.throw(-900, -800, -875, -825)
        remaining = 0.5
        while remaining > 1e-9:
            dt = min(step, remaining)
            ball.update(dt, QRect(-2000, -2000, 4000, 4000))
            remaining -= dt
        positions.append((ball.x, ball.y))
    assert max(x for x, _ in positions) - min(x for x, _ in positions) < 0.01
    assert max(y for _, y in positions) - min(y for _, y in positions) < 0.01
    ball.throw(-100, -100, 10000, 10000)
    ball.update(10, QRect(-500, -500, 500, 500))
    assert -495 <= ball.x <= -6
    assert -495 <= ball.y <= -6


def test_pickup_at_bottom_right_and_follow_toggle(qt_app, monkeypatch):
    import pet.simple_pet as module
    rect = QRect(-500, -300, 500, 300)
    monkeypatch.setattr(module, "available_rect", lambda *_: rect)
    monkeypatch.setattr(module, "movement_bounds", lambda *_: QRect(-500, -300, 453, 253))
    pet = SimplePet("fox")
    pet.window_size = QSize(48, 48)
    pet.position = QPoint(-80, -80)
    pet.chase(-6, -6)
    for _ in range(100):
        pet.get_next_position()
        if pet.carrying_ball:
            break
    assert pet.carrying_ball
    assert not pet.is_chasing
    pet.set_follow_mouse(True)
    assert pet.state == "with_ball"
    for _ in range(180):
        pet.get_next_position()
    assert not pet.carrying_ball
    pet.chase(-50, -50)
    pet.sleep()
    pet.chase(-100, -100)
    assert not pet.is_chasing
    assert pet.state == "lie"


@pytest.mark.parametrize("model", [SimplePet, FullPet])
def test_animation_elapsed_time_preserves_fractional_frames(qt_app, db, model):
    pets = [model("fox") if model is SimplePet else model("fox", db=db) for _ in range(3)]
    for pet, step in zip(pets, (0.016, 0.033, 0.05)):
        remaining = 1.0
        while remaining > 1e-9:
            dt = min(step, remaining)
            pet.get_current_sprite(dt)
            remaining -= dt
    assert len({pet.current_frame for pet in pets}) == 1
    assert max(pet.frame_counter for pet in pets) - min(pet.frame_counter for pet in pets) < 1e-8
    for pet in pets:
        pet.cleanup()
