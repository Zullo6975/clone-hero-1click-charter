from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import pretty_midi
import mido

# ---- Your chart conventions ----
TRACK_NAME = "PART GUITAR"

# Define ranges for all difficulties
ALL_DIFFS = {
    "Expert": range(96, 101),  # 96-100
    "Hard":   range(84, 89),  # 84-88
    "Medium": range(72, 77),  # 72-76
    "Easy":   range(60, 65)   # 60-64
}

# Legacy for validation checks (defaults to Expert)
LANE_PITCHES = set(ALL_DIFFS["Expert"])
ORANGE_PITCH = 100
DEFAULT_MIN_NOTE_START = 0.5
DEFAULT_SP_PITCH = 116


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]


def _find_notes_mid(song_dir: Path) -> Path | None:
    p = song_dir / "notes.mid"
    return p if p.exists() else None


def _find_song_ini(song_dir: Path) -> Path | None:
    p = song_dir / "song.ini"
    return p if p.exists() else None


def _find_audio(song_dir: Path) -> Path | None:
    for name in ("song.ogg", "song.mp3", "song.wav", "song.flac"):
        p = song_dir / name
        if p.exists():
            return p
    for p in song_dir.iterdir():
        if p.is_file() and p.suffix.lower() in {".ogg", ".mp3", ".wav", ".flac"}:
            return p
    return None


def _find_part_guitar(pm: pretty_midi.PrettyMIDI) -> pretty_midi.Instrument | None:
    for inst in pm.instruments:
        if (inst.name or "").strip().upper() == TRACK_NAME:
            return inst
    for inst in pm.instruments:
        if "PART GUITAR" in (inst.name or "").upper():
            return inst
    return None


def _iter_notes(inst: pretty_midi.Instrument) -> Iterable[pretty_midi.Note]:
    for n in inst.notes:
        yield n


def _count_density_spikes(note_starts: list[float], window_sec: float = 1.0, nps_warn: float = 16.0) -> int:
    # EXPERT TUNING: Warn only if NPS exceeds 16.0 (DragonForce speeds)
    if not note_starts:
        return 0
    starts = sorted(note_starts)

    spikes = 0
    left = 0
    for right in range(len(starts)):
        t = starts[right]
        while left < len(starts) and starts[left] < t - window_sec:
            left += 1
        count = (right - left) + 1
        nps = count / window_sec
        if nps >= nps_warn:
            spikes += 1
    return spikes


def _group_sp_phrases(sp_starts: list[float], sp_ends: list[float], gap_join_sec: float = 0.45) -> list[tuple[float, float]]:
    spans = sorted(zip(sp_starts, sp_ends), key=lambda x: x[0])
    if not spans:
        return []

    phrases: list[tuple[float, float]] = []
    cur_s, cur_e = spans[0]
    for s, e in spans[1:]:
        if s <= cur_e + gap_join_sec:
            cur_e = max(cur_e, e)
        else:
            phrases.append((cur_s, cur_e))
            cur_s, cur_e = s, e
    phrases.append((cur_s, cur_e))
    return phrases


def _parse_sections(midi_path: Path, pm: pretty_midi.PrettyMIDI) -> tuple[list[tuple[str, float]], str]:
    out: list[tuple[str, float]] = []
    found_in_track_name = None

    try:
        mid = mido.MidiFile(str(midi_path))

        for i, track in enumerate(mid.tracks):
            track_name = f"Track {i}"
            for msg in track:
                if msg.type == 'track_name':
                    track_name = msg.name
                    break

            abs_time = 0
            for msg in track:
                abs_time += msg.time
                if msg.type in ('text', 'lyrics') and isinstance(msg.text, str):
                    text = msg.text.strip()
                    is_sec = False
                    clean_name = ""

                    if text.lower().startswith("section "):
                        clean_name = text[8:].strip()
                        is_sec = True
                    elif text.lower().startswith("[section "):
                        clean_name = text.replace(
                            "[section ", "").replace("]", "").strip()
                        is_sec = True

                    if is_sec:
                        if found_in_track_name is None:
                            found_in_track_name = track_name
                        seconds = pm.tick_to_time(abs_time)
                        out.append((clean_name, seconds))

    except Exception as e:
        print(f"Warning: Failed to scan sections with mido: {e}")
        return [], "Error"

    out.sort(key=lambda x: x[1])
    track_info = found_in_track_name if found_in_track_name is not None else "None"
    return out, track_info


