"""Fox character choices and probabilities, independent of Qt and translation."""
from dataclasses import dataclass
import random


@dataclass(frozen=True)
class FoxPersonality:
    walk_chance: float
    rest_chance: float
    cursor_chance: float
    ball_interest: float
    rest_ticks: tuple[int, int]


FOX_PERSONALITIES = {
    'active': FoxPersonality(.78, .03, .55, 1.0, (3, 6)),
    'calm': FoxPersonality(.12, .55, .08, .35, (14, 24)),
    'curious': FoxPersonality(.38, .12, .90, .75, (6, 12)),
}


def choose_personality(value=None, rng=random):
    return value if isinstance(value, str) and value in FOX_PERSONALITIES else rng.choice(tuple(FOX_PERSONALITIES))


def idle_action(personality_id, roll):
    profile = FOX_PERSONALITIES[personality_id]
    if roll < profile.walk_chance:
        return 'walk'
    if roll < profile.walk_chance + profile.rest_chance:
        return 'lie'
    return 'idle'
