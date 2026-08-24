from __future__ import annotations

import time
from pathlib import Path

import pygame
import mutagen

TRACK_ENDED = pygame.USEREVENT + 1

_SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a"}


class Player:
    """Audio playback engine built on pygame.mixer.

    Tracks playback position with a monotonic wall-clock model so that
    pause/resume and seek behave consistently across all supported formats.
    Emits a ``TRACK_ENDED`` (``pygame.USEREVENT + 1``) event when a track
    finishes playback naturally.
    """

    def __init__(self) -> None:
        self._ready = False
        self._error = ""
        try:
            pygame.init()
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            pygame.mixer.music.set_endevent(TRACK_ENDED)
            self._ready = True
        except pygame.error as exc:
            self._error = str(exc)

        self._filepath: str | None = None
        self.duration: float = 0.0

        self._state: str = "stopped"
        self._accumulated: float = 0.0
        self._start_offset: float = 0.0
        self._play_start: float = 0.0
        self._volume: float = 1.0

    @property
    def available(self) -> bool:
        """True when the pygame.mixer audio backend initialised successfully."""
        return self._ready

    def _require_ready(self) -> None:
        if not self._ready:
            raise RuntimeError(f"Audio output unavailable: {self._error or 'mixer not initialised'}")

    def _check_format(self, filepath: str) -> None:
        ext = Path(filepath).suffix.lower()
        if ext not in _SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported audio format for {Path(filepath).name}: '{ext or 'no extension'}'"
            )

    def _arm_endevent(self) -> None:
        pygame.mixer.music.set_endevent(TRACK_ENDED)

    def _disarm_endevent(self) -> None:
        pygame.mixer.music.set_endevent(pygame.NOEVENT)

    def load(self, filepath: str) -> None:
        self._require_ready()
        self._check_format(filepath)
        path = Path(filepath)
        if not path.is_file():
            raise ValueError(f"Audio file not found: {filepath}")

        audio = mutagen.File(str(path))
        if audio is None or audio.info is None:
            raise ValueError(f"Could not read audio data from: {filepath}")

        self._filepath = str(path)
        self.duration = float(audio.info.length)

        self.stop()
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(self._volume)

    def play(self) -> None:
        self._require_ready()
        if self._filepath is None:
            raise ValueError("No track loaded; call load() before play()")
        self._accumulated = self._start_offset
        self._play_start = time.perf_counter()
        self._disarm_endevent()
        pygame.mixer.music.play(start=self._start_offset)
        self._arm_endevent()
        self._state = "playing"

    def pause(self) -> None:
        self._require_ready()
        if self._state != "playing":
            return
        self._accumulated += time.perf_counter() - self._play_start
        pygame.mixer.music.pause()
        self._state = "paused"

    def resume(self) -> None:
        self._require_ready()
        if self._state != "paused":
            return
        self._disarm_endevent()
        pygame.mixer.music.unpause()
        self._arm_endevent()
        self._play_start = time.perf_counter()
        self._state = "playing"

    def stop(self) -> None:
        self._require_ready()
        self._disarm_endevent()
        pygame.mixer.music.stop()
        self._state = "stopped"
        self._accumulated = 0.0
        self._start_offset = 0.0

    def seek(self, seconds: float) -> None:
        self._require_ready()
        if self._filepath is None:
            raise ValueError("No track loaded; call load() before seek()")
        seconds = max(0.0, float(seconds))
        was_playing = self._state == "playing"

        self._accumulated = seconds
        self._start_offset = seconds

        self._disarm_endevent()
        pygame.mixer.music.stop()
        pygame.mixer.music.load(self._filepath)
        pygame.mixer.music.play(start=seconds)
        self._arm_endevent()
        try:
            pygame.mixer.music.set_pos(seconds)
        except pygame.error:
            pass

        if was_playing:
            self._play_start = time.perf_counter()
            self._state = "playing"
        else:
            self._state = "paused"
            pygame.mixer.music.pause()
            self._accumulated = seconds

    def get_position(self) -> float:
        match self._state:
            case "playing":
                return self._accumulated + (time.perf_counter() - self._play_start)
            case "paused":
                return self._accumulated
            case _:
                return 0.0

    def set_volume(self, value: float) -> None:
        self._require_ready()
        self._volume = max(0.0, min(1.0, float(value)))
        pygame.mixer.music.set_volume(self._volume)

    def is_playing(self) -> bool:
        return self._state == "playing"

    def is_paused(self) -> bool:
        return self._state == "paused"
