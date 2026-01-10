from __future__ import annotations
from dataclasses import dataclass
import random

@dataclass
class StarPowerPhrase:
    start: float
    end: float

def generate_star_power_phrases(note_times: list[float], duration_sec: float) -> list[StarPowerPhrase]:
    """
    Generates Star Power (SP) phrases based on note density.
    - Finds dense regions (high NPS).
    - Places SP phrases of 4-8 seconds.
    - Ensures SP doesn't overlap or go past the last note.
    """
    if not note_times:
        return []

    # Safe boundaries based on actual notes
    first_note = note_times[0]
    last_note = note_times[-1]

    # 1. Calculate Density (1s windows)
    window_size = 1.0
    buckets = []
    t = first_note
    while t < last_note:
        count = sum(1 for n in note_times if t <= n < t + window_size)
        buckets.append((t, count))
        t += window_size

    if not buckets:
        return []

    # 2. Select candidates (Above average density)
    avg_density = sum(b[1] for b in buckets) / len(buckets) if buckets else 0
    candidates = [b for b in buckets if b[1] >= avg_density]

    # Sort by time to process sequentially
    candidates.sort(key=lambda x: x[0])

    phrases = []
    cooldown = 0.0

    # Target approx 1 phrase every 20-30 seconds
    target_gap = 25.0

    for cand_t, _ in candidates:
        if cand_t < cooldown:
            continue

        # Determine length (randomly 4s to 8s)
        length = random.uniform(4.0, 8.0)

        start_t = cand_t
        end_t = start_t + length

        # Clamp to last note! (Critical Fix)
        if end_t > last_note:
            end_t = last_note
            # If clamping makes it tiny, skip it
            if end_t - start_t < 2.0:
                continue

        phrases.append(StarPowerPhrase(start_t, end_t))
        cooldown = end_t + target_gap

    # If we didn't generate enough (short/sparse songs), fallback to periodic
    if len(phrases) < 2 and duration_sec > 60:
        phrases = []
        cursor = first_note + 15.0
        while cursor < last_note - 10.0:
            end = min(cursor + 6.0, last_note)
            phrases.append(StarPowerPhrase(cursor, end))
            cursor += 35.0

    return phrases
