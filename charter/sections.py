from __future__ import annotations
from dataclasses import dataclass
import librosa # type: ignore
import numpy as np # type: ignore

@dataclass(frozen=True)
class Section:
    name: str
    start: float

SECTION_LABELS = ["Verse", "Chorus", "Verse", "Chorus", "Bridge", "Solo", "Chorus", "Outro"]

def generate_sections(
    audio_path: str,
    duration_sec: float,
) -> list[Section]:
    """
    Attempts to find musical changes using librosa's segmentation.
    If that fails or is too slow, falls back to time-based cycling.
    """
    try:
        # 1. Fast structural segmentation
        y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=duration_sec)
        # Compute bounds based on recurrence (simplified for speed)
        # We look for major spectral changes (novelty)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        bounds = librosa.segment.agglomerative(chroma, k=8) # Aim for ~8 sections
        times = librosa.frames_to_time(bounds, sr=sr)
        times = sorted(list(times))
    except Exception:
        # Fallback if audio analysis fails
        times = [0.0]
        curr = 0.0
        while curr < duration_sec - 15.0:
            curr += 28.0 # Fallback: Every 28s
            times.append(curr)

    # Filter and Label
    sections: list[Section] = []
    times = [t for t in times if t >= 0.5 and t < duration_sec - 5.0]

    # Always start with Intro
    sections.append(Section("Intro", 0.0))

    label_idx = 0
    for t in times:
        if t < 5.0: continue # Skip if too close to intro
        if sections and (t - sections[-1].start < 10.0): continue # Skip short sections

        name = SECTION_LABELS[label_idx % len(SECTION_LABELS)]
        sections.append(Section(name, float(t)))
        label_idx += 1

    return sections

# Stats logic remains the same, just imports changed
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

        # Recalculate max_nps for this section
        # (Simplified rolling window for stats)
        max_nps = 0.0
        if notes_in:
            # Quick & dirty NPS check
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
