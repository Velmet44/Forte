from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QPushButton,
    QHBoxLayout,
)

_THEMES = [("Dark", "dark"), ("Light", "light")]
_CROSSFADE = [("Off", 0), ("1 second", 1), ("2 seconds", 2), ("3 seconds", 3)]


class SettingsDialog(QDialog):
    """Settings modal: theme, crossfade, minimise-to-tray, file extensions.

    Returns the chosen values via :meth:`values` when accepted. No persistent
    state is touched here — ``MainWindow`` applies and saves the result.
    """

    def __init__(self, current: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(320)
        self.setModal(True)

        layout = QFormLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self._theme = QComboBox()
        for label, value in _THEMES:
            self._theme.addItem(label, value)
        self._set_combo(self._theme, current.get("theme", "dark"))

        self._crossfade = QComboBox()
        for label, value in _CROSSFADE:
            self._crossfade.addItem(label, value)
        self._set_combo(self._crossfade, int(current.get("crossfade", 0)))

        self._minimise = QCheckBox("Minimise to tray on close")
        self._minimise.setChecked(bool(current.get("minimise_to_tray", True)))

        self._extensions = QCheckBox("Show file extensions in playlist")
        self._extensions.setChecked(bool(current.get("show_extensions", False)))

        layout.addRow("Theme", self._theme)
        layout.addRow("Crossfade", self._crossfade)
        layout.addRow(self._minimise)
        layout.addRow(self._extensions)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        ok = QPushButton("OK")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout.addRow(buttons)

    @staticmethod
    def _set_combo(combo: QComboBox, value) -> None:
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def values(self) -> dict:
        return {
            "theme": self._theme.currentData(),
            "crossfade": int(self._crossfade.currentData()),
            "minimise_to_tray": self._minimise.isChecked(),
            "show_extensions": self._extensions.isChecked(),
        }
