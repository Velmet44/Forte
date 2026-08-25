from __future__ import annotations

import hashlib
import math
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty, QPropertyAnimation, QSize, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QLinearGradient,
    QPainterPath,
    QPixmap,
    QImage,
    QPolygonF,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
)

from forte.metadata import TrackMetadata
from forte.ui.scrubber import ScrubberWidget

# Fixed 8-pair palette for generated placeholder art. These are generative-art
# colours (not UI chrome), mandated by the spec, so they live here as constants.
_ART_PALETTE: list[list[str]] = [
    ["#E8A838", "#C48A22"],
    ["#E76F51", "#F4A261"],
    ["#2A9D8F", "#264653"],
    ["#5E60CE", "#6930C3"],
    ["#EF476F", "#FFD166"],
    ["#06D6A0", "#118AB2"],
    ["#F15BB5", "#9B5DE5"],
    ["#FF7B00", "#FFB700"],
]

PLAY = "play"
PAUSE = "pause"
PREV = "prev"
NEXT = "next"
BACK10 = "back10"
FWD10 = "fwd10"
SHUFFLE = "shuffle"
REPEAT = "repeat"
REPEAT_ONE = "repeat_one"
VOL_HIGH = "vol_high"
VOL_LOW = "vol_low"
VOL_MUTE = "vol_mute"


