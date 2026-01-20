from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys

import librosa  # type: ignore
import numpy as np  # type: ignore

from gui.utils import repo_root, is_frozen


def get_bin_path(tool_name: str) -> str:
    if is_frozen():
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parents[1]

    bin_dir = base / "bin"
    ext = ".exe" if sys.platform == "win32" else ""
    exe = bin_dir / (tool_name + ext)

    if exe.exists():
        return str(exe)

    return tool_name


FFMPEG_BIN = get_bin_path("ffmpeg")
FFPROBE_BIN = get_bin_path("ffprobe")


@dataclass
class Onset:
    t: float
    strength: float


def check_ffmpeg() -> bool:
    try:
        subprocess.run([FFMPEG_BIN, "-version"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def normalize_and_save(src: Path, dest: Path) -> None:
    cmd = [
        FFMPEG_BIN, "-y",
        # FIX: Quiet mode. Hides the version info and progress bars.
        "-hide_banner", "-loglevel", "error",
        "-i", str(src),
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-codec:a", "libmp3lame", "-qscale:a", "2",
        str(dest)
    ]
    try:
        # We keep stderr visible (don't send to DEVNULL) so 'loglevel error' can still print actual issues.
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        print(f"❌ Error: FFmpeg binary not found at '{FFMPEG_BIN}'.")
        print("   Please run 'make deps' to download it automatically.")
        raise RuntimeError("FFmpeg missing")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: FFmpeg failed to process audio (Code {e.returncode})")
        raise


def detect_onsets(audio_path: Path) -> list[Onset]:
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)

    onsets = librosa.onset.onset_detect(
        y=y, sr=sr, units='time', delta=0.03, wait=1, pre_max=3, post_max=3, post_avg=3
    )

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    times = librosa.times_like(onset_env, sr=sr)

    res = []
    for t in onsets:
        idx = np.searchsorted(times, t)
        if idx < len(onset_env):
            res.append(Onset(t=float(t), strength=float(onset_env[idx])))

    return res


def estimate_pitches(audio_path: Path, times: list[float]) -> list[float]:
    if not times:
        return []
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

    out = []
    t_map = librosa.times_like(pitches, sr=sr)

    for t in times:
        idx = np.searchsorted(t_map, t)
        if idx >= len(t_map):
            idx = len(t_map) - 1

        col = pitches[:, idx]
        mags = magnitudes[:, idx]
        best_idx = mags.argmax()

        p = col[best_idx]
        if p > 0:
            out.append(float(p))
        else:
            out.append(0.0)

    return out
