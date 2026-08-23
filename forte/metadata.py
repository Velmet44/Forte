from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mutagen
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3
from mutagen.mp4 import MP4


@dataclass
class TrackMetadata:
    """Normalised metadata for a single audio track."""

    title: str
    artist: str
    album: str
    duration: float
    duration_str: str
    filepath: str
    album_art: bytes | None


def _format_duration(seconds: float) -> str:
    total = int(round(seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes}:{secs:02d}"


def _read_tags(audio: mutagen.FileType) -> tuple[str, str, str]:
    title = artist = album = ""
    if isinstance(audio, MP4):
        title = str(audio.get("\xa9nam", [""])[0])
        artist = str(audio.get("\xa9ART", [""])[0])
        album = str(audio.get("\xa9alb", [""])[0])
    elif isinstance(audio, FLAC):
        title = str(audio.get("title", [""])[0])
        artist = str(audio.get("artist", [""])[0])
        album = str(audio.get("album", [""])[0])
    elif isinstance(audio, mutagen.ogg.OggFileType):
        title = str(audio.get("title", [""])[0])
        artist = str(audio.get("artist", [""])[0])
        album = str(audio.get("album", [""])[0])
    elif isinstance(audio, mutagen.mp3.MP3):
        tags = audio.tags
        if tags is not None:
            title = str(tags.get("TIT2", "")).strip()
            artist = str(tags.get("TART", "")).strip()
            if not artist:
                artist = str(tags.get("TPE1", "")).strip()
            album = str(tags.get("TALB", "")).strip()
    return title, artist, album


def _read_album_art(audio: mutagen.FileType) -> bytes | None:
    try:
        if isinstance(audio, mutagen.mp3.MP3):
            tags = audio.tags
            if tags is None:
                return None
            apic: list[APIC] = tags.getall("APIC")
            if apic:
                return bytes(apic[0].data)
        elif isinstance(audio, FLAC):
            if audio.pictures:
                return bytes(audio.pictures[0].data)
        elif isinstance(audio, mutagen.ogg.OggFileType):
            pics = audio.get("metadata_block_picture")
            if pics:
                picture = Picture.from_base64(pics[0])
                return bytes(picture.data)
        elif isinstance(audio, MP4):
            covers = audio.get("covr")
            if covers:
                return bytes(covers[0])
    except Exception:
        return None
    return None


def read_metadata(filepath: str) -> TrackMetadata:
    path = Path(filepath)
    if not path.is_file():
        raise ValueError(f"Audio file not found: {filepath}")

    audio = mutagen.File(str(path))
    if audio is None or audio.info is None:
        raise ValueError(f"Could not read audio metadata from: {filepath}")

    duration = float(audio.info.length)
    title, artist, album = _read_tags(audio)

    if not title:
        title = path.stem
    if not artist:
        artist = "Unknown Artist"
    if not album:
        album = "Unknown Album"

    album_art = _read_album_art(audio)

    return TrackMetadata(
        title=title,
        artist=artist,
        album=album,
        duration=duration,
        duration_str=_format_duration(duration),
        filepath=str(path.resolve()),
        album_art=album_art,
    )