def _estimate_chords(lane_note_starts: list[float], tol: float = 0.012) -> int:
    if not lane_note_starts:
        return 0
    times = sorted(lane_note_starts)
    buckets: list[list[float]] = []
    cur: list[float] = [times[0]]
    for t in times[1:]:
        if abs(t - cur[-1]) <= tol:
            cur.append(t)
        else:
            buckets.append(cur)
            cur = [t]
    buckets.append(cur)
    return sum(1 for b in buckets if len(b) >= 2)


def validate_song_dir(song_dir: Path, *, sp_pitch: int, min_note_start: float = DEFAULT_MIN_NOTE_START) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not song_dir.exists() or not song_dir.is_dir():
        return ValidationResult(False, [f"Not a directory: {song_dir}"], [])

    notes_mid = _find_notes_mid(song_dir)
    if not notes_mid:
        errors.append("Missing notes.mid")
        return ValidationResult(False, errors, warnings)

    if not _find_song_ini(song_dir):
        warnings.append(
            "Missing song.ini (Clone Hero will usually require this).")
    if not _find_audio(song_dir):
        warnings.append(
            "No audio file found (expected song.ogg/mp3/wav/flac).")

    try:
        pm = pretty_midi.PrettyMIDI(str(notes_mid))
    except Exception as e:
        errors.append(f"Could not parse notes.mid: {e}")
        return ValidationResult(False, errors, warnings)

    guitar = _find_part_guitar(pm)
    if guitar is None:
        errors.append('No instrument track named "PART GUITAR" found.')
        return ValidationResult(False, errors, warnings)

    if not guitar.notes:
        errors.append("PART GUITAR has zero notes.")
        return ValidationResult(False, errors, warnings)

    bad_dur = 0
    too_early = 0
    lane_notes = 0
    orange_notes = 0
    sp_notes = 0

    lane_note_starts: list[float] = []
    sp_starts: list[float] = []
    sp_ends: list[float] = []

    for n in _iter_notes(guitar):
        if n.end <= n.start:
            bad_dur += 1
        if n.start < 0:
            errors.append(
                f"Note starts before 0.0s: pitch={n.pitch} start={n.start:.3f}")
        if n.start < min_note_start - 1e-6:
            too_early += 1

        if n.pitch in LANE_PITCHES:
            lane_notes += 1
            if n.pitch == ORANGE_PITCH:
                orange_notes += 1
            lane_note_starts.append(float(n.start))
        elif n.pitch == sp_pitch:
            sp_notes += 1
            sp_starts.append(float(n.start))
            sp_ends.append(float(n.end))

    if bad_dur:
        errors.append(
            f"{bad_dur} notes have non-positive duration (end <= start).")

    if lane_notes == 0:
        errors.append("No lane notes found (checked Expert 96-100).")

    if too_early:
        warnings.append(
            f"{too_early} notes start before {min_note_start:.2f}s. "
            "This may cause issues with some Clone Hero versions."
        )

    if sp_notes == 0:
        warnings.append(
            f"No Star Power notes found (expected SP pitch={sp_pitch}).")

    sections, track_loc = _parse_sections(notes_mid, pm)
    if not sections:
        warnings.append("No section markers found.")
    elif track_loc != "EVENTS":
        warnings.append(
            f"Sections found in '{track_loc}', but expected 'EVENTS' track.")

    # EXPERT TUNING: 16.0 NPS threshold
    spikes = _count_density_spikes(
        lane_note_starts, window_sec=1.0, nps_warn=16.0)
    if spikes > 0:
        warnings.append(
            f"Extreme density spikes detected (>= 16 NPS): {spikes}")

    ok = len(errors) == 0
    return ValidationResult(ok, errors, warnings)


