from __future__ import annotations
from dataclasses import dataclass
import random

@dataclass
class Section:
    name: str
    start: float

def generate_sections(audio_path: str, duration: float) -> list[Section]:
    """
    Generates a list of sections based on song duration.
    """
    # Standard structure templates based on duration
    # Short (< 2 min): Intro -> Verse -> Chorus -> Outro
    # Medium (2-4 min): Intro -> Verse 1 -> Chorus 1 -> Verse 2 -> Chorus 2 -> Bridge -> Outro
    # Long (> 4 min): Expanded structure

    sections = []
    cursor = 0.0

    # Always start with Intro
    sections.append(Section("Intro", 0.0))
    cursor += random.uniform(8.0, 15.0) # Short intro

    # Loop to fill duration
    verse_count = 1
    chorus_count = 1

    while cursor < duration - 20.0: # Leave room for Outro
        # Add Verse
        sections.append(Section(f"Verse {verse_count}", cursor))
        cursor += random.uniform(30.0, 45.0)
        verse_count += 1

        if cursor >= duration - 20.0: break

        # Add Chorus
        sections.append(Section(f"Chorus {chorus_count}", cursor))
        cursor += random.uniform(25.0, 40.0)
        chorus_count += 1

        if cursor >= duration - 20.0: break

        # Occasionally add a Bridge or Solo after 2nd Chorus
        if chorus_count == 3 and cursor < duration - 45.0:
            if random.random() > 0.5:
                sections.append(Section("Bridge", cursor))
            else:
                sections.append(Section("Solo", cursor))
            cursor += random.uniform(20.0, 30.0)

    # Final Section: Outro
    # Ensure it doesn't start *after* the song ends
    if cursor < duration:
        sections.append(Section("Outro", cursor))

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
