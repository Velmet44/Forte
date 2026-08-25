from __future__ import annotations

import pygame
from PyQt6.QtCore import Qt, QPoint, QEvent, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QSystemTrayIcon,
)

from forte.player import Player, TRACK_ENDED
from forte.playlist import Playlist
from forte.metadata import read_metadata, _format_duration, TrackMetadata
from forte.state import SessionState
from forte.ui.now_playing import NowPlayingPanel
from forte.ui.playlist_panel import PlaylistPanel
from forte.ui.tray import Tray


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
        self._loaded_path: str | None = None
        self._positions: dict[str, float] = {}
        self._drag_pos: QPoint | None = None
        self._title_buttons: list[QPushButton] = []

        self.repeat: str = session.get("repeat", "off")
        self.shuffle: bool = session.get("shuffle", False)
        self._prev_volume: float = session.get("volume", 1.0)

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
        self._setup_shortcuts()
        self._restore_session()
        self._setup_tray()
        self._start_timers()

        if not self.player.available:
            self._set_status("No audio device — playback disabled")
        else:
            self.player.set_crossfade(session.get("crossfade", 0))
            self.now_playing.set_volume(self._prev_volume)

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

        self.now_playing.play_requested.connect(self._on_play)
        self.now_playing.pause_requested.connect(self._on_pause)
        self.now_playing.next_requested.connect(self._next_track)
        self.now_playing.prev_requested.connect(self._prev_track)
        self.now_playing.seek_offset_requested.connect(self._on_seek_offset)
        self.now_playing.seek_requested.connect(self._on_seek_abs)
        self.now_playing.volume_requested.connect(self._on_volume)
        self.now_playing.mute_requested.connect(self._on_mute)
        self.now_playing.shuffle_toggled.connect(self._on_shuffle)
        self.now_playing.repeat_requested.connect(self._on_repeat_cycle)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Space"), self).activated.connect(self._on_space)
        QShortcut(QKeySequence("Right"), self).activated.connect(self._next_track)
        QShortcut(QKeySequence("Left"), self).activated.connect(self._prev_track)
        QShortcut(QKeySequence("Shift+Right"), self).activated.connect(lambda: self._on_seek_offset(10))
        QShortcut(QKeySequence("Shift+Left"), self).activated.connect(lambda: self._on_seek_offset(-10))
        QShortcut(QKeySequence("M"), self).activated.connect(self._on_mute)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.playlist_panel._add_files)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.playlist_panel.search.setFocus)
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self._quit_app)
        QShortcut(QKeySequence("Delete"), self).activated.connect(self._on_remove_selected)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._save_playlist)

    def _start_timers(self) -> None:
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(200)
        self._progress_timer.timeout.connect(self._update_progress)
        self._progress_timer.start()

        self._event_timer = QTimer(self)
        self._event_timer.setInterval(500)
        self._event_timer.timeout.connect(self._poll_events)
        self._event_timer.start()

    def _index_of(self, filepath: str) -> int:
        for i, track in enumerate(self.playlist):
            if track.filepath == filepath:
                return i
        return -1

    def _restore_session(self) -> None:
        for entry in self.session.get("last_playlist", []):
            if isinstance(entry, str):
                filepath = entry
                position = 0.0
                title = artist = album = ""
                duration = 0.0
            elif isinstance(entry, dict):
                filepath = entry.get("filepath", "")
                position = float(entry.get("position", 0.0) or 0.0)
                title = entry.get("title", "")
                artist = entry.get("artist", "")
                album = entry.get("album", "")
                duration = float(entry.get("duration", 0.0) or 0.0)
            else:
                continue
            if not filepath:
                continue
            self._positions[filepath] = position
            try:
                self.playlist.add_track(filepath)
            except Exception:
                track = TrackMetadata(
                    title=title or Path(filepath).stem,
                    artist=artist,
                    album=album,
                    duration=duration,
                    duration_str=_format_duration(duration),
                    filepath=filepath,
                    album_art=None,
                )
                self.playlist._tracks.append(track)
        self.playlist_panel.model.refresh()
        self.now_playing.set_shuffle(self.shuffle)
        self.now_playing.set_repeat(self.repeat)

        index = self.session.get("last_track_index", -1)
        if 0 <= index < len(self.playlist):
            self._prepare_current(index)

    def _set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _prepare_current(self, index: int) -> None:
        """Load a track into the UI and player without starting playback.

        Used when restoring a session so the Play button can resume from the
        saved position. The scrubber is parked 3s before the saved point.
        """
        if not 0 <= index < len(self.playlist):
            return
        self.current_index = index
        track = self.playlist[index]
        try:
            track = read_metadata(track.filepath)
        except Exception:
            pass
        self.playlist_panel.set_current_track(index)
        self.now_playing.set_track(track)
        self.now_playing.set_duration(track.duration)
        self._loaded_path = track.filepath
        target = 0.0
        if self.player.available:
            try:
                self.player.load(track.filepath)
                saved = self._positions.get(track.filepath, 0.0)
                target = max(0.0, saved - 3.0) if saved > 3.0 else 0.0
                if target > 0:
                    self.player.seek(target)
            except Exception:
                target = 0.0
        self.now_playing.set_position(target)
        self.now_playing.set_playing(False)
        self._set_status(f"Loaded: {track.title} — {track.artist}")
        self._refresh_tray()

    def _play_index(self, index: int, resume: bool = False) -> None:
        if not 0 <= index < len(self.playlist):
            return
        self.current_index = index
        track = self.playlist[index]
        try:
            track = read_metadata(track.filepath)
        except Exception:
            pass
        self.playlist_panel.set_current_track(index)
        self.now_playing.set_track(track)
        self.now_playing.set_duration(track.duration)
        self._set_status(f"Now Playing: {track.title} — {track.artist}")
        self._loaded_path = track.filepath
        if not self.player.available:
            self.now_playing.set_playing(False)
            return
        try:
            self.player.load(track.filepath)
            self.player.play()
            if resume:
                saved = self._positions.get(track.filepath, 0.0)
                if saved > 3.0:
                    target = max(0.0, saved - 3.0)
                    self.player.seek(target)
                    self.now_playing.set_position(target)
            self.now_playing.set_playing(True)
        except Exception:
            self.now_playing.set_playing(False)
        self._refresh_tray()

    def _next_track(self) -> None:
        if len(self.playlist) == 0:
            return
        n = self.current_index + 1
        if n >= len(self.playlist):
            if self.repeat == "all":
                n = 0
            else:
                if self.player.available:
                    self.player.stop()
                self.now_playing.set_playing(False)
                self.now_playing.set_position(0)
                return
        self._play_index(n)

    def _prev_track(self) -> None:
        if len(self.playlist) == 0 or self.current_index < 0:
            return
        if self.player.available and self.player.get_position() < 3:
            if self.current_index > 0:
                self._play_index(self.current_index - 1)
            else:
                self.player.seek(0)
                self.now_playing.set_position(0)
        else:
            if self.player.available:
                self.player.seek(0)
            self.now_playing.set_position(0)

    def _on_track_ended(self) -> None:
        if self.current_index < 0:
            return
        mode = self.repeat
        if mode == "one":
            if self.player.available:
                self.player.seek(0)
                self.player.play()
            self.now_playing.set_playing(True)
        elif mode == "all":
            self._next_track()
        else:
            if self.current_index + 1 < len(self.playlist):
                self._next_track()
            else:
                if self.player.available:
                    self.player.stop()
                self.now_playing.set_playing(False)
                self.now_playing.set_position(0)
        self._refresh_tray()

    def _on_play(self) -> None:
        if not self.playlist:
            return
        if self.current_index < 0 or self.current_index >= len(self.playlist):
            self._play_index(0)
            return
        if self.player.available and self._loaded_path != self.playlist[self.current_index].filepath:
            self._play_index(self.current_index)
            return
        try:
            self.player.play()
            self.now_playing.set_playing(True)
        except Exception:
            self.now_playing.set_playing(False)
        self._refresh_tray()

    def _on_pause(self) -> None:
        if self.player.available:
            self.player.pause()
        self.now_playing.set_playing(False)
        self._refresh_tray()

    def _on_space(self) -> None:
        if self.player.is_playing():
            self._on_pause()
        else:
            self._on_play()

    def _on_seek_offset(self, delta: int) -> None:
        if not self.player.available or self.current_index < 0:
            return
        self.player.seek(max(0.0, self.player.get_position() + delta))
        self.now_playing.set_position(self.player.get_position())

    def _on_seek_abs(self, seconds: float) -> None:
        if not self.player.available or self.current_index < 0:
            return
        self.player.seek(seconds)
        self.now_playing.set_position(seconds)

    def _on_volume(self, value: float) -> None:
        value = max(0.0, min(1.0, value))
        if value > 0:
            self._prev_volume = value
        if self.player.available:
            try:
                self.player.set_volume(value)
            except Exception:
                pass
        self.now_playing.set_volume(value)

    def _on_mute(self) -> None:
        if self.now_playing.get_volume() > 0:
            self._prev_volume = self.now_playing.get_volume()
            self._on_volume(0.0)
        else:
            self._on_volume(self._prev_volume or 1.0)

    def _on_shuffle(self, active: bool) -> None:
        self.shuffle = active
        current = self.playlist[self.current_index].filepath if 0 <= self.current_index < len(self.playlist) else None
        if active:
            self.playlist.shuffle()
        else:
            self.playlist.unshuffle()
        if current:
            self.current_index = self._index_of(current)
        self.playlist_panel.model.refresh()
        self.playlist_panel.set_current_track(self.current_index)
        self.now_playing.set_shuffle(active)
        self.session["shuffle"] = active

    def _on_repeat_cycle(self) -> None:
        order = ["off", "one", "all"]
        self.repeat = order[(order.index(self.repeat) + 1) % 3]
        self.now_playing.set_repeat(self.repeat)
        self.session["repeat"] = self.repeat

    def _on_track_selected(self, index: int) -> None:
        self._play_index(index, resume=True)

    def _on_playlist_changed(self) -> None:
        if len(self.playlist) == 0:
            self._set_status("No track loaded")
            self.current_index = -1
            self._loaded_path = None
        elif self.current_index >= len(self.playlist):
            self.current_index = len(self.playlist) - 1
            self.playlist_panel.set_current_track(self.current_index)

    def _on_remove_selected(self) -> None:
        index = self.playlist_panel.selected_source_row()
        if index is None or not 0 <= index < len(self.playlist):
            return
        was_current = index == self.current_index
        self.playlist_panel.remove_track(index)
        if index < self.current_index:
            self.current_index -= 1
        elif was_current:
            if self.current_index >= len(self.playlist):
                self.current_index = len(self.playlist) - 1
            if self.player.available:
                self.player.stop()
            self.now_playing.set_playing(False)
            self.now_playing.set_position(0)
            self._loaded_path = None
        self.playlist_panel.set_current_track(self.current_index)

    def _on_play_next(self, index: int) -> None:
        if self.current_index < 0 or not 0 <= index < len(self.playlist):
            return
        dest = self.current_index + 1
        if index < dest:
            dest -= 1
        self.playlist.move_track(index, dest)
        self.playlist_panel.model.refresh()
        self.playlist_panel.playlist_changed.emit()

    def _save_playlist(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Playlist", "", "M3U8 (*.m3u8)")
        if path:
            if not path.lower().endswith(".m3u8"):
                path += ".m3u8"
            self.playlist.save_m3u8(path)

    def _update_progress(self) -> None:
        if self.current_index < 0:
            return
        pos = self.player.get_position() if self.player.available else 0.0
        self.now_playing.set_position(pos)
        if self._loaded_path:
            self._positions[self._loaded_path] = pos

    def _poll_events(self) -> None:
        if not self.player.available:
            return
        try:
            for _ in pygame.event.get(TRACK_ENDED):
                self._on_track_ended()
        except pygame.error:
            pass

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = None
            return
        accent = self.theme.get("accent", "#E8A838")
        self.tray = Tray(accent, self)
        self.tray.toggle_requested.connect(self._on_space)
        self.tray.next_requested.connect(self._next_track)
        self.tray.prev_requested.connect(self._prev_track)
        self.tray.restore_requested.connect(self._restore_window)
        self.tray.quit_requested.connect(self._quit_app)
        self.tray.show()
        self._refresh_tray()

    def _refresh_tray(self) -> None:
        if not getattr(self, "tray", None):
            return
        if 0 <= self.current_index < len(self.playlist):
            track = self.playlist[self.current_index]
            symbol = "▶" if self.now_playing._playing else "⏸"
            self.tray.set_now_playing(f"Forte — {symbol} {track.title} — {track.artist}")
        else:
            self.tray.set_now_playing("Forte — no track loaded")

    def _restore_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _minimise(self) -> None:
        if self.session.get("minimise_to_tray", True):
            self.hide()
        else:
            self.showMinimized()

    def _open_settings(self) -> None:
        # Settings dialog is implemented in a later stage.
        pass

    def _quit_app(self) -> None:
        if getattr(self, "tray", None) is not None:
            self.tray.hide()
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
        if getattr(self, "tray", None) is not None:
            self.tray.hide()
        self._save_session()
        event.accept()

    def _save_session(self) -> None:
        data = dict(self.session)
        data["last_playlist"] = [
            {
                "filepath": track.filepath,
                "title": track.title,
                "artist": track.artist,
                "album": track.album,
                "duration": track.duration,
                "position": self._positions.get(track.filepath, 0.0),
            }
            for track in self.playlist
        ]
        data["last_track_index"] = self.current_index
        data["volume"] = self.now_playing.get_volume()
        data["repeat"] = self.repeat
        data["shuffle"] = self.shuffle
        self.state.save(data)
