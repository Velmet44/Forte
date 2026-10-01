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
    finishes playback naturally (music backend).

    When a crossfade duration greater than zero is configured and a track is
    already playing, advancing to the next track overlaps the outgoing stream
    with the incoming one: the old stream fades out while the new track fades
    in on a free :class:`pygame.mixer.Channel`. The channel becomes the active
    stream until the next seek/pause-resume hands control back to the music
    backend, so the rest of the app keeps working unchanged.
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
        self._crossfade: float = 0.0

        self._use_channel: bool = False
        self._channel = None
        self._channel_sound = None
        self._ended_flag: bool = False

    @property
    def available(self) -> bool:
        """True when the pygame.mixer audio backend initialised successfully."""
        return self._ready

    @property
    def using_channel(self) -> bool:
        """True while the active stream is a crossfade Channel (not music)."""
        return self._use_channel

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

    def _active_channel(self):
        return self._use_channel and self._channel is not None

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
        self._use_channel = False

    def play(self) -> None:
        self._require_ready()
        if self._filepath is None:
            raise ValueError("No track loaded; call load() before play()")

        if self._active_channel():
            if self._state == "playing":
                return
            # Resume a paused channel stream by handing control to the music
            # backend at the paused position (channels cannot seek).
            self._handoff_channel_to_music(self._accumulated)
            return

        self._accumulated = self._start_offset
        self._play_start = time.perf_counter()
        self._disarm_endevent()
        fade_ms = int(self._crossfade * 1000)
        if fade_ms > 0:
            pygame.mixer.music.play(start=self._start_offset, fade_ms=fade_ms)
        else:
            pygame.mixer.music.play(start=self._start_offset)
        self._arm_endevent()
        self._state = "playing"
        self._ended_flag = False

    def crossfade_play(self, filepath: str) -> None:
        """Load and start ``filepath``, overlapping the current stream.

        Used when advancing to the next track with a non-zero crossfade. The
        outgoing stream fades out while the new track fades in on a Channel.
        """
        self._require_ready()
        self._check_format(filepath)
        path = Path(filepath)
        if not path.is_file():
            raise ValueError(f"Audio file not found: {filepath}")

        audio = mutagen.File(str(path))
        if audio is None or audio.info is None:
            raise ValueError(f"Could not read audio data from: {filepath}")

        ms = int(self._crossfade * 1000)
        if self._active_channel():
            try:
                self._channel.fadeout(ms)
            except Exception:
                pass
        elif self._state == "playing":
            self._disarm_endevent()
            try:
                pygame.mixer.music.fadeout(ms)
            except Exception:
                pass

        try:
            sound = pygame.mixer.Sound(str(path))
            channel = pygame.mixer.find_channel()
        except Exception:
            sound = None
            channel = None

        if channel is None or sound is None:
            # No channel available — fall back to the music backend.
            self._use_channel = False
            self._filepath = str(path)
            self.duration = float(audio.info.length)
            self.stop()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self._volume)
            self._accumulated = 0.0
            self._start_offset = 0.0
            self._play_start = time.perf_counter()
            self._disarm_endevent()
            pygame.mixer.music.play(start=0)
            self._arm_endevent()
            self._state = "playing"
            self._ended_flag = False
            return

        channel.set_volume(self._volume)
        channel.play(sound, fade_ms=ms)
        self._channel = channel
        self._channel_sound = sound
        self._use_channel = True
        self._filepath = str(path)
        self.duration = float(audio.info.length)
        self._start_offset = 0.0
        self._accumulated = 0.0
        self._play_start = time.perf_counter()
        self._state = "playing"
        self._ended_flag = False

    def _handoff_channel_to_music(self, offset: float) -> None:
        offset = max(0.0, float(offset))
        if self._channel is not None:
            try:
                self._channel.stop()
            except Exception:
                pass
        self._channel = None
        self._channel_sound = None
        self._use_channel = False
        self._accumulated = offset
        self._start_offset = offset
        self._disarm_endevent()
        pygame.mixer.music.load(self._filepath)
        pygame.mixer.music.set_volume(self._volume)
        pygame.mixer.music.play(start=offset)
        self._arm_endevent()
        self._play_start = time.perf_counter()
        self._state = "playing"
        self._ended_flag = False

    def set_crossfade(self, seconds: float) -> None:
        """Set the crossfade duration (seconds) used for track transitions."""
        self._crossfade = max(0.0, min(10.0, float(seconds)))

    def pause(self) -> None:
        self._require_ready()
        if self._state != "playing":
            return
        self._accumulated += time.perf_counter() - self._play_start
        if self._active_channel():
            try:
                self._channel.pause()
            except Exception:
                pass
        else:
            pygame.mixer.music.pause()
        self._state = "paused"

    def resume(self) -> None:
        self._require_ready()
        if self._state != "paused":
            return
        if self._active_channel():
            try:
                self._channel.resume()
            except Exception:
                pass
        else:
            self._disarm_endevent()
            pygame.mixer.music.unpause()
            self._arm_endevent()
        self._play_start = time.perf_counter()
        self._state = "playing"

    def stop(self) -> None:
        self._require_ready()
        self._disarm_endevent()
        pygame.mixer.music.stop()
        if self._channel is not None:
            try:
                self._channel.stop()
            except Exception:
                pass
        self._channel = None
        self._channel_sound = None
        self._use_channel = False
        self._state = "stopped"
        self._accumulated = 0.0
        self._start_offset = 0.0
        self._ended_flag = False

    def seek(self, seconds: float) -> None:
        self._require_ready()
        if self._filepath is None:
            raise ValueError("No track loaded; call load() before seek()")
        seconds = max(0.0, float(seconds))
        was_playing = self._state == "playing"

        if self._active_channel():
            if self._channel is not None:
                try:
                    self._channel.stop()
                except Exception:
                    pass
            self._channel = None
            self._channel_sound = None
            self._use_channel = False

        self._accumulated = seconds
        self._start_offset = seconds

        self._disarm_endevent()
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
        self._ended_flag = False

    def get_position(self) -> float:
        match self._state:
            case "playing":
                return self._accumulated + (time.perf_counter() - self._play_start)
            case "paused":
                return self._accumulated
            case _:
                return 0.0

    def poll_end(self) -> bool:
        """One-shot natural-end detection for the active stream.

        Returns ``True`` exactly once when the playing track has reached its
        end. Used for Channel (crossfade) playback, which has no pygame event;
        the music backend still uses the ``TRACK_ENDED`` event.
        """
        if self._state != "playing":
            self._ended_flag = False
            return False
        if self.duration > 0 and self.get_position() >= self.duration - 0.08:
            if not self._ended_flag:
                self._ended_flag = True
                return True
        else:
            self._ended_flag = False
        return False

    def set_volume(self, value: float) -> None:
        self._require_ready()
        self._volume = max(0.0, min(1.0, float(value)))
        pygame.mixer.music.set_volume(self._volume)
        if self._channel is not None:
            try:
                self._channel.set_volume(self._volume)
            except Exception:
                pass

    def is_playing(self) -> bool:
        return self._state == "playing"

    def is_paused(self) -> bool:
        return self._state == "paused"
