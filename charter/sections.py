from __future__ import annotations
from dataclasses import dataclass
import librosa # type: ignore
import numpy as np # type: ignore

@dataclass(frozen=True)
class Section:
    name: str
    start: float

# UPDATED: Removed "Solo" so it is only used when detected dynamically
SECTION_LABELS = ["Verse", "Chorus", "Verse", "Chorus", "Bridge", "Breakdown", "Chorus", "Outro"]

def generate_sections(
    audio_path: str,
    duration_sec: float,
) -> list[Section]:
    """
    Finds musical boundaries using audio analysis.
    INCLUDES SAFETY VALVE: Force-splits any section > 45s to ensure pacing.
    """
    try:
        # 1. Fast structural segmentation
        y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=duration_sec)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        # Ask for slightly more segments (k=12) to catch smaller changes
        bounds = librosa.segment.agglomerative(chroma, k=12)
        times = librosa.frames_to_time(bounds, sr=sr)
        times = sorted(list(times))
    except Exception:
        # Fallback if analysis crashes
        times = [0.0]

    # 2. Merge "Analysis" times with "Safety" times
    filled_times = [0.0]
    analysis_times = [t for t in times if t > 0.1]
    analysis_times.append(duration_sec)

    curr = 0.0
    for t in analysis_times:
        # While the gap to the next analysis point is too big...
        while t - curr > 45.0:
            # Inject a split at +40s
            curr += 40.0
            if curr < duration_sec - 10.0:
                filled_times.append(curr)

        # Add the actual analysis point if it's not too close to the last one
        if t < duration_sec - 5.0 and (t - filled_times[-1] > 10.0):
            filled_times.append(t)
            curr = t

    # 3. Labeling
    sections: list[Section] = []

    if not filled_times or filled_times[0] != 0.0:
        filled_times.insert(0, 0.0)

    sections.append(Section("Intro", 0.0))

    label_idx = 0
    for t in filled_times[1:]:
        name = SECTION_LABELS[label_idx % len(SECTION_LABELS)]
        sections.append(Section(name, float(t)))
        label_idx += 1

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