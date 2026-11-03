"""Native menu geometry, contrast palettes and plain-text identity."""
import pytest
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QPalette, QPixmap
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QStyle, QStyleOptionButton

from ui.interaction_panel import InteractionPanel
from ui.menu_visuals import colors
from utils.i18n import t


@pytest.mark.parametrize('dark', [False, True])
@pytest.mark.parametrize('style', ['panel', 'ring'])
def test_native_menu_targets_theme_and_identity(qt_app, monkeypatch, dark, style):
    import ui.interaction_panel as module
    monkeypatch.setattr(module, 'available_rect', lambda _: QRect(-900, -500, 900, 650))
    old_palette = qt_app.palette()
    palette = QPalette(old_palette)
    palette.setColor(QPalette.ColorRole.Window, QColor('#202020' if dark else '#fafafa'))
    qt_app.setPalette(palette)
    name = '<img src="file:///never-load">' + 'Very long name ' * 4
    portrait = QPixmap(46, 37)
    portrait.fill(Qt.GlobalColor.transparent)
    actions = [(t(key), lambda: None) for key in
               ('pet_action', 'ball_action', 'sleep', 'start_follow', 'settings', 'hide_to_tray', 'quit')]
    panel = InteractionPanel(None, name, 'Curious', actions, style, portrait)
    try:
        panel.open_at(QPoint(-300, -100))
        qt_app.processEvents()
        assert panel._radial == (style == 'ring')
        assert colors()['surface'] == ('#242321' if dark else '#fbfaf7')
        heading = panel.findChild(QLabel, 'petName')
        assert heading.text() == heading.accessibleName() == name
        assert heading.textFormat() == Qt.TextFormat.PlainText
        assert heading.toolTip() == ''
        assert heading.height() < 44 and heading.width() < panel.width()
        buttons = panel.findChildren(QPushButton)
        assert all(not button.icon().isNull() for button in buttons if button.objectName() != 'petProfile')
        assert all(button.height() >= 44 for button in buttons)
        if style == 'panel':
            assert panel.width() == panel._content_hint().width() + 16
            assert panel.width() >= 272
            assert panel._scroll.horizontalScrollBar().maximum() == 0
            assert QRect(-900, -500, 900, 650).contains(panel.geometry())
            assert panel.findChild(QLabel, 'petPortrait').pixmap().width() <= 40
        else:
            targets = [button for button in buttons if button.objectName() == 'ringAction']
            assert len(targets) == 3
            assert panel.property('radial') is True
            assert all(not first.geometry().intersects(second.geometry())
                       for index, first in enumerate(targets) for second in targets[index + 1:])
    finally:
        panel.close()
        panel.deleteLater()
        qt_app.setPalette(old_palette)


@pytest.mark.parametrize('style', ['panel', 'ring'])
def test_settings_is_direct_and_initial_focus_is_primary(qt_app, monkeypatch, style):
    import ui.interaction_panel as module
    monkeypatch.setattr(module, 'available_rect', lambda _: QRect(0, 0, 900, 650))
    calls = []
    actions = [(t(key), lambda key=key: calls.append(key)) for key in
               ('pet_action', 'ball_action', 'sleep', 'start_follow', 'settings', 'hide_to_tray', 'quit')]
    menu = InteractionPanel(None, 'Pet', '', actions, style)
    try:
        menu.open_at(QPoint(10, 10))
        qt_app.processEvents()
        assert QApplication.focusWidget().accessibleName() == t('pet_action')
        settings = next(button for button in menu.findChildren(QPushButton)
                        if button.accessibleName() == t('settings'))
        QTest.mouseClick(settings, Qt.MouseButton.LeftButton)
        assert calls == ['settings'] and not menu.isVisible()
    finally:
        menu.close()
        menu.deleteLater()


def test_action_sizes_use_final_polished_font_and_styles(qt_app, monkeypatch):
    import ui.interaction_panel as module
    monkeypatch.setattr(module, 'available_rect', lambda _: QRect(0, 0, 1400, 1000))
    menu = InteractionPanel(None, 'Pet', '', [(t('start_follow'), lambda: None)])
    button = menu.findChild(QPushButton)
    button.ensurePolished()
    pixels = max(32, button.fontMetrics().height() * 2)
    menu.setStyleSheet(menu.styleSheet() + f' QPushButton {{ font-size:{pixels}px; padding:9px 18px; }}')
    try:
        menu.open_at(QPoint(10, 10))
        qt_app.processEvents()
        assert button.font().pixelSize() == pixels
        assert button.minimumWidth() >= button.fontMetrics().horizontalAdvance(button.text()) + button.iconSize().width() + 4
        option = QStyleOptionButton()
        option.initFrom(button)
        content = button.style().subElementRect(QStyle.SubElement.SE_PushButtonContents, option, button)
        assert button.fontMetrics().horizontalAdvance(button.text()) <= content.width() - button.iconSize().width() - 4
        assert button.fontMetrics().height() <= content.height()
        assert menu._scroll.horizontalScrollBar().maximum() == 0
    finally:
        menu.close()
        menu.deleteLater()
