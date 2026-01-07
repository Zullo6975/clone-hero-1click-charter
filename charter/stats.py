from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import pretty_midi  # type: ignore


# Clone Hero lead guitar track name we generate
TRACK_NAME = "PART GUITAR"

# Our lane pitches (G,R,Y,B,O) — used only for lane counting
PITCH_TO_LANE = {
    60: 0,  # G
    61: 1,  # R
    62: 2,  # Y
    63: 3,  # B
    64: 4,  # O
}


@dataclass(frozen=True)
class WindowStats:
    start: float
    end: float
    notes: int
    chords: int
    sustains: int
    max_nps_1s: float  # max notes/sec in any 1s inside this window


@dataclass(frozen=True)
class ChartStats:
    # identity
    title: str
    artist: str
    mode: str

    # time
    song_duration_sec: float
    chart_duration_sec: float

    # totals
    total_notes: int
    total_chords: int
    total_sustains: int
    sustain_ratio: float

    # difficulty-ish
    max_nps_1s: float
    avg_nps: float

    # lanes
    lane_counts: dict[str, int]  # {"G":..., "R":..., ...}

    # sections
    window_sec: float
    windows: list[WindowStats]


def _safe_float(x: float) -> float:
    return float(f"{x:.6f}")


def _get_track(pm: pretty_midi.PrettyMIDI) -> pretty_midi.Instrument | None:
    # Prefer exact name match, else first instrument
    for inst in pm.instruments:
        if (inst.name or "").strip() == TRACK_NAME:
            return inst
    return pm.instruments[0] if pm.instruments else None


def _notes_by_time(notes: list[pretty_midi.Note]) -> list[pretty_midi.Note]:
    return sorted(notes, key=lambda n: (n.start, n.pitch, n.end))


def _group_chords(notes: list[pretty_midi.Note], *, tol: float = 0.001) -> list[list[pretty_midi.Note]]:
    """
    Group notes into "chords" by start time.
    tol lets us tolerate tiny floating point jitter.
    """
    notes = _notes_by_time(notes)
    groups: list[list[pretty_midi.Note]] = []
    cur: list[pretty_midi.Note] = []
    cur_t: float | None = None

    for n in notes:
        if cur_t is None:
            cur_t = n.start
            cur = [n]
            continue

        if abs(n.start - cur_t) <= tol:
            cur.append(n)
        else:
            groups.append(cur)
            cur_t = n.start
            cur = [n]

    if cur:
        groups.append(cur)

    return groups


def _rolling_max_nps(note_starts: list[float]) -> float:
    """
    Compute max notes/sec over a rolling 1s window using note start times.
    """
    if not note_starts:
        return 0.0

    starts = sorted(note_starts)
    j = 0
    best = 0

    for i in range(len(starts)):
        t0 = starts[i]
        # advance j while within 1.0s window [t0, t0+1)
        while j < len(starts) and starts[j] < t0 + 1.0:
            j += 1
        best = max(best, j - i)

    return float(best)  # notes within 1 second


def _lane_counts(notes: list[pretty_midi.Note]) -> dict[str, int]:
    out = {"G": 0, "R": 0, "Y": 0, "B": 0, "O": 0, "?": 0}
    for n in notes:
        lane = PITCH_TO_LANE.get(int(n.pitch))
        if lane == 0:
            out["G"] += 1
        elif lane == 1:
            out["R"] += 1
        elif lane == 2:
            out["Y"] += 1
        elif lane == 3:
            out["B"] += 1
        elif lane == 4:
            out["O"] += 1
        else:
            out["?"] += 1
    return out


