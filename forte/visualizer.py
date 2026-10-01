from __future__ import annotations

import hashlib
import math
import random
from pathlib import Path

try:
    import numpy as np

    _HAS_NUMPY = True
except Exception:  # pragma: no cover - exercised only when numpy is absent
    np = None
    _HAS_NUMPY = False

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal

try:
    import pygame
    import pygame.sndarray as _sndarray

    _HAS_SNDARRAY = True
except Exception:  # pragma: no cover - pygame is a hard dependency, but guard anyway
    _HAS_SNDARRAY = False

_N_BANDS = 40
_FPS = 60
_DECAY = 0.9
_POS_EASE = 0.25
_BAR_SMOOTH = 0.6


def _source_capability() -> str:
    """Return the best available sample source: 'samples', 'fake'."""
    if _HAS_NUMPY and _HAS_SNDARRAY:
        return "samples"
    return "fake"


class VisualizerEngine(QObject):
    """Real-time frequency-band visualizer running off the GUI thread.

    The engine analyses a loaded track's PCM samples once (in its worker
    thread) into a precomputed array of 40-band energies, then emits those
    40 normalised values (0.0-1.0) in sync with the reported playback position.
    When numpy or the sample decoder is unavailable it falls back to a seeded,
    animated fake generator so the bars always move.
    """

    bars_ready = pyqtSignal(list)

    # Slots driven from the GUI thread; queued into the worker thread.
    request_track = pyqtSignal(str, float)
    request_position = pyqtSignal(float)
    request_playing = pyqtSignal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._bars = [0.0] * _N_BANDS
        self._position = 0.0
        self._display_position = 0.0
        self._duration = 0.0
        self._playing = False
        self._settled = True
        self._source: object | None = None  # numpy (frames, bands) when available
        self._num_frames = 0
        self._fake_rng = random.Random(0)
        self._fake_phase = 0.0

        self.request_track.connect(self._on_track)
        self.request_position.connect(self._on_position)
        self.request_playing.connect(self._on_playing)

        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._on_started)
        self._thread.finished.connect(self._on_finished)
        self._thread.start()

    def _on_started(self) -> None:
        self._timer = QTimer()
        self._timer.setInterval(int(1000 / _FPS))
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _on_finished(self) -> None:
        if getattr(self, "_timer", None) is not None:
            self._timer.stop()

    def stop(self) -> None:
        self._thread.quit()
        self._thread.wait()

    # --- incoming state (runs in worker thread via queued signals) ---

    def _on_track(self, filepath: str, duration: float) -> None:
        self._duration = max(0.0, duration)
        self._position = 0.0
        self._display_position = 0.0
        self._source = None
        self._num_frames = 0
        self._fake_rng = random.Random(self._hash_seed(filepath))
        self._fake_phase = 0.0

        if _source_capability() == "samples":
            samples = self._read_samples(filepath)
            if samples is not None:
                self._source = self._analyse(samples)
                if self._source is not None:
                    self._num_frames = self._source.shape[0]
        if self._source is None:
            if not _HAS_NUMPY:
                print("[forte.visualizer] numpy unavailable - using animated fake visualizer")
            else:
                print("[forte.visualizer] could not decode samples - using animated fake visualizer")

    def _on_position(self, seconds: float) -> None:
        self._position = max(0.0, seconds)

    def _on_playing(self, playing: bool) -> None:
        self._playing = bool(playing)

    # --- helpers ---

    @staticmethod
    def _hash_seed(filepath: str) -> int:
        return int(hashlib.sha256(filepath.encode("utf-8")).hexdigest(), 16)

    def _read_samples(self, filepath: str):
        if not _HAS_SNDARRAY:
            return None
        try:
            pygame.mixer.init()
            sound = pygame.mixer.Sound(filepath)
            arr = _sndarray.array(sound)
            sr = pygame.mixer.get_init()[0]
        except Exception:
            return None
        try:
            arr = arr.astype(np.float32)
            if arr.ndim > 1:
                arr = arr.mean(axis=1)
            peak = float(np.max(np.abs(arr))) if arr.size else 0.0
            if peak > 0.0:
                arr = arr / peak
            return arr, int(sr)
        except Exception:
            return None

    def _analyse(self, samples):
        samples, sr = samples
        n = samples.size
        if n == 0 or sr <= 0:
            return None
        hop = max(1, sr // _FPS)
        win = hop
        nf = max(1, n // hop)
        freqs = np.fft.rfftfreq(win, d=1.0 / sr)
        top = min(sr / 2.0, 20000.0)
        edges = np.logspace(math.log10(20.0), math.log10(top), _N_BANDS + 1)
        band_masks = [
            np.where((freqs >= edges[i]) & (freqs < edges[i + 1]))[0]
            for i in range(_N_BANDS)
        ]
        window = np.hanning(win)
        out = np.zeros((nf, _N_BANDS), dtype=np.float32)
        for f in range(nf):
            seg = samples[f * hop : f * hop + win]
            if seg.size < win:
                seg = np.pad(seg, (0, win - seg.size))
            spec = np.abs(np.fft.rfft(seg * window))
            for b in range(_N_BANDS):
                idx = band_masks[b]
                if idx.size:
                    out[f, b] = float(np.sqrt(np.mean(spec[idx] ** 2)))
        for b in range(_N_BANDS):
            peak = float(out[:, b].max())
            if peak > 0.0:
                out[:, b] /= peak
        return out

    def _fake_bars(self) -> list[float]:
        self._fake_phase += 1.0 / _FPS
        vals: list[float] = []
        for i in range(_N_BANDS):
            frac = i / (_N_BANDS - 1)
            envelope = math.exp(-((frac - 0.5) ** 2) / 0.08)
            base = 0.25 + 0.75 * envelope
            osc = 0.5 + 0.5 * math.sin(self._fake_phase * (2.0 + i * 0.25) + i)
            noise = self._fake_rng.random()
            v = base * (0.45 + 0.55 * osc) * (0.55 + 0.45 * noise)
            vals.append(max(0.0, min(1.0, v)))
        return vals

    # --- per-frame tick ---

    def _tick(self) -> None:
        if not self._playing:
            if self._settled:
                return
            moving = False
            for i in range(_N_BANDS):
                self._bars[i] *= _DECAY
                if self._bars[i] >= 0.01:
                    moving = True
            self.bars_ready.emit(list(self._bars))
            if not moving:
                self._bars = [0.0] * _N_BANDS
                self._settled = True
            return

        self._settled = False
        if self._source is not None and self._duration > 0 and self._num_frames > 0:
            # Ease the displayed position toward the (less frequently reported)
            # real position so bars glide instead of stepping every 200ms.
            self._display_position += (self._position - self._display_position) * _POS_EASE
            fpos = self._display_position / self._duration * (self._num_frames - 1)
            fpos = max(0.0, min(fpos, self._num_frames - 1))
            i0 = int(fpos)
            i1 = min(i0 + 1, self._num_frames - 1)
            frac = fpos - i0
            a = self._source[i0]
            b = self._source[i1]
            target = [float(a[k]) + (float(b[k]) - float(a[k])) * frac for k in range(_N_BANDS)]
        else:
            target = self._fake_bars()
        self._bars = [self._bars[i] * (1.0 - _BAR_SMOOTH) + target[i] * _BAR_SMOOTH for i in range(_N_BANDS)]
        self.bars_ready.emit(list(self._bars))
