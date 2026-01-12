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

def _map_to_target(notes: list, target_diff: str) -> list:
    new_notes = []
    # Target map: e.g. Medium {0:72, 1:73, 2:74, 3:75, 4:76}
    target_map = DIFFICULTY_PITCHES[target_diff]
    max_lane = max(target_map.keys()) # e.g. 4 for Medium

    if not notes: return []

    # Identify source difficulty base pitch (Expert=96, Hard=84, etc)
    first_p = notes[0].pitch
    base_pitch = 96
    if 84 <= first_p <= 88: base_pitch = 84
    elif 72 <= first_p <= 76: base_pitch = 72
    elif 60 <= first_p <= 64: base_pitch = 60

    for n in notes:
        # Determine current lane (0-4)
        lane = n.pitch - base_pitch

        # Shift down if outside target range (e.g. Orange in Easy)
        if lane > max_lane:
            lane = max_lane

        # "Too Many Blues" Fix for Medium/Easy:
        # Randomly shift highest lane down sometimes to reduce density of "hard" notes
        if target_diff in ["Medium", "Easy"] and lane == max_lane:
            # 40% chance to shift Blue->Yellow (Med) or Yellow->Red (Easy)
            if random.random() < 0.40:
                lane -= 1

        if lane in target_map:
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

    # Max 2-note chords for Hard
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

    # FORCE DIFFERENCE: If Hard == Expert, aggressively thin it out (every 4th note)
    if len(final_notes) >= len(expert_notes) * 0.95:
        thinned = []
        for i, n in enumerate(final_notes):
            if i % 4 != 0:
                thinned.append(n)
        final_notes = thinned

    return final_notes

def reduce_to_medium(hard_notes: list, min_gap_ms: int = 220) -> list:
    """
    Hard -> Medium
    - No Chords.
    - Limits Orange notes to MAX 5.
    """
    base = _map_to_target(hard_notes, "Medium")
    if not base: return []

    filtered = []
    last_start = -1.0
    min_gap_sec = min_gap_ms / 1000.0

    base.sort(key=lambda x: x.start)

    # 1. Filter for time (density)
    for n in base:
        if abs(n.start - last_start) < 0.05: continue # No chords
        if n.start - last_start >= min_gap_sec:
            filtered.append(n)
            last_start = n.start

    # 2. Orange Cap Logic & Scattering
    orange_indices = []
    base_pitch = 72 # Medium starts at 72

    for i, n in enumerate(filtered):
        lane = n.pitch - base_pitch
        if lane == 4: # Orange
            orange_indices.append(i)

    # Keep 5 random ones, scatter the rest to ANY lower lane (not just blue)
    if len(orange_indices) > 5:
        to_keep = set(random.sample(orange_indices, 5))
        for i in orange_indices:
            if i not in to_keep:
                # Scatter logic: Shift Orange to 1 (Red), 2 (Yellow), or 3 (Blue)
                # Weighted slightly towards Blue to keep intensity
                new_lane = random.choices([0, 1, 2, 3], weights=[0.2, 0.3, 0.4, 0.1], k=1)[0]
                filtered[i].pitch = base_pitch + new_lane

    return filtered

def reduce_to_easy(medium_notes: list, min_gap_ms: int = 450) -> list:
    """
    Medium -> Easy
    - No Chords.
    - Compresses 4 lanes to 3.
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
