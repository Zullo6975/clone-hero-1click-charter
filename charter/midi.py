from __future__ import annotations

from pathlib import Path
import random

import pretty_midi

TRACK_NAME = "PART GUITAR"

LANE_PITCH = {
    0: 60,  # Green
    1: 61,  # Red
    2: 62,  # Yellow
    3: 63,  # Blue
    4: 64,  # Orange (never used)
}


def write_dummy_notes_mid(out_path: Path, bpm: float = 115.0, bars: int = 16, density: float = 0.55) -> None:
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

    last_lane = 1  # start at Red
    for beat in range(total_beats):
        # Decide how many "slots" this beat has: 1 (quarter) or 2 (eighths)
        slots = 2 if rng.random() < 0.35 else 1

        for s in range(slots):
            # Roll if we place a note in this slot
            # Lower density => fewer notes
            place = rng.random() < density * (0.75 if slots == 2 else 0.95)
            if not place:
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
                    w *= 0.5
                weights.append(w)

            lane = rng.choices(candidates, weights=weights, k=1)[0]
            last_lane = lane

            lanes = [lane]
            # Occasional simple 2-note chord, but only when density isn't too high
            if density < 0.70 and rng.random() < 0.10:
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