class IconButton(QPushButton):
    """QPushButton that paints its icon with QPainter for cross-platform consistency."""

    def __init__(
        self,
        icon: str,
        size: int,
        theme: dict,
        variant: str = "default",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon = icon
        self._size = size
        self._theme = theme
        self._variant = variant
        self._active = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def set_active(self, active: bool) -> None:
        self._active = bool(active)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        hover = self.underMouse() or self.isDown()
        theme = self._theme

        if self._variant == "play":
            bg = theme["accent"] if not hover else theme["accent_dim"]
            painter.setBrush(QColor(bg))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect.adjusted(2, 2, -2, -2))
            self._draw_icon(painter, rect, "#FFFFFF")
        else:
            if self._variant == "toggle" and self._active:
                colour = theme["accent"]
            elif hover:
                colour = theme["text_primary"]
            else:
                colour = theme["text_secondary"]
            self._draw_icon(painter, rect, colour)

    def _draw_icon(self, painter: QPainter, rect, colour: str) -> None:
        s = min(rect.width(), rect.height())
        cx = rect.center().x()
        cy = rect.center().y()
        pen = QPen(QColor(colour))
        pen.setWidthF(max(1.5, s * 0.06))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        fill = QBrush(QColor(colour))

        if self._icon in (PLAY,):
            poly = QPolygonF([
                QPointF(cx - s * 0.16, cy - s * 0.22),
                QPointF(cx + s * 0.22, cy),
                QPointF(cx - s * 0.16, cy + s * 0.22),
            ])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawPolygon(poly)

        elif self._icon in (PAUSE,):
            bw = s * 0.09
            gap = s * 0.05
            h = s * 0.40
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawRect(QRectF(cx - gap / 2 - bw, cy - h / 2, bw, h))
            painter.drawRect(QRectF(cx + gap / 2, cy - h / 2, bw, h))

        elif self._icon == PREV:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawRect(QRectF(cx - s * 0.20, cy - s * 0.18, s * 0.06, s * 0.36))
            poly = QPolygonF([
                QPointF(cx + s * 0.14, cy - s * 0.18),
                QPointF(cx - s * 0.02, cy),
                QPointF(cx + s * 0.14, cy + s * 0.18),
            ])
            painter.drawPolygon(poly)

        elif self._icon == NEXT:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawRect(QRectF(cx + s * 0.14, cy - s * 0.18, s * 0.06, s * 0.36))
            poly = QPolygonF([
                QPointF(cx - s * 0.14, cy - s * 0.18),
                QPointF(cx + s * 0.02, cy),
                QPointF(cx - s * 0.14, cy + s * 0.18),
            ])
            painter.drawPolygon(poly)

        elif self._icon == BACK10:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            ax0 = cx - s * 0.30
            ax1 = cx - s * 0.10
            poly = QPolygonF([
                QPointF(ax0, cy),
                QPointF(ax1, cy - s * 0.18),
                QPointF(ax1, cy + s * 0.18),
            ])
            painter.drawPolygon(poly)
            painter.setPen(pen)
            painter.setFont(QFont("Inter", int(s * 0.20), QFont.Weight.Bold))
            painter.drawText(
                QRectF(cx + s * 0.08, cy - s * 0.22, s * 0.30, s * 0.44),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                "10",
            )

        elif self._icon == FWD10:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            ax0 = cx + s * 0.30
            ax1 = cx + s * 0.10
            poly = QPolygonF([
                QPointF(ax0, cy),
                QPointF(ax1, cy - s * 0.18),
                QPointF(ax1, cy + s * 0.18),
            ])
            painter.drawPolygon(poly)
            painter.setPen(pen)
            painter.setFont(QFont("Inter", int(s * 0.20), QFont.Weight.Bold))
            painter.drawText(
                QRectF(cx - s * 0.38, cy - s * 0.22, s * 0.30, s * 0.44),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                "10",
            )

        elif self._icon == SHUFFLE:
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            x0 = cx - s * 0.27
            x1 = cx + s * 0.27
            y0 = cy - s * 0.16
            y1 = cy + s * 0.16
            # two arrows crossing, both pointing right
            painter.drawLine(QPointF(x0, y0), QPointF(x1, y1))
            painter.drawLine(QPointF(x0, y1), QPointF(x1, y0))
            self._arrow_head(painter, x1, y1, 45, s * 0.12, fill)
            self._arrow_head(painter, x1, y0, -45, s * 0.12, fill)

        elif self._icon in (REPEAT, REPEAT_ONE):
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = s * 0.28
            start = 290
            sweep = 320
            painter.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), int(start * 16), int(sweep * 16))
            a_rad = math.radians(start)
            px = cx + r * math.cos(a_rad)
            py = cy + r * math.sin(a_rad)
            dx = -math.sin(a_rad)
            dy = math.cos(a_rad)
            ang = math.degrees(math.atan2(dy, dx))
            self._arrow_head(painter, px, py, ang, s * 0.12, fill)
            if self._icon == REPEAT_ONE:
                painter.setPen(pen)
                painter.setFont(QFont("Inter", int(s * 0.24), QFont.Weight.Bold))
                painter.drawText(
                    QRectF(cx - r, cy - r, r * 2, r * 2),
                    Qt.AlignmentFlag.AlignCenter,
                    "1",
                )

        elif self._icon in (VOL_HIGH, VOL_LOW, VOL_MUTE):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawRect(QRectF(cx - s * 0.24, cy - s * 0.05, s * 0.05, s * 0.10))
            painter.drawPolygon(QPolygonF([
                QPointF(cx - s * 0.19, cy - s * 0.05),
                QPointF(cx - s * 0.05, cy - s * 0.16),
                QPointF(cx - s * 0.05, cy + s * 0.16),
                QPointF(cx - s * 0.19, cy + s * 0.05),
            ]))
            if self._icon == VOL_MUTE:
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(cx + s * 0.04, cy - s * 0.13), QPointF(cx + s * 0.22, cy + s * 0.13))
                painter.drawLine(QPointF(cx + s * 0.22, cy - s * 0.13), QPointF(cx + s * 0.04, cy + s * 0.13))
            else:
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                w1, h1 = s * 0.11, s * 0.11
                painter.drawArc(QRectF(cx - s * 0.05 - w1, cy - h1, w1 * 2, h1 * 2), int(315 * 16), int(90 * 16))
                if self._icon == VOL_HIGH:
                    w2, h2 = s * 0.21, s * 0.21
                    painter.drawArc(QRectF(cx - s * 0.05 - w2, cy - h2, w2 * 2, h2 * 2), int(320 * 16), int(80 * 16))

    def _arrow_head(self, painter, x, y, angle_deg, size, brush) -> None:
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle_deg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(brush)
        a = size
        painter.drawPolygon(QPolygonF([
            QPointF(0, 0),
            QPointF(-a, -a * 0.6),
            QPointF(-a, a * 0.6),
        ]))
        painter.restore()


