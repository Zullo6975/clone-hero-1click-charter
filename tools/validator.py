from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import pretty_midi  # type: ignore


# ---- Your chart conventions ----
TRACK_NAME = "PART GUITAR"
LANE_PITCHES = {60, 61, 62, 63, 64}  # G R Y B O
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
    """
    SP notes are written as contiguous ranges (start->end).
    We group nearby SP notes into 'phrases' so you can count them.
    gap_join_sec: if the next SP note starts within this gap, treat as same phrase.
    """
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


def _parse_sections(pm: pretty_midi.PrettyMIDI) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for ly in getattr(pm, "lyrics", []) or []:
        text = getattr(ly, "text", "")
        t = float(getattr(ly, "time", 0.0))
        if isinstance(text, str) and text.lower().startswith("[section "):
            out.append((text.strip(), t))
    out.sort(key=lambda x: x[1])
    return out


def _estimate_chords(lane_note_starts: list[float], tol: float = 0.012) -> int:
    """
    A chord is multiple lane notes starting at ~same time.
    We estimate by bucketing start times within tolerance.
    """
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
            if n.pitch == 64:
                orange_notes += 1
            lane_note_starts.append(float(n.start))
        elif n.pitch == sp_pitch:
            sp_notes += 1
            sp_starts.append(float(n.start))
            sp_ends.append(float(n.end))
        else:
            # Not necessarily wrong, but likely noise.
            warnings.append(f"Unexpected pitch in PART GUITAR: {n.pitch} at {n.start:.3f}s")

    if bad_dur:
        errors.append(f"{bad_dur} notes have non-positive duration (end <= start).")

    if lane_notes == 0:
        errors.append("No lane notes found in PART GUITAR (expected pitches 60–64).")

    if too_early:
        warnings.append(
            f"{too_early} notes start before {min_note_start:.2f}s. "
            "Not always fatal, but many CH charts start at ~1.0s."
        )

    if sp_notes == 0:
        warnings.append(f"No Star Power notes found (expected SP pitch={sp_pitch}).")

    if orange_notes > 0:
        warnings.append(f"Orange notes present: {orange_notes} (OK).")

    sections = _parse_sections(pm)
    if not sections:
        warnings.append("No [section ...] markers found in MIDI lyrics (optional but nice).")

    spikes = _count_density_spikes(lane_note_starts, window_sec=1.0, nps_warn=9.0)
    if spikes > 0:
        warnings.append(f"High-density spikes detected (>= 9 NPS in a 1s window): {spikes} (warning only).")

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

    lane_pitch_counts = {60: 0, 61: 0, 62: 0, 63: 0, 64: 0}

    for n in guitar.notes:
        if n.pitch in LANE_PITCHES:
            lane_note_starts.append(float(n.start))
            lane_pitch_counts[n.pitch] = lane_pitch_counts.get(n.pitch, 0) + 1
        elif n.pitch == sp_pitch:
            sp_starts.append(float(n.start))
            sp_ends.append(float(n.end))

    chords_est = _estimate_chords(lane_note_starts)
    total_lane = len(lane_note_starts)

    sections = _parse_sections(pm)
    sp_phrases = _group_sp_phrases(sp_starts, sp_ends, gap_join_sec=0.45)

    print("\n--- SUMMARY ---")
    print(f"Folder: {song_dir}")
    print(f"notes.mid: {notes_mid.name}")

    song_ini = _find_song_ini(song_dir)
    audio = _find_audio(song_dir)
    print(f"song.ini: {'YES' if song_ini else 'NO'}")
    print(f"audio:    {audio.name if audio else 'NOT FOUND'}")

    print("\nPART GUITAR:")
    print(f"  Lane notes: {total_lane}")
    print(f"  Chords (est): {chords_est}")
    print("  Lane counts:")
    print(f"    Green(60):  {lane_pitch_counts[60]}")
    print(f"    Red(61):    {lane_pitch_counts[61]}")
    print(f"    Yellow(62): {lane_pitch_counts[62]}")
    print(f"    Blue(63):   {lane_pitch_counts[63]}")
    print(f"    Orange(64): {lane_pitch_counts[64]}")

    print("\nSTAR POWER:")
    print(f"  SP pitch: {sp_pitch}")
    print(f"  SP notes: {len(sp_starts)}")
    print(f"  Phrases:  {len(sp_phrases)}")
    if sp_phrases:
        for i, (s, e) in enumerate(sp_phrases[:12], 1):
            print(f"    {i:02d}. {s:7.2f}s → {e:7.2f}s  (len {e - s:5.2f}s)")
        if len(sp_phrases) > 12:
            print(f"    …and {len(sp_phrases) - 12} more")

    print("\nSECTIONS:")
    print(f"  Markers: {len(sections)}")
    if sections:
        for i, (name, t) in enumerate(sections[:18], 1):
            print(f"    {i:02d}. {t:7.2f}s  {name}")
        if len(sections) > 18:
            print(f"    …and {len(sections) - 18} more")

    # Small timeline peek
    if lane_note_starts:
        starts = sorted(lane_note_starts)
        print("\nTIMELINE (lane note starts):")
        print(f"  First: {starts[0]:.2f}s   Median: {starts[len(starts)//2]:.2f}s   Last: {starts[-1]:.2f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description="Sanity-check a Clone Hero output folder without opening Clone Hero.")
    ap.add_argument("song_dir", type=str, help="Path to the output song folder (contains notes.mid, song.ini, audio).")
    ap.add_argument("--sp-pitch", type=int, default=DEFAULT_SP_PITCH, help="Star Power MIDI pitch (default: 116).")
    ap.add_argument("--min-note-start", type=float, default=DEFAULT_MIN_NOTE_START, help="Warn if notes start before this time.")
    ap.add_argument("--summary", action="store_true", help="Print summary (sections, SP phrases, lane counts).")
    args = ap.parse_args()

    song_dir = Path(args.song_dir).expanduser().resolve()

    res = validate_song_dir(song_dir, sp_pitch=int(args.sp_pitch), min_note_start=float(args.min_note_start))

    print(f"\n== Validate: {song_dir} ==")
    if res.errors:
        print("\nERRORS:")
        for e in res.errors:
            print(f"  - {e}")

    if res.warnings:
        print("\nWARNINGS:")
        for w in res.warnings:
            print(f"  - {w}")

    if args.summary:
        summarize(song_dir, sp_pitch=int(args.sp_pitch))

    if res.ok:
        print("\n✅ OK: looks structurally sane for Clone Hero (best-effort).")
        sys.exit(0)
    else:
        print("\n❌ FAIL: fix errors above before bothering with Clone Hero.")
        sys.exit(1)


if __name__ == "__main__":
    main()