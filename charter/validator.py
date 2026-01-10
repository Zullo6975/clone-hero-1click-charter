import sys
import argparse
from pathlib import Path
import mido # type: ignore

def validate_chart_file(song_dir: Path, summary_only: bool = False):
    """
    Scans the song folder for common Clone Hero issues.
    Prints report to stdout.
    """
    chart_path = song_dir / "notes.mid"
    ini_path = song_dir / "song.ini"
    audio_path = song_dir / "song.mp3" # or .ogg

    warnings = []
    infos = []

    if not chart_path.exists():
        print("CRITICAL: notes.mid not found!")
        return

    # Check Audio
    if not audio_path.exists():
        # Try ogg
        if (song_dir / "song.ogg").exists():
            infos.append("Audio: Found song.ogg")
        else:
            warnings.append("Audio file (song.mp3/ogg) missing.")
    else:
        infos.append("Audio: Found song.mp3")

    # Check INI
    if not ini_path.exists():
        warnings.append("song.ini missing.")
    else:
        # Simple parse check
        try:
            content = ini_path.read_text(encoding="utf-8")
            if "[song]" not in content:
                warnings.append("song.ini missing [song] header.")
        except:
            warnings.append("song.ini is unreadable.")

    # Check MIDI
    try:
        mid = mido.MidiFile(str(chart_path))
        track_names = []
        has_tempo = False
        has_notes = False

        for i, track in enumerate(mid.tracks):
            for msg in track:
                if msg.type == 'track_name':
                    track_names.append(msg.name)
                if msg.type == 'set_tempo':
                    has_tempo = True
                if msg.type == 'note_on' and msg.velocity > 0:
                    has_notes = True

        if "PART GUITAR" not in track_names and "T1 GEMS" not in track_names:
            warnings.append("Missing 'PART GUITAR' track.")
        if not has_tempo:
            warnings.append("No tempo map found.")
        if not has_notes:
            warnings.append("Chart appears empty (no notes).")

    except Exception as e:
        warnings.append(f"Corrupt MIDI file: {e}")

    # Output
    print(f"Scanning: {song_dir.name}")
    print("-" * 30)
    for info in infos:
        print(f"OK: {info}")

    if warnings:
        print("\nWARNINGS FOUND:")
        for w in warnings:
            print(f"- {w}")
    else:
        print("\n✅ Chart passed basic health check.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    p.add_argument("--summary", action="store_true")
    args = p.parse_args()
    validate_chart_file(Path(args.folder), args.summary)

if __name__ == "__main__":
    main()
