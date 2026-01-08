from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Section:
    name: str
    start: float  # seconds


SECTION_CYCLE = ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Chorus", "Outro"]


def generate_sections(
    *,
    duration_sec: float,
    approx_section_len_sec: float = 25.0,
    start_at: float = 1.0,
) -> list[Section]:
    """
    Simple, robust sections:
    - Every ~25s create a new section, cycling labels.
    - Guaranteed to cover whole song.
    """
    if duration_sec <= start_at + 5:
        return [Section("Song", start_at)]

    approx_section_len_sec = max(12.0, float(approx_section_len_sec))

    sections: list[Section] = []
    t = float(start_at)
    idx = 0
    while t < duration_sec - 2.0:
        name = SECTION_CYCLE[idx % len(SECTION_CYCLE)]
        sections.append(Section(name=name, start=t))
        t += approx_section_len_sec
        idx += 1

    # Ensure first is Intro-ish
    if sections and sections[0].start > start_at + 0.5:
        sections.insert(0, Section("Intro", start_at))

    # De-dupe any same-time
    out: list[Section] = []
    last_t = None
    for s in sections:
        if last_t is None or abs(s.start - last_t) > 1e-6:
            out.append(s)
            last_t = s.start

    return out


@dataclass(frozen=True)
class SectionStats:
    name: str
    start: float
    end: float
    notes: int
    chords: int
    avg_nps: float
    max_nps_1s: float


def _max_nps_rolling_1s(times: list[float]) -> float:
    if not times:
        return 0.0
    times = sorted(times)
    j = 0
    best = 0
    for i in range(len(times)):
        while times[i] - times[j] > 1.0:
            j += 1
        best = max(best, i - j + 1)
    return float(best)


def compute_section_stats(
    *,
    note_starts: list[float],
    chord_starts: list[float],
    sections: list[Section],
    duration_sec: float,
) -> list[SectionStats]:
    """
    Stats used by *our tool*, exported to stats.json.
    Clone Hero won’t show these on its results screen,
    but it’s great for tuning/debugging.
    """
    if not sections:
        sections = [Section("Song", 1.0)]

    # create boundaries
    bounds: list[tuple[str, float, float]] = []
    for i, s in enumerate(sections):
        a = float(s.start)
        b = float(sections[i + 1].start) if i + 1 < len(sections) else float(duration_sec)
        if b <= a:
            continue
        bounds.append((s.name, a, b))

    stats: list[SectionStats] = []
    note_starts_sorted = sorted(note_starts)
    chord_starts_sorted = sorted(chord_starts)

    for name, a, b in bounds:
        notes_in = [t for t in note_starts_sorted if a <= t < b]
        chords_in = [t for t in chord_starts_sorted if a <= t < b]
        length = max(0.001, b - a)
        stats.append(
            SectionStats(
                name=name,
                start=a,
                end=b,
                notes=len(notes_in),
                chords=len(chords_in),
                avg_nps=len(notes_in) / length,
                max_nps_1s=_max_nps_rolling_1s(notes_in),
            )
        )

    return stats
