from __future__ import annotations

import sys
import time

from forte.metadata import read_metadata
from forte.player import Player
from forte.playlist import Playlist


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python test_engine.py /path/to/any_song.mp3")

    filepath = sys.argv[1]

    playlist = Playlist()
    playlist.add_track(filepath)

    metadata = read_metadata(filepath)
    print("Track metadata:")
    print(f"  title:      {metadata.title}")
    print(f"  artist:     {metadata.artist}")
    print(f"  album:      {metadata.album}")
    print(f"  duration:   {metadata.duration:.2f}s")
    print(f"  duration_str: {metadata.duration_str}")
    print(f"  filepath:   {metadata.filepath}")
    print(f"  album_art:  {'present' if metadata.album_art else 'none'}")

    player = Player()
    player.load(filepath)

    print("Playing for 3 seconds...")
    player.play()
    for _ in range(6):
        time.sleep(0.5)
        print(f"  position: {player.get_position():.2f}s")

    print("Pausing for 1 second...")
    player.pause()
    time.sleep(1)
    print(f"  position after pause: {player.get_position():.2f}s")

    print("Resuming for 2 seconds...")
    player.resume()
    for _ in range(4):
        time.sleep(0.5)
        print(f"  position: {player.get_position():.2f}s")

    print("Stopping...")
    player.stop()
    print(f"  position after stop: {player.get_position():.2f}s")

    print("Engine test passed")


if __name__ == "__main__":
    main()
