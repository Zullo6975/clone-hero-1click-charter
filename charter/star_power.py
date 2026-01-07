from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# Commonly used “star power / overdrive phrase” pitch in FoF/GH-style MIDIs.
# If CH doesn’t recognize it on your setup, we’ll swap this constant once.
SP_PITCH = 116


@dataclass(frozen=True)
class StarPowerPhrase:
    start: float
    end: float


def generate_star_power_phrases(
    *,
    note_times: list[float],
    duration_sec: float,
    every_sec: float = 22.0,
    phrase_len_sec: float = 9.0,
    start_at: float = 12.0,
) -> list[StarPowerPhrase]:
    """
    GH-ish feel:
    - phrases spaced ~every 22s
    - phrases last ~9s
    - aligned to nearby note times so it feels “real”
    """
    if not note_times:
        return []

    note_times = sorted(note_times)
    every_sec = max(14.0, float(every_sec))
    phrase_len_sec = max(6.0, min(14.0, float(phrase_len_sec)))

    phrases: list[StarPowerPhrase] = []
    t = float(start_at)

    idx = 0
    while t < duration_sec - 8.0:
        # snap to nearest note time >= t
        while idx < len(note_times) and note_times[idx] < t:
            idx += 1
        if idx >= len(note_times):
            break

        start = note_times[idx]
        end = min(start + phrase_len_sec, duration_sec - 0.5)

        # ensure phrase spans at least a bit
        if end - start >= 3.0:
            phrases.append(StarPowerPhrase(start=float(start), end=float(end)))

        t += every_sec

    # de-dupe overlaps
    cleaned: list[StarPowerPhrase] = []
    last_end = -1.0
    for p in phrases:
        if p.start < last_end - 0.25:
            continue
        cleaned.append(p)
        last_end = p.end

    return cleaned
