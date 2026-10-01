from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QObject, QPointF, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPolygonF, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu


def _make_icon(accent: str) -> QIcon:
    pm = QPixmap(32, 32)
    pm.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(accent))
    painter.drawRoundedRect(2, 2, 28, 28, 7, 7)
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawPolygon(
        QPolygonF(
            [
                QPointF(13, 10),
                QPointF(13, 22),
                QPointF(22, 16),
            ]
        )
    )
    painter.end()
    return QIcon(pm)


class ForteTray(QObject):
    """System tray controller for Forte.

    Creates a QSystemTrayIcon with a dynamic context menu. Single-click toggles
    the main window visibility; double-click always shows and raises it. All
    interactions are exposed as signals so MainWindow can wire behaviour without
    the tray reaching into UI widgets. On platforms without a system tray the
    object degrades to a no-op (``available`` is ``False``).
    """

    toggle_requested = pyqtSignal()
    show_requested = pyqtSignal()
    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    playpause_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(
        self,
        accent: str,
        icon_path: str | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._playing = False
        self._title = ""
        self._artist = ""

        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray = None
            return

        try:
            self._tray = QSystemTrayIcon(parent)
            self._tray.setIcon(self._load_icon(accent, icon_path))
            self._build_menu()
            self._tray.activated.connect(self._on_activated)
            self._refresh_tooltip()
        except Exception:
            self._tray = None

    @staticmethod
    def _load_icon(accent: str, icon_path: str | None) -> QIcon:
        if icon_path:
            p = Path(icon_path)
            if p.is_file():
                pm = QPixmap(p)
                if not pm.isNull():
                    return QIcon(pm.scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        return _make_icon(accent)

    def _build_menu(self) -> None:
        menu = QMenu()
        self._play_action = QAction("▶ Play", menu)
        self._play_action.triggered.connect(self.playpause_requested.emit)
        next_action = QAction("⏭ Next", menu)
        next_action.triggered.connect(self.next_requested.emit)
        prev_action = QAction("⏮ Previous", menu)
        prev_action.triggered.connect(self.prev_requested.emit)
        show_action = QAction("Show Window", menu)
        show_action.triggered.connect(self.show_requested.emit)
        quit_action = QAction("Quit Forte", menu)
        quit_action.triggered.connect(self.quit_requested.emit)

        menu.addAction(self._play_action)
        menu.addAction(next_action)
        menu.addAction(prev_action)
        menu.addSeparator()
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_requested.emit()

    def _refresh_tooltip(self) -> None:
        if self._tray is None:
            return
        if self._title:
            label = f"{self._title} — {self._artist}" if self._artist else self._title
            symbol = "▶" if not self._playing else "⏸"
            self._tray.setToolTip(f"Forte · {symbol} {label}")
        else:
            self._tray.setToolTip("Forte · No track loaded")

    def set_playing(self, playing: bool) -> None:
        self._playing = bool(playing)
        if self._tray is not None and getattr(self, "_play_action", None) is not None:
            self._play_action.setText("⏸ Pause" if playing else "▶ Play")
        self._refresh_tooltip()

    def set_now_playing(self, title: str, artist: str = "") -> None:
        self._title = title or ""
        self._artist = artist or ""
        self._refresh_tooltip()

    def show(self) -> None:
        if self._tray is not None:
            self._tray.show()

    def hide(self) -> None:
        if self._tray is not None:
            self._tray.hide()

    @property
    def available(self) -> bool:
        return self._tray is not None