def compute_chart_stats(
    *,
    notes_mid_path: Path,
    title: str,
    artist: str,
    mode: str,
    song_duration_sec: float | None = None,
    window_sec: float = 15.0,
    sustain_ms_threshold: int = 220,
) -> ChartStats:
    """
    Compute useful stats from notes.mid (no audio required).
    If you can provide song_duration_sec from librosa, do it (nicer).
    """
    pm = pretty_midi.PrettyMIDI(str(notes_mid_path))
    track = _get_track(pm)

    notes: list[pretty_midi.Note] = []
    if track:
        notes = list(track.notes)

    notes = _notes_by_time(notes)
    starts = [float(n.start) for n in notes]
    chords = _group_chords(notes)

    total_notes = len(notes)
    total_chords = sum(1 for g in chords if len(g) >= 2)
    total_sustains = sum(1 for n in notes if (n.end - n.start) * 1000.0 >= sustain_ms_threshold)

    chart_end = 0.0
    if notes:
        chart_end = max(float(n.end) for n in notes)

    # whole-chart NPS
    max_notes_in_1s = _rolling_max_nps(starts)
    max_nps_1s = float(max_notes_in_1s)  # notes in 1 second window == NPS

    chart_duration = max(0.0, chart_end - (min(starts) if starts else 0.0))
    avg_nps = (total_notes / chart_duration) if chart_duration > 0 else 0.0

    # windows (fixed buckets, GH-ish "section stats")
    w = max(5.0, float(window_sec))
    effective_duration = float(song_duration_sec) if song_duration_sec and song_duration_sec > 0 else chart_end
    num_windows = int(effective_duration // w) + 1 if effective_duration > 0 else 0

    windows: list[WindowStats] = []
    for i in range(num_windows):
        a = i * w
        b = min((i + 1) * w, effective_duration)
        if b <= a:
            continue

        # notes in this bucket by start time
        bucket_notes = [n for n in notes if a <= float(n.start) < b]
        bucket_starts = [float(n.start) for n in bucket_notes]
        bucket_chords = _group_chords(bucket_notes)
        bucket_chord_count = sum(1 for g in bucket_chords if len(g) >= 2)
        bucket_sustains = sum(
            1 for n in bucket_notes if (n.end - n.start) * 1000.0 >= sustain_ms_threshold
        )

        bucket_max_nps = _rolling_max_nps(bucket_starts)

        windows.append(
            WindowStats(
                start=_safe_float(a),
                end=_safe_float(b),
                notes=len(bucket_notes),
                chords=bucket_chord_count,
                sustains=bucket_sustains,
                max_nps_1s=float(bucket_max_nps),
            )
        )

    sustain_ratio = (total_sustains / total_notes) if total_notes else 0.0

    return ChartStats(
        title=title,
        artist=artist,
        mode=mode,
        song_duration_sec=_safe_float(float(song_duration_sec) if song_duration_sec else 0.0),
        chart_duration_sec=_safe_float(chart_end),
        total_notes=total_notes,
        total_chords=total_chords,
        total_sustains=total_sustains,
        sustain_ratio=_safe_float(sustain_ratio),
        max_nps_1s=_safe_float(max_nps_1s),
        avg_nps=_safe_float(avg_nps),
        lane_counts=_lane_counts(notes),
        window_sec=_safe_float(w),
        windows=windows,
    )


def write_stats_json(out_path: Path, stats: ChartStats) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = asdict(stats)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def format_stats_summary(stats: ChartStats) -> str:
    lanes = stats.lane_counts
    lane_str = f"G{lanes['G']} R{lanes['R']} Y{lanes['Y']} B{lanes['B']} O{lanes['O']}"
    return (
        f"Stats\n"
        f"- Notes: {stats.total_notes} (chords: {stats.total_chords}, sustains: {stats.total_sustains}, sustain%: {stats.sustain_ratio:.2f})\n"
        f"- Max NPS (1s): {stats.max_nps_1s:.2f} | Avg NPS: {stats.avg_nps:.2f}\n"
        f"- Lanes: {lane_str}\n"
        f"- Chart end: {stats.chart_duration_sec:.2f}s\n"
        f"- Sections: {len(stats.windows)} @ {stats.window_sec:.0f}s\n"
    )
