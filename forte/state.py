from __future__ import annotations

import json
from pathlib import Path

from forte.metadata import TrackMetadata

_DEFAULTS = {
    "last_playlist": [],
    "last_track_index": -1,
    "last_position": 0.0,
    "volume": 1.0,
    "shuffle": False,
    "repeat": "off",
    "theme": "dark",
    "crossfade": 0,
    "minimise_to_tray": True,
    "recently_played": [],
}

_VALID_REPEAT = {"off", "one", "all"}
_VALID_THEME = {"dark", "light"}
_VALID_CROSSFADE = {0, 1, 2, 3}


class SessionState:
    """Reads and writes persistent session state to ~/.forte/session.json."""

    def __init__(self) -> None:
        self._dir = Path.home() / ".forte"
        self._file = self._dir / "session.json"

    def load(self) -> dict:
        if not self._file.is_file():
            return dict(_DEFAULTS)

        try:
            with self._file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULTS)

        if not isinstance(data, dict):
            return dict(_DEFAULTS)

        merged = dict(_DEFAULTS)
        for key in _DEFAULTS:
            if key in data:
                merged[key] = data[key]
        return self._normalise(merged)

    def _normalise(self, data: dict) -> dict:
        if data["repeat"] not in _VALID_REPEAT:
            data["repeat"] = "off"
        if data["theme"] not in _VALID_THEME:
            data["theme"] = "dark"
        if data["crossfade"] not in _VALID_CROSSFADE:
            data["crossfade"] = 0
        if not isinstance(data["recently_played"], list):
            data["recently_played"] = []
        if not isinstance(data["last_playlist"], list):
            data["last_playlist"] = []
        return data

    def save(self, data: dict) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        normalised = self._normalise({**_DEFAULTS, **data})
        tmp = self._file.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(normalised, fh, indent=2)
        tmp.replace(self._file)

    def add_recently_played(self, filepath: str) -> None:
        data = self.load()
        recent: list[str] = [p for p in data["recently_played"] if p != filepath]
        recent.insert(0, filepath)
        data["recently_played"] = recent[:20]
        self.save(data)
