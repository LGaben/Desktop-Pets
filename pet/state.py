# -*- coding: utf-8 -*-
"""Behavioral state definitions for full-featured pets."""
from enum import Enum


class PetState(Enum):
    """All possible behavioral states for a stat-based pet."""

    IDLE = "idle"
    WALKING = "walk"
    SLEEPING = "sleep"
    EATING = "eat"
    PLAYING = "play"
    SITTING = "sit"
