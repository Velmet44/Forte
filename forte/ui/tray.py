from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPolygonF, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu


def _make_icon(accent: str) -> QIcon:
    pm = QPixmap(32, 32)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(accent))
    painter.drawRoundedRect(2, 2, 28, 28, 7, 7)
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawPolygon(QPolygonF([
        QPointF(13, 10),
        QPointF(13, 22),
        QPointF(22, 16),
    ]))
    painter.end()
    return QIcon(pm)


class Tray(QSystemTrayIcon):
    """System tray icon: shows the current track in its tooltip, restores the
    window on double-click, and exposes play/pause/next/prev/quit via signals."""

    toggle_requested = pyqtSignal()
    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    restore_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, accent: str, parent=None) -> None:
        super().__init__(parent)
        self.setIcon(_make_icon(accent))
        self.setToolTip("Forte")

        menu = QMenu()
        toggle = QAction("Play / Pause", menu)
        toggle.triggered.connect(self.toggle_requested.emit)
        nxt = QAction("Next", menu)
        nxt.triggered.connect(self.next_requested.emit)
        prv = QAction("Previous", menu)
        prv.triggered.connect(self.prev_requested.emit)
        show = QAction("Show Forte", menu)
        show.triggered.connect(self.restore_requested.emit)
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(toggle)
        menu.addAction(prv)
        menu.addAction(nxt)
        menu.addSeparator()
        menu.addAction(show)
        menu.addAction(quit_action)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_requested.emit()

    def set_now_playing(self, text: str) -> None:
        self.setToolTip(text)
