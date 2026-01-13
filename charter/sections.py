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
    Replaces the old random 'generate_sections' logic.
    """

    sections = []

    # Standard Structure Heuristic
    # 1. Intro (0 - ~30s or low density)
    # 2. Verse / Chorus (Cyclic peaks)
    # 3. Solo (Sustained high density usually past middle)
    # 4. Outro (Last ~30s)

    if not density_profile:
        # Fallback if no density data
        return [Section("Song", 0.0)]

    step = duration / len(density_profile)

    # Thresholds
    # We calculate the average density
    avg_density = sum(density_profile) / len(density_profile)
    peak_density = max(density_profile)

    # Threshold for "Intense" (Chorus/Solo)
    high_threshold = avg_density * 1.5

    current_state = "Intro"
    sections.append(Section("Intro", 0.0))

    # We want to avoid spamming sections, so we enforce a minimum duration
    min_sec_len = 15.0 # seconds
    last_sec_time = 0.0

    # Naive state machine
    for i, dens in enumerate(density_profile):
        t = i * step

        if t - last_sec_time < min_sec_len:
            continue

        # Determine likely state
        if t > duration - 20:
            new_state = "Outro"
        elif dens > high_threshold:
            # Is it a solo?
            # Solos usually happen 60-80% into the song and are VERY dense
            # v2.1.2: Widened window to 40%-90% and lowered peak req to 65% to catch more solos
            if 0.40 < (t / duration) < 0.90 and dens > (peak_density * 0.65):
                new_state = "Guitar Solo"
            else:
                new_state = "Chorus"
        elif dens < avg_density * 0.8:
            new_state = "Verse"
        else:
            new_state = "Bridge"

        if new_state != current_state:
            sections.append(Section(new_state, t))
            current_state = new_state
            last_sec_time = t

    return sections

# --- Stats logic ---
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
