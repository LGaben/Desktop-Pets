"""Event-driven app menu journeys; all persistence is isolated by conftest."""
import os
from pathlib import Path

import pytest
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QMenu, QPushButton, QStyle, QStyleOptionButton, QWidget

from ui.menu_visuals import colors
from utils.i18n import t
from utils.settings_store import store


def open_menu(window, qt_app):
    QTest.mouseClick(window, Qt.MouseButton.RightButton, pos=window.rect().center())
    qt_app.processEvents()
    panel = window.interaction_panel
    assert panel is not None and panel.isVisible()
    assert not panel.findChildren(QMenu)
    return panel


def click(panel, label, qt_app):
    button = next(button for button in panel.findChildren(QPushButton) if button.accessibleName() == label)
    panel._scroll.ensureWidgetVisible(button)
    qt_app.processEvents()
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    qt_app.processEvents()


@pytest.mark.parametrize('style', ['panel', 'ring'])
@pytest.mark.parametrize('lang', ['ru', 'en'])
def test_real_menu_journey(window, qt_app, style, lang):
    store.lang, store.menu_style = lang, style
    window.show()
    qt_app.processEvents()
    click(open_menu(window, qt_app), t('pet_action'), qt_app)
    assert window.heart_overlay.active
    click(open_menu(window, qt_app), t('sleep'), qt_app)
    assert window.pet._user_sleep and not window.heart_overlay.active
    click(open_menu(window, qt_app), t('wake_up'), qt_app)
    assert not window.pet._user_sleep
    click(open_menu(window, qt_app), t('start_follow'), qt_app)
    assert window.pet.following_mouse
    click(open_menu(window, qt_app), t('stop_follow'), qt_app)
    assert not window.pet.following_mouse
    click(open_menu(window, qt_app), t('ball_action'), qt_app)
    assert window.ball_widget is not None and window.ball_widget.isVisible()
    window._end_ball()
    click(open_menu(window, qt_app), t('settings'), qt_app)
    assert window.settings_window.isVisible()
    window.settings_window.close()
    click(open_menu(window, qt_app), t('hide_to_tray'), qt_app)
    assert not window.isVisible()


@pytest.mark.parametrize('style', ['panel', 'ring'])
@pytest.mark.parametrize('lang', ['ru', 'en'])
@pytest.mark.parametrize('dark', [False, True])
def test_geometry_text_and_actual_painted_pixels(window, qt_app, monkeypatch, style, lang, dark):
    import ui.interaction_panel as module
    bounds = QRect(-1200, -800, 1100, 750)
    monkeypatch.setattr(module, 'available_rect', lambda _: bounds)
    store.lang, store.menu_style = lang, style
    previous = qt_app.palette()
    palette = QPalette(previous)
    palette.setColor(QPalette.ColorRole.Window, QColor('#242321' if dark else '#fbfaf7'))
    qt_app.setPalette(palette)
    window.pet.name = '<img src="file:///never-load">' + 'abcdefghij' * 5
    window.move(-150, -100)
    window.show()
    try:
        panel = open_menu(window, qt_app)
        assert panel.menu_style == style and not panel._compact
        assert bounds.contains(panel.geometry())
        buttons = panel.findChildren(QPushButton)
        profile = panel.findChild(QPushButton, 'petProfile')
        if profile is not None:
            for child in profile.findChildren(QWidget):
                assert profile.rect().contains(QRect(child.mapTo(profile, QPoint()), child.size()))
        for button in buttons:
            assert button.width() >= 44 and button.height() >= 44
            if button.objectName() == 'ringAction':
                assert button.height() >= 56
                assert button.height() < profile.height()
            if button.text():
                option = QStyleOptionButton()
                option.initFrom(button)
                content = button.style().subElementRect(QStyle.SubElement.SE_PushButtonContents, option, button)
                icon_space = 0 if button.icon().isNull() else button.iconSize().width() + 4
                assert button.fontMetrics().horizontalAdvance(button.text()) <= content.width() - icon_space
                assert button.fontMetrics().height() <= content.height()
            for other in buttons:
                if other is button:
                    continue
                first = QRect(button.mapTo(panel, QPoint()), button.size())
                second = QRect(other.mapTo(panel, QPoint()), other.size())
                assert not first.intersects(second)
        image = panel.grab().toImage()
        ratio = image.devicePixelRatio()
        if style == 'panel':
            pixel = image.pixelColor(round(4 * ratio), round(panel.height() / 2 * ratio))
            expected = QColor(colors()['surface'])
            assert pixel.alpha() == 255
            assert max(abs(pixel.red() - expected.red()), abs(pixel.green() - expected.green()),
                       abs(pixel.blue() - expected.blue())) <= 3
        else:
            assert image.pixelColor(0, 0).alpha() == 0
            for button in buttons:
                point = button.mapTo(panel, QPoint(4, button.height() // 2))
                pixel = image.pixelColor(round(point.x() * ratio), round(point.y() * ratio))
                assert pixel.alpha() == 255
        if directory := os.environ.get('PET_MENU_E2E_OUTPUT'):
            destination = Path(directory) / f'{style}-{lang}-{"dark" if dark else "light"}.png'
            assert not destination.exists()
            assert image.save(str(destination))
    finally:
        window._close_interaction_panel()
        qt_app.setPalette(previous)


def test_inline_style_switch_closes_siblings_and_persists(window, qt_app, isolated_persistence):
    window._add_satellite('panda')
    satellite = window._satellites[0]
    window.show()
    satellite.show()
    open_menu(satellite, qt_app)
    panel = open_menu(window, qt_app)
    picker = next(button for button in panel.findChildren(QPushButton) if button.property('menuStyle') == 'ring')
    QTest.mouseClick(picker, Qt.MouseButton.LeftButton)
    qt_app.processEvents()
    assert isolated_persistence.values['menu_style'] == 'ring'
    assert window.interaction_panel is None and satellite.interaction_panel is None


def test_ring_profile_is_at_requested_cursor_away_from_edges(window, qt_app, monkeypatch):
    import ui.interaction_panel as module
    monkeypatch.setattr(module, 'available_rect', lambda _: QRect(-1400, -1000, 1400, 1100))
    store.menu_style = 'ring'
    point = QPoint(-700, -600)
    window._show_context_menu(point)
    qt_app.processEvents()
    panel = window.interaction_panel
    profile = panel.findChild(QPushButton, 'petProfile')
    assert not panel._compact
    assert (profile.mapToGlobal(profile.rect().center()) - point).manhattanLength() <= 2
