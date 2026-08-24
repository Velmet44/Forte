# Forte

A modern, lightweight desktop music player for Windows, built with Python (PyQt6 + pygame + mutagen + numpy).

Forte is developed in stages. The engine and the main window / playlist UI are complete; the now-playing panel (art, scrubber, transport controls) is still a placeholder skeleton.

## What works today

- **Playback engine** (`forte/player.py`) — `pygame.mixer`-based player with MP3, FLAC, WAV, OGG and M4A support, pause/resume/seek/stop, volume, position tracking and a natural end-of-track event. If no audio output device is available, the app still opens and the UI works; playback is disabled with a status-bar hint.
- **Metadata** (`forte/metadata.py`) — reads title, artist, album, duration and embedded album art from tags (MP3/FLAC/OGG/M4A) with sensible fallbacks.
- **Playlist model** (`forte/playlist.py`) — pure-Python data model: add file/folder, remove, reorder, shuffle/unshuffle, and M3U8 import/export.
- **Session state** (`forte/state.py`) — persists the last session (playlist, track index, position, volume, theme, …) to `~/.forte/session.json`, restored on launch.
- **Theming** (`forte/theme.py`) — central colour tokens and a PyQt6 QSS stylesheet builder for dark/light themes (no magic hex anywhere in the UI).
- **Visualizer** (`forte/visualizer.py`) — pure numpy frequency-band analyzer ready for the UI.
- **Main window** (`forte/ui/main_window.py`) — frameless 900×580 window with a custom 36px title bar (drag-to-move, minimise / settings / close), a 260px playlist panel, a 1px divider, the now-playing panel, and a 24px status bar.
- **Playlist panel** (`forte/ui/playlist_panel.py`) — search bar (Ctrl+F), a custom-delegate track list (track # / ▶, truncated title, right-aligned mono duration, amber "playing" indicator), a toolbar (+ / folder / clear), OS file drag-and-drop, in-list drag reorder, double-click to play, Delete to remove, and a right-click menu (Play Next / Remove / Show in Explorer).

## Roadmap / not yet implemented

- Now-playing art, scrubber and transport controls (`forte/ui/now_playing.py` is a skeleton).
- Settings dialog.
- System tray integration.
- Visualizer rendering.

## Requirements

- Python 3.12+ (code uses modern syntax: `X | Y` unions, `match`, `pathlib`).
- Dependencies in `requirements.txt`: `PyQt6`, `pygame`, `mutagen`, `numpy`.

## Setup

```bash
uv venv
uv pip install -r requirements.txt
```

## Run the app

```bash
python main.py
```

The window opens with an empty playlist. Add tracks with the **+** / **📁** toolbar buttons, drag audio files onto the list, or drop a folder. Double-click a track to play it; type in the search box to filter by title or artist.

## Run the engine test

```bash
python test_engine.py "C:\Users\<you>\Downloads\Michael Jackson - Beat It (SPOTISAVER).mp3"
```

Loads a track, plays/pauses/resumes/stops it, prints position updates, and reports `Engine test passed`.

## Project layout

```
forte/
  player.py        # pygame.mixer playback engine
  playlist.py      # pure-Python playlist data model
  metadata.py      # mutagen-based tag reading
  state.py         # session persistence
  theme.py         # colour tokens + QSS builder
  visualizer.py    # numpy band analyzer
  ui/
    main_window.py     # frameless window, title bar, layout
    playlist_panel.py  # search, track list, toolbar, drag-drop
    now_playing.py     # skeleton (art / scrubber / controls placeholders)
    scrubber.py        # stub
    settings.py        # stub
    tray.py             # stub
    playlist_panel / main_window / now_playing / scrubber / tray / settings
main.py            # entry point (launches MainWindow)
test_engine.py     # engine smoke test
```

## License

See repository for details.
