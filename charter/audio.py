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

    This is deliberately "over-detecty" — we will filter later with rules
    to match your Medium vibe.
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
