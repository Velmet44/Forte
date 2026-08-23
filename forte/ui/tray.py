from __future__ import annotations

from PyQt6.QtWidgets import QSystemTrayIcon


class Tray(QSystemTrayIcon):
    """System tray icon with play/pause/next controls and minimise-to-tray support."""

    def __init__(self) -> None:
        super().__init__()
        pass
