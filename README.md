# Forte

A modern, lightweight desktop music player for Windows, built with Python.

Forte is being developed in stages. This stage delivers the **audio playback engine** and project scaffold — no UI yet.

## Features (current stage)

- **Playback engine** (`forte/player.py`) — built on `pygame.mixer` with support for MP3, FLAC, WAV, OGG and M4A.
- **Metadata** (`forte/metadata.py`) — reads title, artist, album, duration and embedded album art from tags, with sensible fallbacks.
- **Playlist model** (`forte/playlist.py`) — a pure-Python data model with add, remove, reorder, shuffle/unshuffle, and M3U8 import/export.
- **Session state** (`forte/state.py`) — persists last session (playlist, position, volume, theme, etc.) to `~/.forte/session.json`.
- **Theming** (`forte/theme.py`) — central colour tokens and a PyQt6 QSS stylesheet builder for dark/light themes.
- **Visualizer** (`forte/visualizer.py`) — a pure numpy frequency-band analyzer ready for the UI.

## Requirements

- Python 3.12+ (written using modern syntax: `X | Y` unions, `match`, `tomllib`)
- Dependencies listed in `requirements.txt`:
  - `PyQt6`
  - `pygame`
  - `mutagen`
  - `numpy`

## Setup

```bash
uv venv
uv pip install -r requirements.txt
```

## Run the engine test

```bash
python test_engine.py /path/to/any_song.mp3
```

This loads a track, plays/pauses/resumes/stops it, prints position updates, and reports
`Engine test passed` at the end.

## Project layout

```
forte/
  player.py        # pygame.mixer playback engine
  playlist.py      # pure-Python playlist data model
  metadata.py      # mutagen-based tag reading
  state.py         # session persistence
  theme.py         # colour tokens + QSS builder
  visualizer.py    # numpy band analyzer
  ui/              # UI stubs (not yet implemented)
main.py            # entry point (engine placeholder for now)
test_engine.py     # engine smoke test
```

## License

See repository for details.
