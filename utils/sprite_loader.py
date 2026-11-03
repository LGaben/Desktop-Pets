# -*- coding: utf-8 -*-
"""Sprite loading and caching for pet animations."""
from __future__ import annotations

import logging
import re
from collections import OrderedDict
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap, QTransform

from PyQt6.QtWidgets import QApplication

from utils.paths import resource_base

_log = logging.getLogger(__name__)

_DEFAULT_ANIMATIONS = ["idle", "walk", "sleep", "eat", "play", "sit"]

_SPRITE_SIZE = 48  # all pets scaled to fit fox's original size (~46×37)

_PLACEHOLDER_COLORS: dict[str, QColor] = {
    "idle":      QColor(100, 150, 200),
    "walk":      QColor(100, 200, 100),
    "run":       QColor(80,  220, 80),
    "sleep":     QColor(150, 100, 200),
    "eat":       QColor(200, 150, 100),
    "play":      QColor(200, 100, 150),
    "sit":       QColor(150, 150, 150),
    "lie":       QColor(170, 130, 190),
    "with_ball": QColor(60,  200, 120),
}


def natural_frame_key(path: Path) -> tuple:
    return tuple((1, int(part)) if part.isdigit() else (0, part.lower())
                 for part in re.split(r"(\d+)", path.name))


class SpriteLoader:
    """Loads and caches animation frames for a single pet type.

    Frames are loaded from ``assets/sprites/{pet_type}/{animation}/frame_*.png``.
    """

    # LRU holds at most 128 animation/direction sets. Live loaders retain their
    # own references; eviction never invalidates sprites currently being shown.
    _shared = OrderedDict()
    _cache_limit = 128

    @classmethod
    def clear_cache(cls) -> None:
        cls._shared.clear()

    def __init__(
        self,
        pet_type: str,
        animations: list[str] | None = None,
    ) -> None:
        self.pet_type = pet_type
        self.base_path: Path = resource_base() / "assets" / "sprites" / pet_type
        self._animations: list[str] = animations if animations is not None else list(_DEFAULT_ANIMATIONS)
        self.sprites_cache: dict[tuple[str, bool], list[QPixmap]] = {}
        # Load lazily: constructing a loader requires no QApplication.

    # -- public API -----------------------------------------------------------

    def get_animation(self, animation_name: str, mirrored: bool = False) -> list[QPixmap]:
        """Return cached frames, loading them lazily when not yet cached."""
        if QApplication.instance() is None:
            raise RuntimeError("Create QApplication before requesting sprite frames")
        local_key = (animation_name, mirrored)
        if local_key not in self.sprites_cache:
            key = (str(self.base_path.resolve()), animation_name, mirrored)
            if key not in self._shared:
                if mirrored:
                    frames = [frame.transformed(QTransform().scale(-1, 1))
                              for frame in self.get_animation(animation_name)]
                else:
                    frames = self._load_animation(animation_name)
                self._shared[key] = frames
                while len(self._shared) > self._cache_limit:
                    self._shared.popitem(last=False)
            self._shared.move_to_end(key)
            self.sprites_cache[local_key] = self._shared[key]
        return self.sprites_cache[local_key]

    def set_pet_type(self, new_pet_type: str) -> None:
        self.pet_type = new_pet_type
        self.base_path = resource_base() / "assets" / "sprites" / new_pet_type
        self._reload()

    # -- private helpers ------------------------------------------------------

    def _reload(self) -> None:
        self.sprites_cache.clear()

    def _load_animation(self, animation_name: str) -> list[QPixmap]:
        anim_path = self.base_path / animation_name
        if anim_path.exists():
            frames = [QPixmap(str(f)) for f in sorted(anim_path.glob("*.png"), key=natural_frame_key)]
            valid = [p for p in frames if not p.isNull()]
            if valid:
                return [self._normalise(p) for p in valid]

        _log.debug("No sprites found for %s/%s – using placeholder", self.pet_type, animation_name)
        return [self._create_placeholder(animation_name)]

    @staticmethod
    def _normalise(px: QPixmap) -> QPixmap:
        if px.width() <= _SPRITE_SIZE and px.height() <= _SPRITE_SIZE:
            return px
        return px.scaled(
            _SPRITE_SIZE, _SPRITE_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _create_placeholder(self, animation_name: str = "idle") -> QPixmap:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = _PLACEHOLDER_COLORS.get(animation_name, QColor(150, 150, 150))
        painter.setBrush(color)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawEllipse(16, 16, 32, 32)
        painter.setBrush(Qt.GlobalColor.black)
        if animation_name == "sleep":
            painter.drawEllipse(22, 28, 4, 2)
            painter.drawEllipse(38, 28, 4, 2)
        else:
            painter.drawEllipse(24, 28, 4, 4)
            painter.drawEllipse(36, 28, 4, 4)
        painter.drawEllipse(30, 34, 4, 2)
        painter.end()
        return pixmap
