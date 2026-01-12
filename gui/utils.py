from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel


def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)

def repo_root() -> Path:
    if is_frozen(): return Path(sys._MEIPASS)
    # Assumes this file is in /gui/utils.py, so parents[1] is the repo root
    return Path(__file__).resolve().parents[1]

def get_python_exec() -> str | Path:
    if is_frozen(): return sys.executable
    return repo_root() / ".venv" / "bin" / "python"

def form_label(text: str, required: bool = False, align=Qt.AlignCenter | Qt.AlignVCenter) -> QLabel:
    """
    Creates a standardized label for forms.
    UPDATED: Default alignment is now Center (was Right).
    """
    txt = f"{text} <span style='color:#ff4444;'>*</span>" if required else text
    lbl = QLabel(txt)
    lbl.setAlignment(align)
    lbl.setMinimumWidth(110)
    lbl.setFont(get_font(11))
    return lbl

def get_font(size: int = 11, bold: bool = False) -> QFont:
    f = QApplication.font()
    f.setPointSize(size)
    f.setBold(bold)
    return f

@dataclass
class RunConfig:
    audio: Path
    out_root: Path
    title: str
    artist: str
    album: str
    genre: str
    mode: str
    max_nps: float
    min_gap_ms: int
    seed: int
    # CLEANUP: These are now hardcoded in the build logic
    allow_orange: bool
    rhythmic_glue: bool
    grid_snap: str

    chord_prob: float
    sustain_len: float
    sustain_threshold: float
    sustain_buffer: float

    # New Scaling Params
    hard_gap_ms: int
    med_gap_ms: int
    easy_gap_ms: int

    write_chart: bool = False

    charter: str = "Zullo7569"
    fetch_metadata: bool = True
