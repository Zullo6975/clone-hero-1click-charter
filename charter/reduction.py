from __future__ import annotations
import copy
import random
from charter.config import DIFFICULTY_PITCHES

# Lane indices
LANE_G = 0
LANE_R = 1
LANE_Y = 2
LANE_B = 3
LANE_O = 4

def _get_lane_from_pitch(pitch: int, diff_name: str) -> int | None:
    mapping = DIFFICULTY_PITCHES.get(diff_name, {})
    for lane_idx, midi_val in mapping.items():
        if midi_val == pitch:
            return lane_idx
    return None

def _map_to_target(notes: list, target_diff: str) -> list:
    new_notes = []
    target_map = DIFFICULTY_PITCHES[target_diff]

    if not notes: return []

    first_p = notes[0].pitch
    source_diff = "Expert"
    if 84 <= first_p <= 88: source_diff = "Hard"
    elif 72 <= first_p <= 76: source_diff = "Medium"

    for n in notes:
        lane = _get_lane_from_pitch(n.pitch, source_diff)
        if lane is not None and lane in target_map:
            new_note = copy.copy(n)
            new_note.pitch = target_map[lane]
            new_notes.append(new_note)

    return new_notes

def reduce_to_hard(expert_notes: list, min_gap_ms: int = 120) -> list:
    """
    Expert -> Hard
    min_gap_ms: Minimum time (ms) between notes.
    """
    base = _map_to_target(expert_notes, "Hard")
    if not base: return []

    filtered = []
    last_start = -1.0
    min_gap_sec = min_gap_ms / 1000.0

    base.sort(key=lambda x: x.start)

    for n in base:
        # Allow chords (same start time)
        if abs(n.start - last_start) < 0.01:
            filtered.append(n)
            continue

        if n.start - last_start >= min_gap_sec:
            filtered.append(n)
            last_start = n.start

    # Max 2-note chords
    final_notes = []
    chord_groups = {}
    for n in filtered:
        t_key = round(n.start, 3)
        chord_groups.setdefault(t_key, []).append(n)

    for t in sorted(chord_groups.keys()):
        chord = chord_groups[t]
        if len(chord) > 2:
            chord = chord[:2]
        final_notes.extend(chord)

    return final_notes

def reduce_to_medium(hard_notes: list, min_gap_ms: int = 220) -> list:
    """
    Hard -> Medium
    - Orange is now ALLOWED (but rare due to density filters).
    - Max 1/8th note density.
    - No Chords (Single notes only).
    """
    base = _map_to_target(hard_notes, "Medium")
    if not base: return []

    # REMOVED: The explicit "no_orange" filter.
    # Orange notes will now survive if they are spaced out enough.

    filtered = []
    last_start = -1.0
    min_gap_sec = min_gap_ms / 1000.0

    base.sort(key=lambda x: x.start)

    for n in base:
        # Collapse chords (Single notes only)
        if abs(n.start - last_start) < 0.05:
            continue

        if n.start - last_start >= min_gap_sec:
            filtered.append(n)
            last_start = n.start

    return filtered

def reduce_to_easy(medium_notes: list, min_gap_ms: int = 450) -> list:
    """
    Medium -> Easy
    min_gap_ms: Minimum time (ms) between notes.
    """
    base = _map_to_target(medium_notes, "Easy")
    if not base: return []

    filtered = []
    last_start = -1.0
    min_gap_sec = min_gap_ms / 1000.0

    base.sort(key=lambda x: x.start)

    for n in base:
        # No chords
        if abs(n.start - last_start) < 0.05:
            continue

        if n.start - last_start >= min_gap_sec:
            filtered.append(n)
            last_start = n.start

    return filtered
