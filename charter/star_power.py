from __future__ import annotations
from dataclasses import dataclass
from charter.config import SP_PITCH

@dataclass(frozen=True)
class StarPowerPhrase:
    start: float
    end: float

def generate_star_power_phrases(
    *,
    note_times: list[float],
    duration_sec: float,
    every_sec: float = 25.0,   # Slightly less frequent
    phrase_len_sec: float = 6.0, # Shorter (was 9.0)
    start_at: float = 15.0,
) -> list[StarPowerPhrase]:
    """
    Generates Star Power phrases.
    Updated v0.4: Shorter phrases (6s) that feel more like 'rewards'
    than 'chores'.
    """
    if not note_times:
        return []

    note_times = sorted(note_times)
    phrases: list[StarPowerPhrase] = []
    t = float(start_at)

    idx = 0
    while t < duration_sec - 10.0:
        # Snap to nearest note
        while idx < len(note_times) and note_times[idx] < t:
            idx += 1
        if idx >= len(note_times):
            break

        start = note_times[idx]
        # Shorter max length, minimum 2 seconds
        end = min(start + phrase_len_sec, duration_sec - 1.0)

        if end - start >= 2.0:
            phrases.append(StarPowerPhrase(start=float(start), end=float(end)))

        t = end + every_sec

    return phrases
