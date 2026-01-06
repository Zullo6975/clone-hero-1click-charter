from __future__ import annotations

from pathlib import Path
import random

import pretty_midi  # type: ignore
import librosa  # type: ignore

from charter.audio import detect_onsets, OnsetCandidate

# Keep this EXACTLY as your known-good baseline for now
TRACK_NAME = "PART GUITAR"

LANE_PITCH = {
    0: 60,  # Green
    1: 61,  # Red
    2: 62,  # Yellow
    3: 63,  # Blue
    4: 64,  # Orange (never used)
}


def _filter_onsets_windowed(
    candidates: list[OnsetCandidate],
    *,
    duration_sec: float,
    window_sec: float,
    min_gap_ms: int,
    max_nps: float,
    min_notes_per_window: int,
) -> list[OnsetCandidate]:
    """
    Windowed onset selection for full-song coverage.

    - Split song into windows (e.g., 4s)
    - Pick strongest onsets per window up to a quota
    - Enforce min gap between selected notes
    - If a window would have 0 notes, inject 1 "filler" note
      at the window midpoint (strength=0.0)
    """
    if window_sec <= 0:
        window_sec = 4.0

    min_gap = max(0.03, min_gap_ms / 1000.0)
    quota = max(1, int(round(max_nps * window_sec)))
    min_notes_per_window = max(0, int(min_notes_per_window))

    # group candidates by window index
    buckets: dict[int, list[OnsetCandidate]] = {}
    for c in candidates:
        idx = int(c.t // window_sec)
        buckets.setdefault(idx, []).append(c)

    selected: list[OnsetCandidate] = []

    def too_close(t: float) -> bool:
        return any(abs(s.t - t) < min_gap for s in selected)

    num_windows = int(duration_sec // window_sec) + 1

    for w in range(num_windows):
        items = buckets.get(w, [])
        # strongest first
        items_sorted = sorted(items, key=lambda x: x.strength, reverse=True)

        picked_this_window: list[OnsetCandidate] = []
        for c in items_sorted:
            if len(picked_this_window) >= quota:
                break
            if too_close(c.t):
                continue
            picked_this_window.append(c)
            selected.append(c)

        # Ensure some coverage (optional but fixes "cuts off")
        if len(picked_this_window) < min_notes_per_window:
            # insert a synthetic "tap" near the middle of the window
            mid = (w * window_sec) + (window_sec * 0.5)
            # don't add near the very start; avoid t<1.0 since we clamp to 1.0 anyway
            if mid >= 1.0 and mid <= duration_sec - 0.5 and not too_close(mid):
                filler = OnsetCandidate(t=float(mid), strength=0.0)
                selected.append(filler)

    selected.sort(key=lambda c: c.t)
    return selected


def _assign_lanes(times: list[float], *, seed: int = 42) -> list[int]:
    """
    Conservative lane assignment:
    - no orange
    - bias repeats and +/-1 movement
    - blue rarer
    """
    rng = random.Random(seed)
    last_lane = 1
    out: list[int] = []

    for _t in times:
        candidates = [0, 1, 2, 3]
        weights = []
        for lane in candidates:
            move = abs(lane - last_lane)
            if move == 0:
                w = 3.0
            elif move == 1:
                w = 2.2
            elif move == 2:
                w = 1.0
            else:
                w = 0.5
            if lane == 3:
                w *= 0.6
            weights.append(w)

        lane = rng.choices(candidates, weights=weights, k=1)[0]
        out.append(lane)
        last_lane = lane

    return out


def write_real_notes_mid(
    *,
    audio_path: Path,
    out_path: Path,
    min_gap_ms: int = 140,
    max_nps: float = 3.8,
    seed: int = 42,
    tap_duration: float = 0.10,
    bpm: float = 120.0,
    window_sec: float = 4.0,
    min_notes_per_window: int = 1,
) -> None:
    """
    Real chart v1:
      audio -> onsets -> windowed filtering (coverage) -> lanes -> notes.mid

    Changes vs v0:
    - ensures coverage across the full song (prevents "cuts off")
    - caps note lengths to feel like taps (prevents long sustains)
    """
    candidates = detect_onsets(audio_path)

    # Get duration for coverage windows
    duration_sec = float(librosa.get_duration(path=str(audio_path)))

    kept = _filter_onsets_windowed(
        candidates,
        duration_sec=duration_sec,
        window_sec=window_sec,
        min_gap_ms=min_gap_ms,
        max_nps=max_nps,
        min_notes_per_window=min_notes_per_window,
    )

    times = [c.t for c in kept]
    lanes = _assign_lanes(times, seed=seed)

    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=0, name=TRACK_NAME)

    # cap note duration against next note so nothing becomes a huge sustain
    for i, (t, lane) in enumerate(zip(times, lanes)):
        start = max(1.0, float(t))
        next_start = float(times[i + 1]) if i + 1 < len(times) else (start + 999.0)

        end = start + float(tap_duration)
        end = min(end, max(start + 0.05, next_start - 0.03))  # keep tap-like, avoid overlap

        pitch = LANE_PITCH[int(lane)]
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=start, end=end))

    pm.instruments.append(inst)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(out_path))


