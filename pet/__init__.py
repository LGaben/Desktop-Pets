"""Desktop pet public API, loaded lazily so metadata needs no Qt runtime."""
from importlib import import_module

_EXPORTS = {
    "BasePet": "base_pet", "PetFactory": "factory", "FullPet": "full_pet",
    "SimplePet": "simple_pet", "PetState": "state",
    "BallChaser": "protocols", "HasStats": "protocols",
    "MouseFollower": "protocols", "PetStorage": "protocols",
}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(f"pet.{_EXPORTS[name]}"), name)
    globals()[name] = value
    return value