class AlbumArtLabel(QLabel):
    """220×220 label that paints a rounded album cover with a fade-in opacity."""

    def __init__(self, theme: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setFixedSize(220, 220)
        self._pixmap: QPixmap | None = None
        self._opacity = 1.0
        self._anim = QPropertyAnimation(self, b"art_opacity")
        self._anim.setDuration(200)

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, value: float) -> None:
        self._opacity = value
        self.update()

    art_opacity = pyqtProperty(float, get_opacity, set_opacity)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._pixmap is None:
            return
        painter.setOpacity(self._opacity)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        painter.setClipPath(path)
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (self.width() - scaled.width()) / 2
        y = (self.height() - scaled.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled)


def _placeholder_art(title: str) -> QPixmap:
    seed = int(hashlib.sha256(title.encode("utf-8")).hexdigest(), 16)
    pair = _ART_PALETTE[seed % len(_ART_PALETTE)]
    size = 220
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0, QColor(pair[0]))
    gradient.setColorAt(1, QColor(pair[1]))
    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRect(0, 0, size, size)
    letter = (title.strip()[:1] or "?").upper()
    painter.setPen(QColor("#FFFFFF"))
    painter.setFont(QFont("Inter", 80, QFont.Weight.Bold))
    painter.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, letter)
    painter.end()
    return pixmap


def _load_art(track: TrackMetadata) -> QPixmap:
    if track.album_art:
        image = QImage.fromData(track.album_art)
        if not image.isNull():
            return QPixmap.fromImage(image)
    return _placeholder_art(track.title)


