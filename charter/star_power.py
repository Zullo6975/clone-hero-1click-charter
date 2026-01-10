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
    - Ensures SP ends BEFORE the last note to allow activation time.
    """
    if not note_times:
        return []

    # Safe boundaries
    first_note = note_times[0]
    last_note = note_times[-1]

    # User Request: Avoid the very last note
    # Give a 2.5 second buffer at the end of the chart
    valid_end_zone = last_note - 2.5

    # 1. Calculate Density (1s windows)
    window_size = 1.0
    buckets = []
    t = first_note
    while t < valid_end_zone:
        count = sum(1 for n in note_times if t <= n < t + window_size)
        buckets.append((t, count))
        t += window_size

    if not buckets:
        return []

    # 2. Select candidates (Above average density)
    avg_density = sum(b[1] for b in buckets) / len(buckets) if buckets else 0
    # Lower threshold slightly to allow more phrases in sparse songs
    threshold = avg_density * 0.8
    candidates = [b for b in buckets if b[1] >= threshold]

    candidates.sort(key=lambda x: x[0])

    phrases = []
    cooldown = 0.0

    # Reduced gap to allow more phrases (was 25.0)
    target_gap = 15.0

    for cand_t, _ in candidates:
        if cand_t < cooldown:
            continue

        length = random.uniform(4.0, 8.0)
        start_t = cand_t
        end_t = start_t + length

        # Hard Clamp to safety zone
        if end_t > valid_end_zone:
            end_t = valid_end_zone
            if end_t - start_t < 2.0: # Too short after clamping? Skip.
                continue

        phrases.append(StarPowerPhrase(start_t, end_t))
        cooldown = end_t + target_gap

    # Fallback for short/sparse songs: Periodic placement
    if len(phrases) < 2 and duration_sec > 60:
        phrases = []
        cursor = first_note + 15.0
        while cursor < valid_end_zone - 5.0:
            end = min(cursor + 6.0, valid_end_zone)
            phrases.append(StarPowerPhrase(cursor, end))
            cursor += 30.0

    return phrases
