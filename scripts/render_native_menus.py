"""Render the actual Qt menus without starting pets, database, registry or tray."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--lang', choices=('ru', 'en'), default='ru')
    parser.add_argument('--theme', choices=('light', 'dark', 'both'), default='light')
    parser.add_argument('--force', action='store_true', help='Replace only the requested menu PNG files')
    args = parser.parse_args()
    themes = ('light', 'dark') if args.theme == 'both' else (args.theme,)
    outputs = [(theme, style, args.output / f'{style}-{theme}-{args.lang}.png')
               for theme in themes for style in ('panel', 'ring')]
    for _, _, destination in outputs:
        if destination.exists() and not args.force:
            raise FileExistsError(f'{destination} already exists; use --force to update menu PNGs')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PyQt6.QtCore import QPoint, QRect
    from PyQt6.QtGui import QColor, QPalette, QPixmap
    from PyQt6.QtWidgets import QApplication
    from ui import interaction_panel
    from utils.i18n import set_lang, t
    app = QApplication([])
    palette = app.palette()
    set_lang(args.lang)  # Memory only; no load/save of registry settings.
    interaction_panel.available_rect = lambda _: QRect(0, 0, 1200, 800)
    args.output.mkdir(parents=True, exist_ok=True)
    portrait = QPixmap(str(ROOT / 'assets/sprites/fox/idle/frame_1.png'))
    actions = [(t(key), lambda: None) for key in
               ('pet_action', 'ball_action', 'sleep', 'start_follow', 'settings', 'hide_to_tray', 'quit')]
    for theme, style, destination in outputs:
        palette.setColor(QPalette.ColorRole.Window, QColor('#242321' if theme == 'dark' else '#fbfaf7'))
        app.setPalette(palette)
        menu = interaction_panel.InteractionPanel(None, t('name_fox'), t('personality_curious'),
                                                   actions, style, portrait, style_changed=lambda _: None)
        menu.open_at(QPoint(100, 100))
        app.processEvents()
        if not menu.grab().save(str(destination)):
            raise OSError(f'Could not save {destination}')
        print(f'{destination}: {menu.width()}x{menu.height()}, radial={menu._radial}')
        menu.close()
        menu.deleteLater()
    app.processEvents()


if __name__ == '__main__':
    try:
        main()
    except (OSError, ImportError, RuntimeError) as exc:
        print(f'Menu capture failed: {exc}', file=sys.stderr)
        sys.exit(1)
