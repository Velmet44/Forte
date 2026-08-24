from __future__ import annotations

import random
from pathlib import Path

from forte.metadata import TrackMetadata, read_metadata

_AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a"}


class Playlist:
    """Pure-Python data model holding an ordered list of TrackMetadata."""

    def __init__(self) -> None:
        self._tracks: list[TrackMetadata] = []
        self._original_order: list[TrackMetadata] | None = None

    def add_track(self, filepath: str) -> TrackMetadata:
        metadata = read_metadata(filepath)
        self._tracks.append(metadata)
        return metadata

    def add_folder(self, folderpath: str) -> int:
        folder = Path(folderpath)
        if not folder.is_dir():
            raise ValueError(f"Folder not found: {folderpath}")

        files = sorted(
            (
                str(p)
                for p in folder.rglob("*")
                if p.is_file() and p.suffix.lower() in _AUDIO_EXTENSIONS
            ),
            key=lambda f: Path(f).name.lower(),
        )
        for f in files:
            self._tracks.append(read_metadata(f))
        return len(files)

    def remove_track(self, index: int) -> None:
        if not 0 <= index < len(self._tracks):
            raise IndexError(f"Track index out of range: {index}")
        del self._tracks[index]

    def clear(self) -> None:
        self._tracks.clear()
        self._original_order = None

    def move_track(self, from_index: int, to_index: int) -> None:
        if not 0 <= from_index < len(self._tracks):
            raise IndexError(f"Track index out of range: {from_index}")
        if not 0 <= to_index < len(self._tracks):
            raise IndexError(f"Track index out of range: {to_index}")
        track = self._tracks.pop(from_index)
        self._tracks.insert(to_index, track)

    def reorder(self, new_order: list[int]) -> None:
        """Reorder tracks in-place given a permutation of current indices."""
        expected = list(range(len(self._tracks)))
        if sorted(new_order) != expected:
            raise ValueError("reorder requires a permutation of all current track indices")
        self._tracks = [self._tracks[i] for i in new_order]

    def shuffle(self) -> None:
        if self._original_order is None:
            self._original_order = list(self._tracks)
        rng = random.Random()
        tracks = list(self._tracks)
        for i in range(len(tracks) - 1, 0, -1):
            j = rng.randint(0, i)
            tracks[i], tracks[j] = tracks[j], tracks[i]
        self._tracks = tracks

    def unshuffle(self) -> None:
        if self._original_order is not None:
            self._tracks = list(self._original_order)
            self._original_order = None

    def save_m3u8(self, filepath: str) -> None:
        path = Path(filepath)
        with path.open("w", encoding="utf-8") as fh:
            fh.write("#EXTM3U\n")
            for track in self._tracks:
                fh.write(f"#EXTINF:{int(round(track.duration))},{track.artist} - {track.title}\n")
                fh.write(f"{track.filepath}\n")

    def load_m3u8(self, filepath: str) -> None:
        path = Path(filepath)
        if not path.is_file():
            raise ValueError(f"Playlist file not found: {filepath}")

        lines = path.read_text(encoding="utf-8").splitlines()
        if lines and lines[0].strip() != "#EXTM3U":
            raise ValueError(f"Not a valid m3u8 playlist: {filepath}")

        base_dir = path.resolve().parent
        for raw in lines[1:]:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            candidate = Path(line)
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            if candidate.is_file() and candidate.suffix.lower() in _AUDIO_EXTENSIONS:
                self._tracks.append(read_metadata(str(candidate)))

    def __len__(self) -> int:
        return len(self._tracks)

    def __getitem__(self, index: int) -> TrackMetadata:
        return self._tracks[index]

    def __iter__(self):
        return iter(self._tracks)
