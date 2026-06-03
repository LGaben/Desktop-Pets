"""Unit tests for pet classes and factory."""
from __future__ import annotations

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def qt_app():
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    return app


class TestPetFactory:
    def test_fox_returns_simple_pet(self, qt_app):
        from pet.factory import PetFactory
        from pet.simple_pet import SimplePet

        pet = PetFactory.create("fox")
        assert isinstance(pet, SimplePet)

    def test_panda_returns_simple_pet(self, qt_app):
        from pet.factory import PetFactory
        from pet.simple_pet import SimplePet

        pet = PetFactory.create("panda")
        assert isinstance(pet, SimplePet)

    def test_unknown_type_returns_full_pet(self, qt_app):
        from pet.factory import PetFactory
        from pet.full_pet import FullPet

        pet = PetFactory.create("unknown_type", "Test")
        assert isinstance(pet, FullPet)

    def test_available_types_no_cat(self, qt_app):
        from pet.factory import PetFactory

        types = PetFactory.available_types()
        assert "cat" not in types
        assert "fox" in types


class TestSimplePet:
    def test_default_name(self, qt_app):
        from pet.simple_pet import SimplePet

        pet = SimplePet("fox")
        assert pet.name == "Рыжик"

    def test_custom_name(self, qt_app):
        from pet.simple_pet import SimplePet

        pet = SimplePet("fox", "Buddy")
        assert pet.name == "Buddy"

    def test_protocols(self, qt_app):
        from pet.simple_pet import SimplePet
        from pet.protocols import BallChaser, MouseFollower

        pet = SimplePet("fox")
        assert isinstance(pet, BallChaser)
        assert isinstance(pet, MouseFollower)

    def test_no_has_stats(self, qt_app):
        from pet.simple_pet import SimplePet
        from pet.protocols import HasStats

        pet = SimplePet("fox")
        assert not isinstance(pet, HasStats)

    def test_chase_sets_state(self, qt_app):
        from pet.simple_pet import SimplePet

        pet = SimplePet("fox")
        pet.chase(200, 300)
        assert pet.is_chasing
        assert pet.state == "run"

    def test_sleep_wake(self, qt_app):
        from pet.simple_pet import SimplePet

        pet = SimplePet("fox")
        pet.sleep()
        assert pet.state == "lie"
        assert pet._user_sleep
        pet.wake()
        assert pet.state == "idle"
        assert not pet._user_sleep


class TestFullPet:
    def test_has_stats_protocol(self, qt_app):
        from pet.full_pet import FullPet
        from pet.protocols import HasStats
        from utils.database import PetDatabase

        db = PetDatabase()
        pet = FullPet("fox", "Test", db)
        assert isinstance(pet, HasStats)

    def test_feed_increases_hunger(self, qt_app):
        from pet.full_pet import FullPet
        from utils.database import PetDatabase

        db = PetDatabase()
        pet = FullPet("fox", "Test", db)
        pet.hunger = 50.0
        pet.feed()
        assert pet.hunger > 50.0

    def test_no_cat_default(self, qt_app):
        from pet.full_pet import FullPet
        from utils.database import PetDatabase

        db = PetDatabase()
        pet = FullPet(db=db)
        assert pet.pet_type != "cat"

    def test_energy_decays(self, qt_app):
        from pet.full_pet import FullPet
        from utils.database import PetDatabase

        db = PetDatabase()
        pet = FullPet("fox", "Test", db)
        initial = pet.energy
        pet.update_stats()
        assert pet.energy < initial

    def test_mood_no_cat_emojis(self, qt_app):
        from pet.full_pet import FullPet
        from utils.database import PetDatabase

        db = PetDatabase()
        pet = FullPet("fox", "Test", db)
        for hunger, energy, happiness in [
            (10, 80, 80), (80, 10, 80), (80, 80, 90), (80, 80, 20)
        ]:
            pet.hunger, pet.energy, pet.happiness = hunger, energy, happiness
            mood = pet.get_mood()
            assert "😸" not in mood
            assert "😿" not in mood
            assert "😺" not in mood
