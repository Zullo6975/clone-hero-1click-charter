from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import librosa  # type: ignore
import numpy as np  # type: ignore


@dataclass(frozen=True)
class OnsetCandidate:
    t: float          # seconds
    strength: float   # relative strength


def detect_onsets(audio_path: Path, *, hop_length: int = 512) -> list[OnsetCandidate]:
    """
    Detect onset candidates with relative strength using librosa.
    """
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)

    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    frames = librosa.onset.onset_detect(
        onset_envelope=oenv,
        sr=sr,
        hop_length=hop_length,
        units="frames",
        backtrack=False,
    )

    times = librosa.frames_to_time(frames, sr=sr, hop_length=hop_length)

    strengths = []
    for f in frames:
        strengths.append(float(oenv[f]) if 0 <= f < len(oenv) else 0.0)

    return [OnsetCandidate(t=float(t), strength=s) for t, s in zip(times, strengths)]


def estimate_pitches(audio_path: Path, times: list[float]) -> list[float | None]:
    """
    Estimates the fundamental frequency (pitch) at specific timestamps.
    Returns a list of frequencies (Hz) or None if unpitched (silence/noise).
    """
    if not times:
        return []

    y, sr = librosa.load(str(audio_path), sr=None, mono=True)

    # fmin/fmax range covers typical guitar/bass frequencies (approx C1 to C7)
    # We increase frame_length to 4096 to safely detect C1 (32.7Hz) without warnings.
    f0, _, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz('C1'),
        fmax=librosa.note_to_hz('C7'),
        sr=sr,
        frame_length=4096
    )

    # Map our target times to the f0 frames
    # pyin uses hop_length = frame_length // 4 by default = 1024
    frame_indices = librosa.time_to_frames(times, sr=sr, hop_length=1024)

    pitches = []
    for idx in frame_indices:
        if 0 <= idx < len(f0):
            val = f0[idx]
            if np.isnan(val):
                pitches.append(None)
            else:
                pitches.append(float(val))
        else:
            pitches.append(None)

    return pitches