def summarize(song_dir: Path, *, sp_pitch: int) -> None:
    notes_mid = _find_notes_mid(song_dir)
    if not notes_mid:
        print("No notes.mid to summarize.")
        return

    pm = pretty_midi.PrettyMIDI(str(notes_mid))
    guitar = _find_part_guitar(pm)
    if guitar is None:
        print('No "PART GUITAR" found to summarize.')
        return

    # Gather data per difficulty
    stats_by_diff = {
        name: {"notes": 0, "chords": 0, "lanes": {
            0: 0, 1: 0, 2: 0, 3: 0, 4: 0}}
        for name in ALL_DIFFS
    }

    # Pre-calc chords per diff
    starts_by_diff = {name: [] for name in ALL_DIFFS}

    sp_starts: list[float] = []
    sp_ends: list[float] = []

    for n in guitar.notes:
        p = int(n.pitch)

        # Check Star Power
        if p == sp_pitch:
            sp_starts.append(float(n.start))
            sp_ends.append(float(n.end))
            continue

        # Check Difficulties
        for name, r in ALL_DIFFS.items():
            if p in r:
                stats = stats_by_diff[name]
                stats["notes"] += 1
                lane_idx = p - r.start  # 96->0, 97->1, etc
                if lane_idx in stats["lanes"]:
                    stats["lanes"][lane_idx] += 1
                starts_by_diff[name].append(float(n.start))
                break

    # Calculate chords for each
    for name in ALL_DIFFS:
        stats_by_diff[name]["chords"] = _estimate_chords(starts_by_diff[name])

    print("\n--- CHART SUMMARY ---")
    print(f"Folder: {song_dir}")
    print("\nPART GUITAR Stats:")

    # Print table header
    print(f"  {'Difficulty':<10} | {'Notes':<6} | {'Chords':<6} | {'G':<4} {'R':<4} {'Y':<4} {'B':<4} {'O':<4}")
    print("  " + "-"*55)

    # Print rows (Expert -> Hard -> Med -> Easy)
    for name in ["Expert", "Hard", "Medium", "Easy"]:
        s = stats_by_diff[name]
        l = s["lanes"]
        print(
            f"  {name:<10} | {s['notes']:<6} | {s['chords']:<6} | {l[0]:<4} {l[1]:<4} {l[2]:<4} {l[3]:<4} {l[4]:<4}")

    sp_phrases = _group_sp_phrases(sp_starts, sp_ends, gap_join_sec=0.45)
    print(f"\nSTAR POWER: {len(sp_phrases)} phrases")
    if sp_phrases:
        for i, (s, e) in enumerate(sp_phrases, 1):
            print(f"    {i:02d}. {s:7.2f}s -> {e:7.2f}s  (len {e - s:5.2f}s)")

    sections, track_loc = _parse_sections(notes_mid, pm)
    print(f"\nSECTIONS:   {len(sections)} markers (in {track_loc})")

    if sections:
        for i, (name, t) in enumerate(sections, 1):
            print(f"    {i:02d}. {t:7.2f}s  {name}")


def validate_chart_file(song_dir: Path, summary_only: bool = False):
    res = validate_song_dir(song_dir, sp_pitch=DEFAULT_SP_PITCH)

    if res.errors:
        for e in res.errors:
            print(f"Error: {e}")

    if res.warnings:
        for w in res.warnings:
            print(f"Warning: {w}")

    if res.ok and not res.warnings:
        # FIXED: Replaced checkmark with [OK]
        print("\n[OK] Chart passed basic health check.")

    if summary_only:
        summarize(song_dir, sp_pitch=DEFAULT_SP_PITCH)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Sanity-check a Clone Hero output folder.")
    ap.add_argument("song_dir", type=str,
                    help="Path to the output song folder.")
    ap.add_argument("--sp-pitch", type=int,
                    default=DEFAULT_SP_PITCH, help="Star Power MIDI pitch.")
    ap.add_argument("--min-note-start", type=float,
                    default=DEFAULT_MIN_NOTE_START, help="Warn if notes start too early.")
    ap.add_argument("--summary", action="store_true", help="Print summary.")
    args = ap.parse_args()

    validate_chart_file(Path(args.song_dir), summary_only=args.summary)


if __name__ == "__main__":
    main()
