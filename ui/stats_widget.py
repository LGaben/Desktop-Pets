# -*- coding: utf-8 -*-
"""Statistics display window for stat-bearing pets."""
from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pet.protocols import HasStats

_WINDOW_STYLESHEET = """
    QWidget {
        background-color: #f0f0f0;
        font-family: Arial, sans-serif;
    }
    QProgressBar {
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
        height: 20px;
    }
    QProgressBar::chunk { border-radius: 3px; }
    QPushButton {
        border: 2px solid #8f8f91;
        border-radius: 6px;
        background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                          stop:0 #f6f7fa, stop:1 #dadbde);
        min-width: 80px;
        padding: 5px;
    }
    QPushButton:pressed {
        background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                          stop:0 #dadbde, stop:1 #f6f7fa);
    }
"""


class StatsWindow(QWidget):
    """Displays hunger, happiness, energy, health and level for a :class:`~pet.protocols.HasStats` pet.

    Args:
        pet: Any object that satisfies the :class:`~pet.protocols.HasStats` protocol.
    """

    def __init__(self, pet: HasStats) -> None:
        super().__init__()
        self.pet = pet
        self._init_ui()

        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._refresh)
        self._update_timer.start(1000)

    def _init_ui(self) -> None:
        self.setWindowTitle(f"Статистика — {self.pet.name}")
        self.setFixedSize(350, 450)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        main = QVBoxLayout()
        main.setSpacing(10)
        main.setContentsMargins(15, 15, 15, 15)

        title = QLabel(f"🐾 {self.pet.name}")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        # Level / exp row
        level_row = QHBoxLayout()
        self.level_label = QLabel(f"Уровень: {self.pet.level}")
        level_row.addWidget(self.level_label)
        self.exp_label = QLabel(f"Опыт: {self.pet.exp}/{self.pet.level * 100}")
        level_row.addWidget(self.exp_label)
        main.addLayout(level_row)

        self.exp_bar = QProgressBar()
        self.exp_bar.setMaximum(self.pet.level * 100)
        self.exp_bar.setValue(self.pet.exp)
        main.addWidget(self.exp_bar)

        main.addWidget(self._separator())

        # Stats grid
        grid = QGridLayout()
        self.hunger_bar, self.hunger_lbl = self._stat_row(grid, 0, "🍖 Голод:", self.pet.hunger)
        self.happiness_bar, self.happiness_lbl = self._stat_row(grid, 1, "😊 Счастье:", self.pet.happiness)
        self.energy_bar, self.energy_lbl = self._stat_row(grid, 2, "⚡ Энергия:", self.pet.energy)
        self.health_bar, self.health_lbl = self._stat_row(grid, 3, "❤️ Здоровье:", self.pet.health)
        main.addLayout(grid)

        main.addWidget(self._separator())

        self.state_label = QLabel(f"Состояние: {self.pet.state.value}")
        main.addWidget(self.state_label)

        self.mood_label = QLabel(f"Настроение: {self.pet.get_mood()}")
        main.addWidget(self.mood_label)

        main.addWidget(QLabel(f"Тип: {self.pet.pet_type.title()}"))

        main.addWidget(self._separator())

        btn_row = QHBoxLayout()
        for label, slot in [
            ("🍖 Покормить", self.pet.feed),
            ("🎾 Играть", self.pet.play),
            ("💤 Спать", self.pet.sleep),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        main.addLayout(btn_row)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        main.addWidget(close_btn)

        self.setLayout(main)
        self.setStyleSheet(_WINDOW_STYLESHEET)

    # -- helpers --------------------------------------------------------------

    def _separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def _stat_row(
        self,
        grid: QGridLayout,
        row: int,
        label: str,
        value: float,
    ) -> tuple[QProgressBar, QLabel]:
        grid.addWidget(QLabel(label), row, 0)
        bar = QProgressBar()
        bar.setMaximum(100)
        self._color_bar(bar, value)
        grid.addWidget(bar, row, 1)
        lbl = QLabel(f"{int(value)}%")
        grid.addWidget(lbl, row, 2)
        return bar, lbl

    @staticmethod
    def _color_bar(bar: QProgressBar, value: float) -> None:
        bar.setValue(int(value))
        if value > 70:
            color = "#4CAF50"
        elif value > 40:
            color = "#FF9800"
        else:
            color = "#F44336"
        bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")

    def _refresh(self) -> None:
        """Refresh all displayed values from the live pet object."""
        self.level_label.setText(f"Уровень: {self.pet.level}")
        self.exp_label.setText(f"Опыт: {self.pet.exp}/{self.pet.level * 100}")
        self.exp_bar.setMaximum(self.pet.level * 100)
        self.exp_bar.setValue(self.pet.exp)

        for bar, lbl, val in [
            (self.hunger_bar, self.hunger_lbl, self.pet.hunger),
            (self.happiness_bar, self.happiness_lbl, self.pet.happiness),
            (self.energy_bar, self.energy_lbl, self.pet.energy),
            (self.health_bar, self.health_lbl, self.pet.health),
        ]:
            self._color_bar(bar, val)
            lbl.setText(f"{int(val)}%")

        self.state_label.setText(f"Состояние: {self.pet.state.value}")
        self.mood_label.setText(f"Настроение: {self.pet.get_mood()}")

    def closeEvent(self, event) -> None:
        self._update_timer.stop()
        event.accept()
