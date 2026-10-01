# AGENTS.md — Forte

Music player. Python 3.12+ (`X | Y`, `match`, `pathlib`). `PyQt6 + pygame.mixer + mutagen + numpy`. Entry `main.py` (QApplication → `SessionState.load()` → apply theme stylesheet → `MainWindow`).

## Commands

- Setup: `uv venv` + `uv pip install -r requirements.txt` (deps: `requirements.txt` only, no lockfile).
- Run: `python main.py`
- Only verification: `python test_engine.py "<path-to-real.mp3>"` — requires an audio-file arg. No pytest/ruff/mypy/CI.
- Shell here is Windows PowerShell.

## Where logic lives

- `forte/ui/main_window.py` is the wiring hub. It owns `Playlist`, `Player`, both panels, `ForteTray`, `VisualizerEngine`, and 3 timers (progress 200ms / pygame-event poll 500ms / autosave 30s). Put cross-panel behavior here, not in leaf widgets.
- `forte/playlist.py` is pure data (`TrackMetadata` list). `forte/ui/playlist_panel.py:46` wraps it in `PlaylistModel(QAbstractListModel)` + `PlaylistProxyModel` (title+artist filter). Reorder takes a full permutation; `shuffle()` saves `_original_order` for `unshuffle()`.
- `forte/player.py` position is wall-clock (`perf_counter`), not `mixer.get_pos()`. Don't "fix" this.
- `forte/visualizer.py:40` `VisualizerEngine` is `moveToThread` with **no parent**. GUI → worker via `request_track/position/playing` signals; worker → GUI via `bars_ready` → `ScrubberWidget.update_bars()`. Call `visualizer.stop()` on quit. Worker ticks at 60 FPS; progress reporting stays at 200ms — don't merge them.
- `forte/state.py` persists to `~/.forte/session.json` atomically (tmp + replace) with `_normalise()` clamping `repeat {off,one,all}`, `theme {dark,light}`, `crossfade {0,1,2,3}`. Per-track resume offsets live in `MainWindow._positions`, not in `SessionState`. Restore parks paused at `saved − 3s` (`_prepare_current`).

## Gotchas

- Player endevents: `_disarm_endevent()` before every `music.play()/load()` and `_arm_endevent()` after, or `TRACK_ENDED` fires spuriously. Natural end needs **both** paths in `_poll_events`: pygame event queue (music backend) **and** `poll_end()` (crossfade `Channel` has no event).
- `Player.seek()` / pause-resume on a crossfade `Channel` hands control back to the music backend (channels can't seek). `crossfade_play()` only when `_crossfade > 0` and already `is_playing() or using_channel`; otherwise normal `load() + play()`. Guard everything with `player.available` — UI must work with no audio device.
- Theme: zero magic hex in UI files — all chrome colors from the `theme` dict (`forte/theme.py`) + `build_stylesheet()`. `set_theme` must update app stylesheet **and** each `IconButton._theme`, `scrubber.theme`, plus `model.refresh()`. Exception: `_ART_PALETTE` in `now_playing.py` is generative art, intentionally hardcoded.
- Window is frameless fixed 900×580 with custom drag (`eventFilter`) — don't make it resizable. Close/minimise hides to tray when `minimise_to_tray` is true; real quit sets `_quitting = True` first. `ForteTray` is a no-op when `QSystemTrayIcon.isSystemTrayAvailable()` is false — always guard with `.available`.
- `ScrubberWidget` is a custom `QWidget`, not `QSlider`; time labels reserve `_SIDE = 48`px per side, seek math must subtract it. Album-art slot is fixed 220×220 (`AlbumArtLabel`), never reflows layout.
- Spec is `SPEC.md`; `build.sh`/`icon.ico` mentioned there do **not** exist in-tree. Don't reference them as if they do.
