from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from forte.metadata import TrackMetadata


class NowPlayingPanel(QWidget):
    """Right-hand panel showing album art, metadata, scrubber and transport.

    This stage only builds the layout skeleton with placeholder labels; the
    real art/scrubber/controls are wired in Stage 3.
    """

    def __init__(self, theme: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("nowPlaying")
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        meta = QWidget()
        meta.setFixedHeight(300)
        meta_layout = QVBoxLayout(meta)
        meta_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._art = QLabel("Album Art Here")
        self._art.setObjectName("artPlaceholder")
        self._art.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._title = QLabel("Track Title")
        self._title.setObjectName("nowTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._subtitle = QLabel("Artist · Album")
        self._subtitle.setObjectName("nowSub")
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        meta_layout.addStretch(1)
        meta_layout.addWidget(self._art, alignment=Qt.AlignmentFlag.AlignHCenter)
        meta_layout.addSpacing(12)
        meta_layout.addWidget(self._title, alignment=Qt.AlignmentFlag.AlignHCenter)
        meta_layout.addWidget(self._subtitle, alignment=Qt.AlignmentFlag.AlignHCenter)
        meta_layout.addStretch(1)

        scrubber = QWidget()
        scrubber.setFixedHeight(60)
        scrubber.setObjectName("scrubberPlaceholder")

        controls = QWidget()
        controls.setFixedHeight(72)
        controls.setObjectName("controlsPlaceholder")

        layout.addWidget(meta)
        layout.addWidget(scrubber)
        layout.addWidget(controls)
        layout.addStretch(1)

    def set_track(self, track: TrackMetadata) -> None:
        """Update the placeholder labels with the given track's metadata."""
        self._title.setText(track.title)
        self._subtitle.setText(f"{track.artist} · {track.album}")
