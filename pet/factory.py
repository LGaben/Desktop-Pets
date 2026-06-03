# -*- coding: utf-8 -*-
"""Factory for constructing pet instances by type identifier."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pet.base_pet import BasePet
from pet.full_pet import FullPet
from pet.simple_pet import SimplePet

if TYPE_CHECKING:
    from utils.database import PetDatabase

_SIMPLE_PET_TYPES: frozenset[str] = frozenset({
    # original PNG-based
    "fox", "panda", "cockatiel",
    # GIF-converted batch
    "dog", "turtle", "totoro",
    "chicken", "clippy", "crab", "deno", "horse",
    "mod", "monkey", "morph", "rat", "rocky",
    "rubber_duck", "skeleton", "snail", "snake", "zappy",
})


class PetFactory:
    """Creates the correct :class:`BasePet` subclass for a given type.

    Adding support for a new pet type only requires extending
    :data:`_SIMPLE_PET_TYPES` or adding a new branch here — existing
    classes are never modified (Open/Closed Principle).
    """

    @staticmethod
    def create(
        pet_type: str,
        name: str | None = None,
        db: PetDatabase | None = None,
    ) -> BasePet:
        """Instantiate and return the appropriate pet subclass.

        Args:
            pet_type: Identifier string (``"fox"``, ``"panda"``,
                ``"cockatiel"``).
            name: Display-name override; each type has a sensible default.
            db: Database to inject into :class:`FullPet`; ignored for
                :class:`SimplePet`.

        Returns:
            A fully initialised :class:`BasePet` subclass.
        """
        if pet_type in _SIMPLE_PET_TYPES:
            return SimplePet(pet_type, name)
        return FullPet(pet_type, name or "Питомец", db)

    @staticmethod
    def available_types() -> list[str]:
        """Return all registered pet-type identifiers."""
        return [
            "fox", "panda", "cockatiel",
            "dog", "turtle", "totoro",
            "chicken", "clippy", "crab", "deno", "horse",
            "mod", "monkey", "morph", "rat", "rocky",
            "rubber_duck", "skeleton", "snail", "snake", "zappy",
        ]
