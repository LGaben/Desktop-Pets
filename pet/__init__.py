# -*- coding: utf-8 -*-
"""Desktop Pet – pet package.

Public API
----------
- :class:`~pet.base_pet.BasePet` – abstract base for all pet types
- :class:`~pet.full_pet.FullPet` – stat-based pet with AI
- :class:`~pet.simple_pet.SimplePet` – lightweight ball-chasing pet
- :class:`~pet.factory.PetFactory` – creates the correct subclass by type
- :class:`~pet.state.PetState` – behavioural state enum for FullPet
- :mod:`~pet.protocols` – runtime-checkable capability protocols
"""
from pet.base_pet import BasePet
from pet.factory import PetFactory
from pet.full_pet import FullPet
from pet.protocols import BallChaser, HasStats, MouseFollower, PetStorage
from pet.simple_pet import SimplePet
from pet.state import PetState

__all__ = [
    "BasePet",
    "BallChaser",
    "FullPet",
    "HasStats",
    "MouseFollower",
    "PetFactory",
    "PetState",
    "PetStorage",
    "SimplePet",
]
