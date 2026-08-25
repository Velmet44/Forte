# Forte

A modern, lightweight desktop music player for Windows, built with Python (PyQt6 + pygame + mutagen + numpy).

Forte is developed in stages. The playback engine, playlist, and main window were completed in Stage 1–2. **Stage 3 delivers the full Now Playing panel** (album art, track info, scrubber, transport controls), full player wiring, keyboard shortcuts, session resume, and a system tray icon.

## What works today

- **Playback engine** (`forte/player.py`) — `pygame.mixer`-based player with MP3, FLAC, WAV, OGG and M4A support, pause/resume/seek/stop, volume, position tracking and a natural end-of-track event. If no audio output device is available, the app still opens and the UI works; playback is disabled with a status-bar hint.
- **Metadata** (`forte/metadata.py`) — reads title, artist, album, duration and embedded album art from tags (MP3/FLAC/OGG/M4A) with sensible fallbacks.
- **Playlist model** (`forte/playlist.py`) — pure-Python data model: add file/folder, remove, reorder, shuffle/unshuffle, and M3U8 import/export.
- **Session state** (`forte/state.py`) — persists the last session (playlist with per-track duration + position, track index, volume, shuffle/repeat, theme, …) to `~/.forte/session.json`, restored on launch. On reopen the app loads paused at `saved − 3s`; pressing Play resumes from there.
- **Theming** (`forte/theme.py`) — central colour tokens and a PyQt6 QSS stylesheet builder for dark/light themes (no magic hex anywhere in the UI).
- **Visualizer** (`forte/visualizer.py`) — pure numpy frequency-band analyzer ready for the UI.
- **Main window** (`forte/ui/main_window.py`) — frameless 900×580 window with a custom title bar (drag-to-move, minimise / settings / close), a playlist panel, the now-playing panel, a status bar, and a system tray icon.
- **Playlist panel** (`forte/ui/playlist_panel.py`) — search bar (Ctrl+F), a custom-delegate track list (track # / ▶, truncated title, right-aligned mono duration, amber "playing" indicator), a toolbar (+ / folder / clear), OS file drag-and-drop, in-list drag reorder, double-click to play, Delete to remove, and a right-click menu (Play Next / Remove / Show in Explorer).
- **Now Playing panel** (`forte/ui/now_playing.py`) — 220×220 rounded album art with a 200ms fade and a seeded gradient placeholder when art is missing; title / artist / album · year; a fully painted **scrubber** with `[current] [bar] [total]` time labels and a hover thumb; and transport controls (prev, −10s, play/pause, +10s, next, shuffle, repeat, volume) drawn entirely with `QPainter` for cross-platform consistency. Every control has a hover tooltip.
- **Scrubber** (`forte/ui/scrubber.py`) — custom `QWidget`, not a `QSlider`: painted track/fill/thumb, 200ms progress polling, click/drag to seek.
- **Keyboard shortcuts** — Space (play/pause), ← (restart if <3s else previous), → (next), Shift+← / Shift+→ (seek −10s / +10s), M (mute toggle), Ctrl+O (add files), Ctrl+F (focus search), Ctrl+Q (quit), Delete (remove selected), Ctrl+S (save playlist).
- **System tray** (`forte/ui/tray.py`) — minimises to tray, shows the current track in its tooltip, restores on double-click, and exposes play/pause/next/prev/quit via its context menu.

## Roadmap / not yet implemented

- Settings dialog (currently a stub; launch hook wired to a no-op). The persisted `crossfade` value is already honoured on playback as a fade-in, but there is no UI to change it yet.
- Visualizer rendering in the UI (`forte/visualizer.py` exists and is unused — the signature waveform-in-scrubber feature is not yet drawn).

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

The window opens with your last session restored (paused, ready to resume). Add tracks with the **+** / **📁** toolbar buttons, drag audio files onto the list, or drop a folder. Double-click a track to play it; type in the search box to filter by title or artist. Closing the app saves the session; reopening resumes where you left off.

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
    main_window.py     # frameless window, title bar, layout, wiring, tray
    playlist_panel.py  # search, track list, toolbar, drag-drop
    now_playing.py     # album art, track info, scrubber host, controls
    scrubber.py        # custom painted progress/seek bar
    tray.py            # system tray icon + menu
    settings.py        # stub
main.py            # entry point (launches MainWindow)
test_engine.py     # engine smoke test
```

## License

See repository for details.
