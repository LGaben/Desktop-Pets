"""Frame ordering and reuse across instances and directions."""
import subprocess
import sys

from PyQt6.QtGui import QColor, QPixmap
from utils.sprite_loader import SpriteLoader


def test_numeric_frame_order_and_shared_mirroring(qt_app, tmp_path, monkeypatch):
    import utils.sprite_loader as module
    folder = tmp_path / "assets" / "sprites" / "test" / "idle"
    folder.mkdir(parents=True)
    for number in (1, 2, 10):
        image = QPixmap(100, 80)
        image.fill(QColor(number, 0, 0))
        assert image.save(str(folder / f"frame_{number}.png"))
    monkeypatch.setattr(module, "resource_base", lambda: tmp_path)
    SpriteLoader.clear_cache()
    first, second = SpriteLoader("test"), SpriteLoader("test")
    frames = first.get_animation("idle")
    assert [frame.toImage().pixelColor(0, 0).red() for frame in frames] == [1, 2, 10]
    assert all(frame.width() <= 48 and frame.height() <= 48 for frame in frames)
    assert frames is second.get_animation("idle")
    mirrored = first.get_animation("idle", mirrored=True)
    assert mirrored is second.get_animation("idle", mirrored=True)
    keys = [frame.cacheKey() for frame in mirrored]
    assert keys == [frame.cacheKey() for frame in first.get_animation("idle", mirrored=True)]


def test_shared_cache_is_bounded_and_live_frames_survive(qt_app, monkeypatch):
    SpriteLoader.clear_cache()
    monkeypatch.setattr(SpriteLoader, "_cache_limit", 3)
    loader = SpriteLoader("fox")
    frame = loader.get_animation("idle")[0]
    key = frame.cacheKey()
    for pet_type in ("panda", "dog", "turtle", "snail"):
        SpriteLoader(pet_type).get_animation("idle")
    assert len(SpriteLoader._shared) <= 3
    assert not frame.isNull()
    assert loader.get_animation("idle")[0].cacheKey() == key
    SpriteLoader.clear_cache()


def test_loader_construction_requires_no_qapplication():
    result = subprocess.run([sys.executable, "-c",
        "from utils.sprite_loader import SpriteLoader; loader=SpriteLoader('fox'); "
        "assert not loader.sprites_cache"], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
