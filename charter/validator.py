from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import pretty_midi  # type: ignore
import mido  # type: ignore

# ---- Your chart conventions ----
TRACK_NAME = "PART GUITAR"
LANE_PITCHES = {72, 73, 74, 75, 76}
ORANGE_PITCH = 76
DEFAULT_MIN_NOTE_START = 1.0
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


def _count_density_spikes(note_starts: list[float], window_sec: float = 1.0, nps_warn: float = 9.0) -> int:
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
    """
    Scans the raw MIDI file for Text or Lyric events starting with 'section '.
    Returns (list_of_sections, track_name_info)
    """
    out: list[tuple[str, float]] = []
    found_in_track_name = None

    try:
        mid = mido.MidiFile(str(midi_path))

        for i, track in enumerate(mid.tracks):
            track_name = f"Track {i}"
            # Check for track name event first
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
                        clean_name = text.replace("[section ", "").replace("]", "").strip()
                        is_sec = True

                    if is_sec:
                        if found_in_track_name is None: found_in_track_name = track_name
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
        warnings.append("Missing song.ini (Clone Hero will usually require this).")
    if not _find_audio(song_dir):
        warnings.append("No audio file found (expected song.ogg/mp3/wav/flac).")

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
            errors.append(f"Note starts before 0.0s: pitch={n.pitch} start={n.start:.3f}")
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
        errors.append(f"{bad_dur} notes have non-positive duration (end <= start).")

    if lane_notes == 0:
        errors.append("No lane notes found in PART GUITAR (expected Medium pitches 72–76).")

    if too_early:
        warnings.append(
            f"{too_early} notes start before {min_note_start:.2f}s. "
            "Not always fatal, but many CH charts start at ~1.0s."
        )

    if sp_notes == 0:
        warnings.append(f"No Star Power notes found (expected SP pitch={sp_pitch}).")

    if orange_notes > 0:
        warnings.append(f"{orange_notes} orange notes found!")

    sections, track_loc = _parse_sections(notes_mid, pm)
    if not sections:
        warnings.append("No section markers found.")
    elif track_loc != "EVENTS":
        warnings.append(f"Sections found in '{track_loc}', but expected 'EVENTS' track.")

    spikes = _count_density_spikes(lane_note_starts, window_sec=1.0, nps_warn=9.0)
    if spikes > 0:
        warnings.append(f"High-density spikes detected (>= 9 NPS): {spikes}")

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

    lane_note_starts: list[float] = []
    sp_starts: list[float] = []
    sp_ends: list[float] = []

    # Map for Medium Difficulty (72-76)
    lane_pitch_counts = {72: 0, 73: 0, 74: 0, 75: 0, 76: 0}

    for n in guitar.notes:
        if n.pitch in LANE_PITCHES:
            lane_note_starts.append(float(n.start))
            if n.pitch in lane_pitch_counts:
                lane_pitch_counts[n.pitch] += 1
        elif n.pitch == sp_pitch:
            sp_starts.append(float(n.start))
            sp_ends.append(float(n.end))

    chords_est = _estimate_chords(lane_note_starts)
    total_lane = len(lane_note_starts)

    sections, track_loc = _parse_sections(notes_mid, pm)
    sp_phrases = _group_sp_phrases(sp_starts, sp_ends, gap_join_sec=0.45)

    print("\n--- SUMMARY (Medium Difficulty) ---")
    print(f"Folder: {song_dir}")
    print("\nPART GUITAR:")
    print(f"  Lane notes: {total_lane}")
    print(f"  Chords (est): {chords_est}")
    print("  Lane counts:")
    print(f"    Green(72):  {lane_pitch_counts[72]}")
    print(f"    Red(73):    {lane_pitch_counts[73]}")
    print(f"    Yellow(74): {lane_pitch_counts[74]}")
    print(f"    Blue(75):   {lane_pitch_counts[75]}")
    print(f"    Orange(76): {lane_pitch_counts[76]}")

    print("\nSTAR POWER:")
    print(f"  Phrases:  {len(sp_phrases)}")
    if sp_phrases:
        for i, (s, e) in enumerate(sp_phrases[:12], 1):
            print(f"    {i:02d}. {s:7.2f}s -> {e:7.2f}s  (len {e - s:5.2f}s)")
        if len(sp_phrases) > 12:
            print(f"    ...and {len(sp_phrases) - 12} more")

    print(f"\nSECTIONS (Found in {track_loc}):")
    print(f"  Markers: {len(sections)}")
    if sections:
        for i, (name, t) in enumerate(sections[:18], 1):
            print(f"    {i:02d}. {t:7.2f}s  {name}")
        if len(sections) > 18:
            print(f"    ...and {len(sections) - 18} more")

    if lane_note_starts:
        starts = sorted(lane_note_starts)
        print("\nTIMELINE (lane note starts):")
        print(f"  First: {starts[0]:.2f}s   Median: {starts[len(starts)//2]:.2f}s   Last: {starts[-1]:.2f}s")


def validate_chart_file(song_dir: Path, summary_only: bool = False):
    print(f"DEBUG: Validator started for {song_dir.name}", flush=True)
    res = validate_song_dir(song_dir, sp_pitch=DEFAULT_SP_PITCH)

    if res.errors:
        for e in res.errors:
            print(f"Error: {e}")

    if res.warnings:
        for w in res.warnings:
            print(f"Warning: {w}")

    if res.ok and not res.warnings:
        print("\n✅ Chart passed basic health check.")

    if summary_only or True:
        summarize(song_dir, sp_pitch=DEFAULT_SP_PITCH)


def main() -> None:
    ap = argparse.ArgumentParser(description="Sanity-check a Clone Hero output folder.")
    ap.add_argument("song_dir", type=str, help="Path to the output song folder.")
    ap.add_argument("--sp-pitch", type=int, default=DEFAULT_SP_PITCH, help="Star Power MIDI pitch.")
    ap.add_argument("--min-note-start", type=float, default=DEFAULT_MIN_NOTE_START, help="Warn if notes start too early.")
    ap.add_argument("--summary", action="store_true", help="Print summary.")
    args = ap.parse_args()

    validate_chart_file(Path(args.song_dir), summary_only=args.summary)


if __name__ == "__main__":
    main()
