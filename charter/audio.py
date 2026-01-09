from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

import librosa  # type: ignore
import numpy as np  # type: ignore
from pydub import AudioSegment # type: ignore


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
    Estimates pitch only in the guitar frequency range (E2 to C6).
    """
    if not times:
        return []

    y, sr = librosa.load(str(audio_path), sr=None, mono=True)

    f0, _, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz('E2'), # was C1
        fmax=librosa.note_to_hz('C6'), # was C7
        sr=sr,
        frame_length=4096
    )

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

def normalize_and_save(src: Path, dst: Path, target_dbfs: float = -14.0) -> None:
    """
    Normalizes audio to a target average loudness (dBFS) and saves as MP3.
    Includes a peak limiter to prevent clipping.
    """
    try:
        # Load audio (pydub auto-detects format)
        audio = AudioSegment.from_file(str(src))
        
        # Calculate gain needed to hit target average
        change_needed = target_dbfs - audio.dBFS
        normalized = audio.apply_gain(change_needed)
        
        # Safety Check: If peak is > -0.5 dB, limit it down
        # (This prevents clipping on loud tracks)
        if normalized.max_dBFS > -0.5:
            safety_reduction = -0.5 - normalized.max_dBFS
            normalized = normalized.apply_gain(safety_reduction)

        # Export as standard 192k MP3 for Clone Hero
        normalized.export(str(dst), format="mp3", bitrate="192k")
        print(f"DEBUG: Normalized audio. Avg: {audio.dBFS:.1f} -> {normalized.dBFS:.1f} dBFS")
        
    except Exception as e:
        print(f"WARNING: Audio normalization failed ({e}). Using raw copy.")
        # Fallback to simple copy if user doesn't have ffmpeg installed
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)