def write_dummy_notes_mid(
    out_path: Path,
    bpm: float = 115.0,
    bars: int = 24,
    density: float = 0.58,
) -> None:
    """
    Dummy chart for compatibility + baseline feel testing.
    density in [0..1]: lower = fewer notes (easier).
    """
    density = max(0.05, min(1.0, float(density)))
    rng = random.Random(42)

    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=0, name=TRACK_NAME)

    spb = 60.0 / bpm
    total_beats = bars * 4

    # We place events on a mixed grid: mostly quarter notes, occasional eighths.
    # Start after 1s so the audio "settles".
    t = 1.0
    last_lane = 1  # start Red

    for _beat in range(total_beats):
        # More eighths as density rises (but still controlled)
        eighth_prob = 0.25 + 0.45 * density  # 0.38-ish @ 0.58 density
        slots = 2 if rng.random() < eighth_prob else 1

        for _s in range(slots):
            # Roll if we place a note in this slot
            # Lower density => fewer notes
            place_prob = density * (0.70 if slots == 2 else 0.90)
            if rng.random() >= place_prob:
                t += spb / slots
                continue

            # Choose lane with movement bias (prefer repeats / +/-1)
            candidates = [0, 1, 2, 3]  # no orange
            weights = []
            for lane in candidates:
                move = abs(lane - last_lane)
                if move == 0:
                    w = 3.0
                elif move == 1:
                    w = 2.2
                elif move == 2:
                    w = 1.0
                else:
                    w = 0.5
                # Keep Blue rarer
                if lane == 3:
                    w *= 0.6
                weights.append(w)

            lane = rng.choices(candidates, weights=weights, k=1)[0]
            last_lane = lane

            lanes = [lane]
            # Occasional simple 2-note chord, but only when density isn't too high
            if density < 0.72 and rng.random() < (0.06 + 0.06 * density):
                chord_options = [(0, 1), (1, 2), (2, 3), (0, 2), (1, 3)]
                # Prefer chords involving current lane
                cand = [c for c in chord_options if lane in c] or chord_options
                a, b = rng.choice(cand)
                lanes = [a, b]

            dur = 0.18 if slots == 2 else 0.22
            for ln in lanes:
                inst.notes.append(pretty_midi.Note(velocity=100, pitch=LANE_PITCH[ln], start=t, end=t + dur))

            t += spb / slots

        # Ensure we end exactly on beat boundary if slots==2 caused rounding drift
        # (tiny drift doesn’t matter much, but keep it tidy)
        # no-op for simplicity
    pm.instruments.append(inst)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(out_path))