class NowPlayingPanel(QWidget):
    """Right-hand panel: album art, metadata, scrubber and transport controls."""

    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    seek_offset_requested = pyqtSignal(int)
    seek_requested = pyqtSignal(float)
    volume_requested = pyqtSignal(float)
    mute_requested = pyqtSignal()
    shuffle_toggled = pyqtSignal(bool)
    repeat_requested = pyqtSignal()

    def __init__(self, theme: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self._playing = False
        self._volume = 1.0
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top = QWidget()
        top.setFixedHeight(300)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(24, 0, 24, 0)
        top_layout.setSpacing(24)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._art = AlbumArtLabel(self.theme)
        top_layout.addWidget(self._art)

        info = QWidget()
        info.setMaximumWidth(300)
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(6)

        self._title = QLabel("Track Title")
        self._title.setObjectName("nowTitle")
        self._title.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        self._title.setTextFormat(Qt.TextFormat.PlainText)

        self._artist = QLabel("Artist")
        self._artist.setObjectName("nowArtist")
        self._artist.setFont(QFont("Inter", 13))

        self._album = QLabel("Album · Year")
        self._album.setObjectName("nowAlbum")
        self._album.setFont(QFont("Inter", 12))

        info_layout.addStretch(1)
        info_layout.addWidget(self._title)
        info_layout.addWidget(self._artist)
        info_layout.addWidget(self._album)
        info_layout.addStretch(1)

        top_layout.addWidget(info)
        top_layout.addStretch(1)
        layout.addWidget(top)

        self._scrubber = ScrubberWidget(self.theme)
        self._scrubber.seek.connect(self.seek_requested)
        layout.addWidget(self._scrubber)

        self._build_controls()
        layout.addWidget(self._controls)
        layout.addStretch(1)

    def _build_controls(self) -> None:
        self._controls = QWidget()
        self._controls.setFixedHeight(72)
        layout = QHBoxLayout(self._controls)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._prev = IconButton(PREV, 36, self.theme)
        self._back10 = IconButton(BACK10, 36, self.theme)
        self._play = IconButton(PLAY, 48, self.theme, variant="play")
        self._fwd10 = IconButton(FWD10, 36, self.theme)
        self._next = IconButton(NEXT, 36, self.theme)

        self._prev.setToolTip("Previous track")
        self._back10.setToolTip("Back 10 seconds")
        self._play.setToolTip("Play")
        self._fwd10.setToolTip("Forward 10 seconds")
        self._next.setToolTip("Next track")

        self._prev.clicked.connect(self.prev_requested)
        self._back10.clicked.connect(lambda: self.seek_offset_requested.emit(-10))
        self._play.clicked.connect(self._on_play_toggle)
        self._fwd10.clicked.connect(lambda: self.seek_offset_requested.emit(10))
        self._next.clicked.connect(self.next_requested)

        layout.addWidget(self._prev)
        layout.addWidget(self._back10)
        layout.addWidget(self._play)
        layout.addWidget(self._fwd10)
        layout.addWidget(self._next)

        layout.addSpacing(28)
        self._shuffle = IconButton(SHUFFLE, 28, self.theme, variant="toggle")
        self._repeat = IconButton(REPEAT, 28, self.theme, variant="toggle")
        self._shuffle.setToolTip("Shuffle")
        self._repeat.setToolTip("Repeat")
        self._shuffle.clicked.connect(lambda: self.shuffle_toggled.emit(not self._shuffle._active))
        self._repeat.clicked.connect(self.repeat_requested)
        layout.addWidget(self._shuffle)
        layout.addWidget(self._repeat)

        layout.addSpacing(28)
        self._volume_icon = IconButton(VOL_HIGH, 20, self.theme)
        self._volume_icon.setToolTip("Mute")
        self._volume_icon.clicked.connect(self.mute_requested)
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setObjectName("volumeSlider")
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setFixedWidth(80)
        self._volume_slider.setValue(100)
        self._volume_slider.setToolTip("Volume")
        self._volume_slider.valueChanged.connect(lambda v: self.volume_requested.emit(v / 100.0))
        layout.addWidget(self._volume_icon)
        layout.addWidget(self._volume_slider)

    def _on_play_toggle(self) -> None:
        if self._playing:
            self.pause_requested.emit()
        else:
            self.play_requested.emit()

    def set_track(self, track: TrackMetadata) -> None:
        self._art.set_opacity(0.0)
        self._art.set_pixmap(_load_art(track))
        self._anim = self._art._anim
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

        self._title.setText(track.title)
        self._artist.setText(track.artist)
        album = track.album
        year = ""
        if track.filepath:
            try:
                from mutagen import File as _Mut
                meta = _Mut(track.filepath)
                year = _year_from_meta(meta)
            except Exception:
                year = ""
        self._album.setText(f"{album}{(' · ' + year) if year else ''}")

    def set_duration(self, seconds: float) -> None:
        self._scrubber.set_duration(seconds)

    def set_position(self, seconds: float) -> None:
        self._scrubber.set_position(seconds)

    def set_playing(self, playing: bool) -> None:
        self._playing = bool(playing)
        self._play._icon = PAUSE if self._playing else PLAY
        self._play.setToolTip("Pause" if self._playing else "Play")
        self._play.update()

    def set_volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, value))
        self._volume_slider.setValue(int(self._volume * 100))
        icon = VOL_MUTE if self._volume == 0 else (VOL_LOW if self._volume <= 0.5 else VOL_HIGH)
        self._volume_icon._icon = icon
        self._volume_icon.setToolTip("Unmute" if self._volume == 0 else "Mute")
        self._volume_icon.update()

    def set_shuffle(self, active: bool) -> None:
        self._shuffle.set_active(active)
        self._shuffle.setToolTip("Shuffle on" if active else "Shuffle")

    def set_repeat(self, mode: str) -> None:
        self._repeat.set_active(mode != "off")
        self._repeat._icon = REPEAT_ONE if mode == "one" else REPEAT
        self._repeat.setToolTip(
            "Repeat one" if mode == "one" else ("Repeat all" if mode == "all" else "Repeat")
        )
        self._repeat.update()

    def get_volume(self) -> float:
        return self._volume


def _year_from_meta(meta) -> str:
    try:
        if hasattr(meta, "tags") and meta.tags is not None:
            for key in ("TDRC", "TYER", "date"):
                val = meta.tags.get(key)
                if val:
                    text = str(val)
                    digits = "".join(ch for ch in text if ch.isdigit())
                    if len(digits) >= 4:
                        return digits[:4]
            if hasattr(meta, "info") and getattr(meta.info, "year", None):
                return str(meta.info.year)
        if getattr(meta, "year", None):
            return str(meta.year)
    except Exception:
        return ""
    return ""
