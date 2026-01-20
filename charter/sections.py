from __future__ import annotations
from dataclasses import dataclass
import random


@dataclass
class Section:
    name: str
    start: float


def find_sections(density_profile: list[float], duration: float) -> list[Section]:
    """
    Analyzes note density to create section markers.
    """
    sections = []

    # If no data, return basic Song section
    if not density_profile:
        return [Section("Song", 0.0)]

    step = duration / len(density_profile)

    # Calculate Stats
    avg_density = sum(density_profile) / len(density_profile)
    peak_density = max(density_profile) if density_profile else 0.0

    # Thresholds (Tuned for v2.1.2)
    # 1.35x average is a good baseline for a Chorus
    chorus_threshold = avg_density * 1.35

    current_state = "Intro"
    sections.append(Section("Intro", 0.0))

    # Min duration to prevent "flickering" between sections
    min_sec_len = 12.0
    last_sec_time = 0.0

    for i, dens in enumerate(density_profile):
        t = i * step

        # Lock section for a minimum time
        if t - last_sec_time < min_sec_len:
            continue

        # Force Outro in last 15s
        if t > duration - 15.0:
            new_state = "Outro"

        elif dens > chorus_threshold:
            # High Density Logic
            # Solos are usually late in the song (45%-90%) and VERY dense
            if 0.45 < (t / duration) < 0.90 and dens > (peak_density * 0.70):
                new_state = "Guitar Solo"
            else:
                new_state = "Chorus"

        else:
            # Low/Med Density Logic
            # Default to "Verse" instead of "Bridge" to avoid confusion
            # Only identify "Breakdown" if it's super quiet (but not silent)
            if dens < avg_density * 0.4 and dens > 0.1:
                new_state = "Breakdown"
            else:
                new_state = "Verse"

        # Apply State Change
        if new_state != current_state:
            # Don't switch INTO Intro (only start there)
            if new_state == "Intro":
                continue

            sections.append(Section(new_state, t))
            current_state = new_state
            last_sec_time = t

    return sections

# --- Stats logic (Unchanged) ---


@dataclass(frozen=True)
class SectionStats:
    name: str
    start: float
    end: float
    notes: int
    chords: int
    avg_nps: float
    max_nps_1s: float


def compute_section_stats(
    *,
    note_starts: list[float],
    chord_starts: list[float],
    sections: list[Section],
    duration_sec: float,
) -> list[SectionStats]:
    if not sections:
        sections = [Section("Song", 0.0)]

    bounds = []
    for i, s in enumerate(sections):
        a = s.start
        b = sections[i+1].start if i+1 < len(sections) else duration_sec
        bounds.append((s.name, a, b))

    stats = []
    n_sorted = sorted(note_starts)
    c_sorted = sorted(chord_starts)

    for name, a, b in bounds:
        notes_in = [t for t in n_sorted if a <= t < b]
        chords_in = [t for t in c_sorted if a <= t < b]
        length = max(0.1, b - a)

        max_nps = 0.0
        if notes_in:
            for i in range(len(notes_in)):
                t_end = notes_in[i] + 1.0
                count = sum(1 for t in notes_in[i:] if t < t_end)
                max_nps = max(max_nps, float(count))

        stats.append(SectionStats(
            name=name, start=a, end=b,
            notes=len(notes_in), chords=len(chords_in),
            avg_nps=len(notes_in)/length, max_nps_1s=max_nps
        ))
    return stats
