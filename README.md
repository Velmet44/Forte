# Forte

A modern, lightweight desktop music player for Windows, built with Python (PyQt6 + pygame + mutagen + numpy).

Forte is developed in stages. The playback engine, playlist, and main window were completed in Stage 1–2. **Stage 3 delivers the full Now Playing panel** (album art, track info, scrubber, transport controls), full player wiring, keyboard shortcuts, session resume, and a system tray icon.

## Screenshot

![Forte screenshot](assets/screenshot.gif)

> Drop a real capture at `assets/screenshot.gif` (GIF preferred — show the visualizer moving).

## What works today

- **Playback engine** (`forte/player.py`) — `pygame.mixer`-based player with MP3, FLAC, WAV, OGG and M4A support, pause/resume/seek/stop, volume, position tracking and a natural end-of-track event. If no audio output device is available, the app still opens and the UI works; playback is disabled with a status-bar hint.
- **Metadata** (`forte/metadata.py`) — reads title, artist, album, duration and embedded album art from tags (MP3/FLAC/OGG/M4A) with sensible fallbacks.
- **Playlist model** (`forte/playlist.py`) — pure-Python data model: add file/folder, remove, reorder, shuffle/unshuffle, and M3U8 import/export.
- **Session state** (`forte/state.py`) — persists the last session (playlist with per-track duration + position, track index, volume, shuffle/repeat, theme, …) to `~/.forte/session.json`, restored on launch. On reopen the app loads paused at `saved − 3s`; pressing Play resumes from there.
- **Theming** (`forte/theme.py`) — central colour tokens and a PyQt6 QSS stylesheet builder for dark/light themes (no magic hex anywhere in the UI).
- **Visualizer** (`forte/visualizer.py`) — `VisualizerEngine` runs off the GUI thread (QThread) and analyses a track's decoded samples into 40 logarithmically-spaced frequency bands, normalised against a rolling max with lerp smoothing. It emits 40 bar values (0–1) in sync with playback position, and smoothly decays to flat when paused. If numpy or the sample decoder is unavailable it falls back to a seeded, always-animated fake generator.
- **Main window** (`forte/ui/main_window.py`) — frameless 900×580 window with a custom title bar (drag-to-move, minimise / settings / close), a playlist panel, the now-playing panel, a status bar, and a system tray icon.
- **Playlist panel** (`forte/ui/playlist_panel.py`) — search bar (Ctrl+F), a custom-delegate track list (track # / ▶, truncated title, right-aligned mono duration, amber "playing" indicator), a toolbar (+ / folder / clear), OS file drag-and-drop, in-list drag reorder, double-click to play, Delete to remove, and a right-click menu (Play Next / Remove / Show in Explorer).
- **Now Playing panel** (`forte/ui/now_playing.py`) — 220×220 rounded album art with a 200ms fade and a seeded gradient placeholder when art is missing; title / artist / album · year; a fully painted **scrubber** with `[current] [bar] [total]` time labels and a hover thumb; and transport controls (prev, −10s, play/pause, +10s, next, shuffle, repeat, volume) drawn entirely with `QPainter` for cross-platform consistency. Every control has a hover tooltip.
- **Scrubber** (`forte/ui/scrubber.py`) — custom `QWidget`, not a `QSlider`: painted track/fill/thumb, 200ms progress polling, click/drag to seek, and the 40-bar visualizer rendered inside the track behind the progress fill.
- **Visualizer rendering** — the waveform bars pulse live inside the scrubber track (real samples when decodable, convincing animated fallback otherwise).
- **System tray** (`forte/ui/tray.py`) — `ForteTray` shows the Forte icon, updates its tooltip to the current track, and exposes a context menu (Play/Pause · Next · Previous · Show Window · Quit). Single-click toggles the window; double-click shows and raises it. Minimising the window hides it to the tray instead of quitting.
- **Session persistence** — playlist, per-track position, current track index, volume, shuffle/repeat and theme are restored on launch and autosaved every 30s (and on quit). The last 20 played tracks are remembered; the playlist context menu has a **Recently Played** submenu that plays any of the last 10.
- **Crossfade** — when the (persisted) crossfade duration is greater than 0, advancing to the next track overlaps the outgoing stream with the incoming one (fade-out + channel fade-in).
- **Settings dialog** (`forte/ui/settings.py`) — `SettingsDialog` with theme (Dark/Light), crossfade duration (0/1/2/3s), minimise-to-tray-on-close, and show-file-extensions toggles. Changes apply live and persist to the session.
- **Keyboard shortcuts** — see the table below.

## Roadmap / not yet implemented

- Nothing outstanding — all spec features are implemented. (The Settings dialog is the last item completed.)

## Requirements

- Python 3.12+ (code uses modern syntax: `X | Y` unions, `match`, `pathlib`).
- Dependencies in `requirements.txt`: `PyQt6`, `pygame`, `mutagen`, `numpy`.

## Setup

```bash
pip install -r requirements.txt && python main.py
```

Or with `uv`:

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
python test_engine.py "C:\Users\<you>\Music\example.mp3"
```

Loads a track, plays/pauses/resumes/stops it, prints position updates, and reports `Engine test passed`. Requires a path to a real audio file.

## Supported formats

MP3, FLAC, WAV, OGG, M4A — playback via `pygame.mixer`, tags and album art via `mutagen`. Unsupported files are skipped with a status message, never a crash.

## Keyboard shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `Right` | Next track |
| `Left` | Previous track (restart if >3s in, else go back) |
| `Shift+Right` / `Shift+Left` | Skip +10s / −10s |
| `M` | Mute toggle |
| `Ctrl+O` | Add files |
| `Ctrl+F` | Focus search |
| `Ctrl+Q` | Quit |
| `Delete` | Remove selected track from playlist |
| `Ctrl+S` | Save playlist (`.m3u8`) |

## How AI was used

Built with AI-assisted coding in OpenCode (implementation and refactors drafted with an AI coding agent, then reviewed and smoke-tested by the maintainer via `test_engine.py` and manual runs). If your submission rules need exact models and prompts, fill them in here.

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
    settings.py        # settings dialog (theme/crossfade/tray/extensions)
main.py            # entry point (launches MainWindow)
test_engine.py     # engine smoke test
```

## License

MIT — see [LICENSE](LICENSE).
