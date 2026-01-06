from __future__ import annotations

from pathlib import Path

import pretty_midi

TRACK_NAME = "PART GUITAR"

# Common 5-fret mapping (Clone Hero-compatible in most setups/tools)
LANE_PITCH = {
    0: 60,  # Green
    1: 61,  # Red
    2: 62,  # Yellow
    3: 63,  # Blue
    4: 64,  # Orange (we won't use)
}


def write_dummy_notes_mid(out_path: Path, bpm: float = 120.0, bars: int = 16) -> None:
    """
    Writes a tiny, deterministic 'dummy' chart that should load in Clone Hero.
    This is purely to validate the export pipeline.
    """
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=0, name=TRACK_NAME)

    seconds_per_beat = 60.0 / bpm
    total_beats = bars * 4

    # Simple pattern: alternating single notes, occasional 2-note chords
    pattern = [
        ([0], 0.18),        # G
        ([1], 0.18),        # R
        ([2], 0.18),        # Y
        ([1, 2], 0.22),     # R+Y chord
        ([0], 0.18),        # G
        ([2], 0.18),        # Y
        ([3], 0.18),        # B
        ([1, 3], 0.22),     # R+B spaced chord (allowed boundary)
    ]

    t = 1.0  # start after 1s so the song has time to "begin"
    for i in range(total_beats * 2):  # 8th notes
        lanes, dur = pattern[i % len(pattern)]
        for lane in lanes:
            pitch = LANE_PITCH[lane]
            inst.notes.append(pretty_midi.Note(velocity=100, pitch=pitch, start=t, end=t + dur))
        t += seconds_per_beat / 2.0  # eighth note step

    pm.instruments.append(inst)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pm.write(str(out_path))
