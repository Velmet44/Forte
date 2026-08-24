from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint, QEvent
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from forte.player import Player
from forte.playlist import Playlist
from forte.state import SessionState
from forte.ui.now_playing import NowPlayingPanel
from forte.ui.playlist_panel import PlaylistPanel


class MainWindow(QMainWindow):
    """Frameless main window hosting the playlist and now-playing panels."""

    def __init__(
        self,
        session: dict,
        state: SessionState,
        theme: dict,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session = session
        self.state = state
        self.theme = theme
        self.playlist = Playlist()
        self.player = Player()
        self.current_index = -1
        self._drag_pos: QPoint | None = None
        self._title_buttons: list[QPushButton] = []

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(900, 580)

        self._build_title_bar()
        self._build_body()
        self._build_status_bar()

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self._title_bar)
        central_layout.addWidget(self._body, 1)
        central_layout.addWidget(self._status_bar)
        self.setCentralWidget(central)

        self._connect_signals()
        self._restore_session()
        if not self.player.available:
            self._set_status("No audio device — playback disabled")

    def _build_title_bar(self) -> None:
        bar = QWidget()
        bar.setObjectName("titleBar")
        bar.setFixedHeight(36)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(4)

        label = QLabel("FORTE")
        label.setObjectName("titleLabel")
        font = QFont("Inter", 12, QFont.Weight.DemiBold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        label.setFont(font)

        layout.addWidget(label)
        layout.addStretch(1)

        for glyph, tooltip, slot in (
            ("–", "Minimise", self._minimise),
            ("⚙", "Settings", self._open_settings),
            ("✕", "Close", self._quit_app),
        ):
            btn = QPushButton(glyph)
            btn.setObjectName("titleButton")
            btn.setToolTip(tooltip)
            btn.setFixedSize(32, 28)
            btn.clicked.connect(slot)
            layout.addWidget(btn)
            self._title_buttons.append(btn)

        self._title_bar = bar
        for widget in (bar, *bar.findChildren(QWidget)):
            widget.installEventFilter(self)

    def _build_body(self) -> None:
        body = QWidget()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.playlist_panel = PlaylistPanel(self.playlist, self.theme)
        self.playlist_panel.setFixedWidth(260)

        divider = QWidget()
        divider.setObjectName("divider")
        divider.setFixedWidth(1)

        self.now_playing = NowPlayingPanel(self.theme)

        layout.addWidget(self.playlist_panel)
        layout.addWidget(divider)
        layout.addWidget(self.now_playing, 1)
        self._body = body

    def _build_status_bar(self) -> None:
        bar = QWidget()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(24)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)
        self._status_label = QLabel("No track loaded")
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)
        self._status_bar = bar

    def _connect_signals(self) -> None:
        self.playlist_panel.track_selected.connect(self._on_track_selected)
        self.playlist_panel.playlist_changed.connect(self._on_playlist_changed)
        self.playlist_panel.play_next.connect(self._on_play_next)

    def _restore_session(self) -> None:
        for path in self.session.get("last_playlist", []):
            try:
                self.playlist.add_track(path)
            except Exception:
                continue
        if len(self.playlist) > 0:
            self.playlist_panel.model.refresh()
            index = self.session.get("last_track_index", -1)
            if 0 <= index < len(self.playlist):
                self.current_index = index
                self.playlist_panel.set_current_track(index)
                track = self.playlist[index]
                self._set_status(f"Loaded: {track.title} — {track.artist}")

    def _set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _on_track_selected(self, index: int) -> None:
        if not 0 <= index < len(self.playlist):
            return
        self.current_index = index
        self.playlist_panel.set_current_track(index)
        track = self.playlist[index]
        self.now_playing.set_track(track)
        if not self.player.available:
            self._set_status(f"Selected: {track.title} — {track.artist} (no audio device)")
            return
        self._set_status(f"Now Playing: {track.title} — {track.artist}")
        try:
            self.player.load(track.filepath)
            self.player.play()
        except Exception:
            pass

    def _on_playlist_changed(self) -> None:
        if len(self.playlist) == 0:
            self._set_status("No track loaded")

    def _on_play_next(self, index: int) -> None:
        if self.current_index < 0 or not 0 <= index < len(self.playlist):
            return
        dest = self.current_index + 1
        if index < dest:
            dest -= 1
        self.playlist.move_track(index, dest)
        self.playlist_panel.model.refresh()
        self.playlist_panel.playlist_changed.emit()

    def _minimise(self) -> None:
        if self.session.get("minimise_to_tray", True):
            self.hide()
        else:
            self.showMinimized()

    def _open_settings(self) -> None:
        # Settings dialog is implemented in a later stage.
        pass

    def _quit_app(self) -> None:
        self._save_session()
        QApplication.quit()

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton and obj not in self._title_buttons:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.type() == QEvent.Type.MouseMove:
            if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self._drag_pos)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self._drag_pos = None
        return super().eventFilter(obj, event)

    def closeEvent(self, event) -> None:
        self._save_session()
        event.accept()

    def _save_session(self) -> None:
        data = dict(self.session)
        data["last_playlist"] = [track.filepath for track in self.playlist]
        data["last_track_index"] = self.current_index
        data["last_position"] = self.player.get_position() if self.player.is_playing() else 0.0
        if "volume" not in data:
            data["volume"] = 1.0
        self.state.save(data)
