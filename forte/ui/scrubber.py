from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty, QPropertyAnimation, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtWidgets import QWidget


def _format_time(seconds: float) -> str:
    total = int(max(0.0, seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes}:{secs:02d}"


_SIDE = 48
_LABEL_W = 44


class ScrubberWidget(QWidget):
    """Custom painted progress bar (no QSlider) with hover thumb and seek signals."""

    seek = pyqtSignal(float)

    def __init__(self, theme: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setFixedHeight(48)
        self.setMouseTracking(True)
        self._duration = 0.0
        self._position = 0.0
        self._hovered = False
        self._seeking = False
        self._thumb_opacity = 0.0

        self._anim = QPropertyAnimation(self, b"thumb_opacity")
        self._anim.setDuration(100)

    def get_thumb_opacity(self) -> float:
        return self._thumb_opacity

    def set_thumb_opacity(self, value: float) -> None:
        self._thumb_opacity = value
        self.update()

    thumb_opacity = pyqtProperty(float, get_thumb_opacity, set_thumb_opacity)

    def set_duration(self, seconds: float) -> None:
        self._duration = max(0.0, seconds)
        self.update()

    def set_position(self, seconds: float) -> None:
        self._position = max(0.0, seconds)
        self.update()

    def _ratio(self) -> float:
        if self._duration <= 0:
            return 0.0
        return min(1.0, max(0.0, self._position / self._duration))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        centre_y = height / 2
        track_h = 3
        track_top = centre_y - track_h / 2

        bar_x0 = _SIDE
        bar_w = max(1, width - 2 * _SIDE)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.theme["bg_scrubber"]))
        painter.drawRoundedRect(QRectF(bar_x0, track_top, bar_w, track_h), 1.5, 1.5)

        ratio = self._ratio()
        if self._duration > 0:
            prog = max(track_h, ratio * bar_w)
            fill = QColor(self.theme["accent"])
            fill.setAlphaF(0.6)
            painter.setBrush(fill)
            painter.drawRoundedRect(QRectF(bar_x0, track_top, prog, track_h), 1.5, 1.5)

        if self._hovered or self._seeking:
            thumb = QColor(self.theme["accent"])
            thumb.setAlphaF(1.0 if self._seeking else self._thumb_opacity)
            painter.setBrush(thumb)
            cx = int(bar_x0 + ratio * bar_w) if self._duration > 0 else bar_x0
            cy = int(centre_y)
            painter.drawEllipse(cx - 5, cy - 5, 10, 10)

        painter.setPen(QColor(self.theme["text_secondary"]))
        painter.setFont(QFont("monospace", 11))
        painter.drawText(0, 0, _LABEL_W, height, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, _format_time(self._position))
        painter.drawText(width - _LABEL_W, 0, _LABEL_W, height, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, _format_time(self._duration))

    def _seek_to(self, x: int) -> None:
        if self._duration <= 0:
            return
        ratio = (x - _SIDE) / max(1, self.width() - 2 * _SIDE)
        ratio = min(1.0, max(0.0, ratio))
        seconds = ratio * self._duration
        self.seek.emit(seconds)
        self.set_position(seconds)

    def mousePressEvent(self, event) -> None:
        self._seeking = True
        self._seek_to(int(event.position().x()))
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._seeking:
            self._seek_to(int(event.position().x()))
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._seeking = False
        event.accept()

    def enterEvent(self, event) -> None:
        self._hovered = True
        self._anim.stop()
        self._anim.setStartValue(self._thumb_opacity)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self.update()

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._anim.stop()
        self._anim.setStartValue(self._thumb_opacity)
        self._anim.setEndValue(0.0)
        self._anim.start()
        self.update()
