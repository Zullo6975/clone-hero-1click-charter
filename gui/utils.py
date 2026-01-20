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
    if is_frozen():
        return Path(sys._MEIPASS)
    # Assumes this file is in /gui/utils.py, so parents[1] is the repo root
    return Path(__file__).resolve().parents[1]


def get_python_exec() -> str | Path:
    """
    Returns the path to the Python executable.
    Handles Frozen (PyInstaller), Windows (.venv/Scripts), and Unix (.venv/bin).
    """
    if is_frozen():
        return sys.executable

    root = repo_root()

    # 1. Check for Windows Virtual Environment
    win_python = root / ".venv" / "Scripts" / "python.exe"
    if win_python.exists():
        return win_python

    # 2. Check for Unix/Mac Virtual Environment
    unix_python = root / ".venv" / "bin" / "python"
    if unix_python.exists():
        return unix_python

    # 3. Fallback to system python
    return sys.executable


def get_base_font_size() -> int:
    """Returns the native standard font size for the current OS."""
    if sys.platform == "win32":
        return 9  # Windows standard is smaller
    elif sys.platform == "darwin":
        return 11  # macOS standard is larger
    return 10     # Linux


def get_font(size: int | None = None, bold: bool = False) -> QFont:
    """
    Returns a QFont. If size is None, uses the OS default base size.
    """
    f = QApplication.font()

    # If no specific size requested, use the OS native default
    final_size = size if size is not None else get_base_font_size()

    f.setPointSize(final_size)
    f.setBold(bold)
    return f


def form_label(text: str, required: bool = False, align=Qt.AlignCenter | Qt.AlignVCenter) -> QLabel:
    """
    Creates a standardized label for forms.
    """
    txt = f"{text} <span style='color:#ff4444;'>*</span>" if required else text
    lbl = QLabel(txt)
    lbl.setAlignment(align)
    # Adjusted: Use slightly larger than base for form labels, but not huge
    lbl.setFont(get_font(size=get_base_font_size() + 1))
    lbl.setMinimumWidth(110)
    return lbl


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
