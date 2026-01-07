from __future__ import annotations
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QSize
from PySide6.QtGui import QFont, QPixmap, QAction, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QButtonGroup,
    QComboBox,
    QRadioButton,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

# ---------------- Paths ----------------
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

def venv_python() -> Path:
    return repo_root() / ".venv" / "bin" / "python"


# ---------------- Difficulty presets ----------------
# We’re mapping "feel" to ONLY the CLI args you already have.
# - max_nps: higher = denser
# - min_gap_ms: lower = tighter spacing
DIFFICULTY_PRESETS: dict[str, dict[str, float | int] | None] = {
    "Medium (Casual)":   {"max_nps": 2.25, "min_gap_ms": 170},
    "Medium (Balanced)": {"max_nps": 2.80, "min_gap_ms": 140},
    "Medium (Intense)":  {"max_nps": 3.35, "min_gap_ms": 115},
    "Medium (Chaotic)":  {"max_nps": 3.90, "min_gap_ms": 95},
    "Custom…":           None,
}


# ---------------- Themes ----------------
LIGHT_QSS = """
QMainWindow { background: #f3f6fb; }
QWidget { color: #0f172a; font-size: 14px; }

/* Clean Scrollbars */
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 0px; }
QScrollBar::handle:vertical { background: rgba(15,23,42,0.15); min-height: 30px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: rgba(15,23,42,0.3); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

/* Panels */
QFrame#Sidebar, QFrame#MainPanel {
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(15,23,42,0.10);
  border-radius: 16px;
}

/* Group containers */
QGroupBox {
  border: 1px solid rgba(15,23,42,0.10);
  border-radius: 14px;
  margin-top: 10px;
  padding: 12px;
  background: rgba(255,255,255,0.55);
}
QGroupBox::title {
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 0 8px;
  color: rgba(15,23,42,0.88);
  font-weight: 800;
}
QLabel#Muted { color: rgba(15,23,42,0.60); }

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QComboBox {
  background: rgba(255,255,255,0.85);
  border: 1px solid rgba(15,23,42,0.14);
  border-radius: 10px;
  padding: 8px 12px;
  selection-background-color: rgba(59,130,246,0.20);
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QComboBox:focus {
  border: 1px solid rgba(59,130,246,0.65);
  background: rgba(255,255,255,0.92);
}

/* Spinbox Arrows */
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid rgba(15,23,42,0.1);
    border-bottom: 1px solid rgba(15,23,42,0.1);
    background: rgba(240,242,245,1.0);
    border-top-right-radius: 10px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 24px;
    border-left: 1px solid rgba(15,23,42,0.1);
    background: rgba(240,242,245,1.0);
    border-bottom-right-radius: 10px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: rgba(59,130,246,0.1);
}

/* Radio Buttons - Clean Blue Dot Style */
QRadioButton { spacing: 8px; font-weight: 500; }
QRadioButton::indicator {
    width: 16px; height: 16px;
    border-radius: 9px;
    border: 1px solid #9ca3af;
    background: white;
}
QRadioButton::indicator:checked {
    border: 1px solid #3b82f6;
    background: qradialgradient(
        cx: 0.5, cy: 0.5, radius: 0.4,
        fx: 0.5, fy: 0.5,
        stop: 0.0 #3b82f6,
        stop: 1.0 #3b82f6
    );
}
QRadioButton::indicator:hover { border-color: #3b82f6; }

/* Buttons */
QPushButton, QToolButton {
  background: rgba(15,23,42,0.04);
  border: 1px solid rgba(15,23,42,0.14);
  border-radius: 10px;
  padding: 10px 16px;
  font-weight: 700;
}
QPushButton:hover, QToolButton:hover { background: rgba(15,23,42,0.06); border-color: rgba(15,23,42,0.18); }
QPushButton:pressed, QToolButton:pressed { background: rgba(15,23,42,0.03); }

/* Primary Action */
QPushButton#Primary {
  color: white;
  background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 rgba(59,130,246,0.98), stop:1 rgba(99,102,241,0.98));
  border: 1px solid rgba(15,23,42,0.10);
}
QPushButton#Primary:hover {
  background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 rgba(37,99,235,0.98), stop:1 rgba(79,70,229,0.98));
}

/* Toggle Buttons (Advanced/Logs) */
QPushButton#Toggle {
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    color: rgba(15,23,42,0.7);
}
QPushButton#Toggle:checked {
    background: rgba(15,23,42,0.05);
    border: 1px solid rgba(15,23,42,0.1);
    color: rgba(15,23,42,1.0);
}
QPushButton#Toggle:hover { background: rgba(15,23,42,0.03); color: rgba(15,23,42,0.9); }

/* Art preview */
QLabel#ArtFrame {
  background: rgba(255,255,255,0.55);
  border: 1px dashed rgba(15,23,42,0.22);
  border-radius: 14px;
  color: rgba(15,23,42,0.55);
}

/* Logs */
QTextEdit#Log {
  background: #0b0f17;
  border: 1px solid rgba(15,23,42,0.14);
  border-radius: 14px;
  padding: 12px;
  color: rgba(232,238,248,0.92);
}
QFrame#Divider { background: rgba(15,23,42,0.10); }
"""

DARK_QSS = """
QMainWindow { background: #0b0f17; }
QWidget { color: #e8eef8; font-size: 14px; }

/* Scrollbars */
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 0px; }
QScrollBar::handle:vertical { background: rgba(255,255,255,0.15); min-height: 30px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.3); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QFrame#Sidebar, QFrame#MainPanel {
  background: rgba(15,22,35,0.78);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
}
QGroupBox {
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 14px;
  margin-top: 10px;
  padding: 12px;
  background: rgba(255,255,255,0.03);
}
QGroupBox::title {
  subcontrol-origin: margin;
  subcontrol-position: top left;
  padding: 0 8px;
  color: rgba(232,238,248,0.90);
  font-weight: 800;
}
QLabel#Muted { color: rgba(232,238,248,0.65); }

QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QComboBox {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 10px;
  padding: 8px 12px;
  selection-background-color: rgba(80, 140, 255, 0.35);
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QComboBox:focus {
  border: 1px solid rgba(90,160,255,0.75);
  background: rgba(255,255,255,0.07);
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid rgba(255,255,255,0.1);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    background: rgba(255,255,255,0.05);
    border-top-right-radius: 10px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 24px;
    border-left: 1px solid rgba(255,255,255,0.1);
    background: rgba(255,255,255,0.05);
    border-bottom-right-radius: 10px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: rgba(255,255,255,0.15);
}

QRadioButton { spacing: 8px; font-weight: 500; }
QRadioButton::indicator {
    width: 16px; height: 16px;
    border-radius: 9px;
    border: 1px solid rgba(255,255,255,0.4);
    background: transparent;
}
QRadioButton::indicator:checked {
    border: 1px solid #3b82f6;
    background: qradialgradient(
        cx: 0.5, cy: 0.5, radius: 0.55,
        fx: 0.5, fy: 0.5,
        stop: 0.0 #3b82f6,
        stop: 0.45 #3b82f6,
        stop: 0.46 white,
        stop: 1.0 white
    );
}

QPushButton, QToolButton {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 10px;
  padding: 10px 16px;
  font-weight: 700;
}
QPushButton:hover, QToolButton:hover { background: rgba(255,255,255,0.10); border-color: rgba(255,255,255,0.18); }
QPushButton:pressed, QToolButton:pressed { background: rgba(255,255,255,0.05); }

QPushButton#Primary {
  background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 rgba(72,118,255,0.95), stop:1 rgba(122,72,255,0.95));
  border: 1px solid rgba(255,255,255,0.18);
}
QPushButton#Primary:hover {
  background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 rgba(86,132,255,0.98), stop:1 rgba(138,88,255,0.98));
}

QPushButton#Toggle {
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    color: rgba(255,255,255,0.6);
}
QPushButton#Toggle:checked {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.95);
}
QPushButton#Toggle:hover { background: rgba(255,255,255,0.03); color: rgba(255,255,255,0.8); }

QLabel#ArtFrame {
  background: rgba(255,255,255,0.03);
  border: 1px dashed rgba(255,255,255,0.18);
  border-radius: 14px;
  color: rgba(232,238,248,0.55);
}

QTextEdit#Log {
  background: #0b0f17;
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 14px;
  padding: 12px;
  color: rgba(232,238,248,0.92);
}
QFrame#Divider { background: rgba(255,255,255,0.08); }
"""


# ---------------- Helpers ----------------
def human_ok(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")

def arrow_text(expanded: bool) -> str:
    return "▼" if expanded else "▶"

def form_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setMinimumWidth(110)
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return lbl


# ---------------- Config ----------------
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
    charter: str = "Zullo7569"
    fetch_metadata: bool = True


# ---------------- Main Window ----------------
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CH 1-Click Charter")
        self.setMinimumSize(950, 720)

        self.audio_path: Path | None = None
        self.cover_path: Path | None = None
        self.last_out_song: Path | None = None
        self.proc: QProcess | None = None

        self.dark_mode = False
        self._title_user_edited = False

        self._build_ui()
        self._wire()
        self.apply_theme(dark=self.dark_mode)

        # Apply default preset once the widgets exist
        self.apply_preset(self.preset_combo.currentText())

        self._update_state()
        self.statusBar().showMessage("Ready")

    # ---------- UI ----------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(14)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        outer.addWidget(splitter)

        # ---- Sidebar ----
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.NoFrame)
        sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        s = QVBoxLayout(sidebar)
        s.setContentsMargins(16, 16, 16, 16)
        s.setSpacing(12)

        title = QLabel("CH 1-Click Charter")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setWeight(QFont.DemiBold)
        title.setFont(title_font)

        subtitle = QLabel("A fast, portable chart generator UI powered by your CLI.")
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)

        s.addWidget(title)
        s.addWidget(subtitle)

        # Theme toggle
        theme_row = QHBoxLayout()
        self.chk_dark = QCheckBox("Dark mode")
        self.chk_dark.setChecked(False)
        theme_row.addWidget(self.chk_dark)
        theme_row.addStretch(1)
        s.addLayout(theme_row)

        # Audio group
        audio_box = QGroupBox("Audio")
        audio_layout = QVBoxLayout(audio_box)
        audio_layout.setSpacing(10)

        self.audio_label = QLabel("No file selected")
        self.audio_label.setObjectName("Muted")
        self.audio_label.setWordWrap(True)

        audio_btn_row = QHBoxLayout()
        self.btn_pick_audio = QPushButton("Browse Audio…")
        self.btn_clear_audio = QToolButton()
        self.btn_clear_audio.setText("Clear")
        self.btn_clear_audio.setToolButtonStyle(Qt.ToolButtonTextOnly)
        audio_btn_row.addWidget(self.btn_pick_audio, 1)
        audio_btn_row.addWidget(self.btn_clear_audio)

        audio_layout.addWidget(self.audio_label)
        audio_layout.addLayout(audio_btn_row)
        s.addWidget(audio_box)

        # Album art
        art_box = QGroupBox("Album Art")
        art_layout = QVBoxLayout(art_box)
        art_layout.setSpacing(12)

        self.cover_label = QLabel("No art selected")
        self.cover_label.setObjectName("Muted")
        self.cover_label.setWordWrap(True)

        self.cover_preview = QLabel("Preview")
        self.cover_preview.setObjectName("ArtFrame")
        self.cover_preview.setAlignment(Qt.AlignCenter)
        self.cover_preview.setMinimumHeight(160)
        self.cover_preview.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        cover_btn_row = QHBoxLayout()
        self.btn_pick_cover = QPushButton("Choose Image…")
        self.btn_clear_cover = QToolButton()
        self.btn_clear_cover.setText("Clear")
        self.btn_clear_cover.setToolButtonStyle(Qt.ToolButtonTextOnly)
        cover_btn_row.addWidget(self.btn_pick_cover, 1)
        cover_btn_row.addWidget(self.btn_clear_cover)

        art_layout.addWidget(self.cover_label)
        art_layout.addWidget(self.cover_preview)
        art_layout.addLayout(cover_btn_row)
        s.addWidget(art_box)

        # Convenience
        util_box = QGroupBox("Convenience")
        util_layout = QVBoxLayout(util_box)
        util_layout.setSpacing(10)
        self.btn_open_output = QPushButton("Open Output Folder")
        self.btn_open_song = QPushButton("Open Last Song Folder")
        util_layout.addWidget(self.btn_open_output)
        util_layout.addWidget(self.btn_open_song)
        s.addWidget(util_box)

        s.addStretch(1)
        sidebar_scroll.setWidget(sidebar)

        # ---- Main panel ----
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QFrame.NoFrame)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        main = QFrame()
        main.setObjectName("MainPanel")

        m = QVBoxLayout(main)
        m.setContentsMargins(24, 24, 24, 24)
        m.setSpacing(16)

        # Styling
        input_font = QFont()
        input_font.setPointSize(14)

        def beefy_line(edit: QLineEdit) -> QLineEdit:
            edit.setFont(input_font)
            edit.setMinimumHeight(42)
            edit.setClearButtonEnabled(True)
            return edit

        def beefy_combo(combo: QComboBox) -> QComboBox:
            combo.setFont(input_font)
            combo.setMinimumHeight(42)
            return combo

        # Metadata
        meta = QGroupBox("Metadata")
        meta_form = QFormLayout(meta)
        meta_form.setHorizontalSpacing(18)
        meta_form.setVerticalSpacing(14)
        meta_form.setContentsMargins(14, 16, 14, 14)
        meta_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.title_edit = beefy_line(QLineEdit())
        self.artist_edit = beefy_line(QLineEdit())
        self.album_edit = beefy_line(QLineEdit())
        self.genre_edit = beefy_line(QLineEdit("Rock"))

        meta_form.addRow(form_label("Title"), self.title_edit)
        meta_form.addRow(form_label("Artist"), self.artist_edit)
        meta_form.addRow(form_label("Album"), self.album_edit)
        meta_form.addRow(form_label("Genre"), self.genre_edit)
        m.addWidget(meta)

        # Output
        out = QGroupBox("Output")
        out_row = QHBoxLayout(out)
        out_row.setContentsMargins(14, 16, 14, 14)
        out_row.setSpacing(12)

        self.out_dir_edit = beefy_line(QLineEdit("output"))
        self.btn_pick_output = QPushButton("Browse…")

        out_row.addWidget(form_label("Folder"), 0)
        out_row.addWidget(self.out_dir_edit, 1)
        out_row.addWidget(self.btn_pick_output, 0)
        m.addWidget(out)

        # Collapsible: Advanced
        self.adv_header = QPushButton(f"{arrow_text(False)}  Advanced Settings")
        self.adv_header.setObjectName("Toggle")
        self.adv_header.setCheckable(True)
        self.adv_header.setChecked(False)
        self.adv_header.setCursor(Qt.PointingHandCursor)

        self.adv_group = QGroupBox("")
        self.adv_group.setTitle("")
        self.adv_group.setFlat(True)
        self.adv_group.setVisible(False)

        adv_group_layout = QVBoxLayout(self.adv_group)
        adv_group_layout.setContentsMargins(0, 0, 0, 0)

        adv_body = QWidget()
        adv_group_layout.addWidget(adv_body)

        adv_form = QFormLayout(adv_body)
        adv_form.setContentsMargins(14, 12, 14, 8)
        adv_form.setHorizontalSpacing(18)
        adv_form.setVerticalSpacing(12)
        adv_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Preset picker (human-friendly)
        self.preset_combo = beefy_combo(QComboBox())
        self.preset_combo.addItems(list(DIFFICULTY_PRESETS.keys()))
        self.preset_combo.setCurrentText("Medium (Balanced)")

        self.preset_hint = QLabel(
            "Choose a feel. Balanced is your ‘default good’. Custom… unlocks the knobs."
        )
        self.preset_hint.setObjectName("Muted")
        self.preset_hint.setWordWrap(True)

        adv_form.addRow(form_label("Difficulty"), self.preset_combo)
        adv_form.addRow(QLabel(""), self.preset_hint)

        # Custom-only container (raw knobs)
        self.custom_row_container = QWidget()
        custom_form = QFormLayout(self.custom_row_container)
        custom_form.setContentsMargins(0, 6, 0, 0)
        custom_form.setHorizontalSpacing(18)
        custom_form.setVerticalSpacing(12)
        custom_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # MODE radios
        self.mode_group = QButtonGroup(self)
        self.mode_real = QRadioButton("Real")
        self.mode_dummy = QRadioButton("Dummy")
        self.mode_group.addButton(self.mode_real)
        self.mode_group.addButton(self.mode_dummy)
        self.mode_real.setChecked(True)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.mode_real)
        mode_layout.addWidget(self.mode_dummy)
        mode_layout.addStretch(1)

        def beefy_spin(spin: QSpinBox | QDoubleSpinBox) -> QWidget:
            spin.setFont(input_font)
            spin.setMinimumHeight(42)
            return spin

        self.max_nps_spin = beefy_spin(QDoubleSpinBox())
        self.max_nps_spin.setRange(1.5, 6.0)
        self.max_nps_spin.setSingleStep(0.05)
        self.max_nps_spin.setValue(2.8)
        self.max_nps_spin.setDecimals(2)
        self.max_nps_spin.setSuffix(" nps")
        self.max_nps_spin.setToolTip("Higher = more notes per second (denser chart).")

        self.min_gap_spin = beefy_spin(QSpinBox())
        self.min_gap_spin.setRange(40, 400)
        self.min_gap_spin.setSingleStep(5)
        self.min_gap_spin.setValue(140)
        self.min_gap_spin.setSuffix(" ms")
        self.min_gap_spin.setToolTip("Lower = notes can be closer together (tighter).")

        self.seed_spin = beefy_spin(QSpinBox())
        self.seed_spin.setRange(0, 2_000_000_000)
        self.seed_spin.setValue(42)
        self.seed_spin.setToolTip("Changes the pattern/variation while keeping the same difficulty.")

        # Human labels
        custom_form.addRow(form_label("Mode"), mode_layout)
        custom_form.addRow(form_label("Note density"), self.max_nps_spin)
        custom_form.addRow(form_label("Note spacing"), self.min_gap_spin)
        custom_form.addRow(form_label("Variation"), self.seed_spin)

        self.custom_row_container.setVisible(False)
        adv_group_layout.addWidget(self.custom_row_container)

        m.addWidget(self.adv_header)
        m.addWidget(self.adv_group)

        # Run row
        run_row = QHBoxLayout()
        run_row.setSpacing(12)
        self.btn_generate = QPushButton("Generate Chart")
        self.btn_generate.setObjectName("Primary")
        self.btn_generate.setMinimumHeight(52)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setMinimumHeight(52)

        run_row.addWidget(self.btn_generate, 1)
        run_row.addWidget(self.btn_cancel, 0)
        m.addLayout(run_row)

        # Divider
        div = QFrame()
        div.setObjectName("Divider")
        div.setFixedHeight(1)
        m.addWidget(div)

        # Logs (Collapsible)
        self.log_header = QPushButton(f"{arrow_text(False)}  Logs")
        self.log_header.setObjectName("Toggle")
        self.log_header.setCheckable(True)
        self.log_header.setChecked(False)
        self.log_header.setCursor(Qt.PointingHandCursor)

        self.log = QTextEdit()
        self.log.setObjectName("Log")
        self.log.setReadOnly(True)
        self.log.setVisible(False)
        self.log.setMinimumHeight(260)
        self.log.setPlaceholderText("CLI output, errors, stats, etc.")

        m.addWidget(self.log_header)
        m.addWidget(self.log)

        m.addStretch(1)
        main_scroll.setWidget(main)

        splitter.addWidget(sidebar_scroll)
        splitter.addWidget(main_scroll)
        splitter.setSizes([320, 780])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Menu
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)

        act_clear = QAction("Clear Log", self)
        act_clear.triggered.connect(lambda: self.log.clear())

        menu = self.menuBar().addMenu("App")
        menu.addAction(act_clear)
        menu.addSeparator()
        menu.addAction(act_quit)

    # ---------- Wiring ----------
    def _wire(self) -> None:
        self.btn_pick_audio.clicked.connect(self.pick_audio)
        self.btn_clear_audio.clicked.connect(self.clear_audio)
        self.btn_pick_cover.clicked.connect(self.pick_cover)
        self.btn_clear_cover.clicked.connect(self.clear_cover)
        self.btn_pick_output.clicked.connect(self.pick_output_dir)
        self.btn_open_output.clicked.connect(self.open_output_root)
        self.btn_open_song.clicked.connect(self.open_last_song)
        self.btn_generate.clicked.connect(self.run_generate)
        self.btn_cancel.clicked.connect(self.cancel_run)

        self.title_edit.textEdited.connect(lambda _: setattr(self, "_title_user_edited", True))

        self.adv_header.toggled.connect(self.toggle_advanced)
        self.log_header.toggled.connect(self.toggle_logs)
        self.chk_dark.toggled.connect(self.on_dark_toggle)

        self.preset_combo.currentTextChanged.connect(self.apply_preset)

        for w in [self.out_dir_edit, self.title_edit]:
            w.textChanged.connect(self._update_state)

    # ---------- Theme ----------
    def apply_theme(self, dark: bool) -> None:
        QApplication.instance().setStyleSheet(DARK_QSS if dark else LIGHT_QSS)

    def on_dark_toggle(self, checked: bool) -> None:
        self.dark_mode = checked
        self.apply_theme(dark=self.dark_mode)

    # ---------- Presets ----------
    def apply_preset(self, name: str) -> None:
        preset = DIFFICULTY_PRESETS.get(name)
        is_custom = preset is None

        # Show/hide manual controls
        self.custom_row_container.setVisible(is_custom)

        if is_custom:
            self.preset_hint.setText(
                "Custom: tweak density + spacing. Higher density = more notes; lower spacing = tighter notes."
            )
            return

        # Apply preset values
        assert preset is not None
        self.max_nps_spin.setValue(float(preset["max_nps"]))
        self.min_gap_spin.setValue(int(preset["min_gap_ms"]))

        # Leave seed as-is (your personal “riff style”)
        self.preset_hint.setText(
            f"Applied: {preset['max_nps']} nps density • {preset['min_gap_ms']}ms spacing. "
            "Pick Custom… if you want to tune."
        )

    # ---------- Collapsibles ----------
    def toggle_advanced(self, expanded: bool) -> None:
        self.adv_header.setText(f"{arrow_text(expanded)}  Advanced Settings")
        self.adv_group.setVisible(expanded)

    def toggle_logs(self, expanded: bool) -> None:
        self.log_header.setText(f"{arrow_text(expanded)}  Logs")
        self.log.setVisible(expanded)

    # ---------- State / log ----------
    def _update_state(self) -> None:
        running = self.proc is not None and self.proc.state() != QProcess.NotRunning
        has_audio = self.audio_path is not None and self.audio_path.exists()

        self.btn_generate.setEnabled((not running) and has_audio)
        self.btn_cancel.setEnabled(running)
        self.btn_open_song.setEnabled(self.last_out_song is not None and self.last_out_song.exists())

    def append_log(self, text: str) -> None:
        t = human_ok(text).strip("\n")
        if not t:
            return
        self.log.append(t)
        self.log.moveCursor(QTextCursor.End)

    # ---------- Album art preview ----------
    def update_cover_preview(self, image_path: Path | None) -> None:
        if not image_path or not image_path.exists():
            self.cover_preview.setPixmap(QPixmap())
            self.cover_preview.setText("Preview")
            self.cover_preview.setMinimumHeight(160)
            return

        pix = QPixmap(str(image_path))
        if pix.isNull():
            self.cover_preview.setPixmap(QPixmap())
            self.cover_preview.setText("Invalid image")
            return

        scaled = pix.scaled(QSize(250, 250), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.cover_preview.setText("")
        self.cover_preview.setPixmap(scaled)
        self.cover_preview.setMinimumHeight(scaled.height() + 10)

    # ---------- Pickers ----------
    def pick_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Audio File", "", "Audio Files (*.mp3 *.wav *.ogg *.flac)"
        )
        if not path:
            return
        self.audio_path = Path(path)
        self.audio_label.setText(self.audio_path.name)
        self.audio_label.setObjectName("")

        if (not self._title_user_edited) and (not self.title_edit.text().strip()):
            self.title_edit.setText(self.audio_path.stem)

        self.statusBar().showMessage(f"Selected audio: {self.audio_path.name}")
        self._update_state()

    def clear_audio(self) -> None:
        self.audio_path = None
        self.audio_label.setText("No file selected")
        self.audio_label.setObjectName("Muted")
        self.statusBar().showMessage("Audio cleared")
        self._update_state()

    def pick_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Album Art", "", "Images (*.png *.jpg *.jpeg)"
        )
        if not path:
            return
        self.cover_path = Path(path)
        self.cover_label.setText(self.cover_path.name)
        self.cover_label.setObjectName("")
        self.update_cover_preview(self.cover_path)

    def clear_cover(self) -> None:
        self.cover_path = None
        self.cover_label.setText("No art selected")
        self.cover_label.setObjectName("Muted")
        self.update_cover_preview(None)

    def pick_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose Output Folder")
        if path:
            self.out_dir_edit.setText(path)

    # ---------- Open helpers ----------
    def _open_in_finder(self, p: Path) -> None:
        proc = QProcess(self)
        proc.start("open", [str(p)])

    def open_output_root(self) -> None:
        out_root = Path(self.out_dir_edit.text()).expanduser().resolve()
        out_root.mkdir(parents=True, exist_ok=True)
        self._open_in_finder(out_root)

    def open_last_song(self) -> None:
        if self.last_out_song and self.last_out_song.exists():
            self._open_in_finder(self.last_out_song)

    # ---------- Run CLI ----------
    def build_cfg(self) -> RunConfig | None:
        if not self.audio_path:
            return None

        audio = self.audio_path.expanduser().resolve()
        if not audio.exists():
            QMessageBox.critical(self, "Audio missing", f"Audio file not found:\n{audio}")
            return None

        out_root = Path(self.out_dir_edit.text()).expanduser().resolve()
        title = self.title_edit.text().strip() or audio.stem
        mode_val = "real" if self.mode_real.isChecked() else "dummy"

        return RunConfig(
            audio=audio,
            out_root=out_root,
            title=title,
            artist=self.artist_edit.text().strip(),
            album=self.album_edit.text().strip(),
            genre=self.genre_edit.text().strip(),
            mode=mode_val,
            max_nps=float(self.max_nps_spin.value()),
            min_gap_ms=int(self.min_gap_spin.value()),
            seed=int(self.seed_spin.value()),
        )

    def run_generate(self) -> None:
        if self.proc and self.proc.state() != QProcess.NotRunning:
            return

        cfg = self.build_cfg()
        if not cfg:
            return

        py = venv_python()
        if not py.exists():
            QMessageBox.critical(self, "Missing venv", "Missing .venv.\n\nRun:\n  make install")
            return

        out_song = (cfg.out_root / cfg.title).resolve()
        out_song.mkdir(parents=True, exist_ok=True)
        self.last_out_song = out_song

        cmd = [
            str(py), "-m", "charter.cli",
            "--audio", str(cfg.audio),
            "--out", str(out_song),
            "--title", cfg.title,
            "--artist", cfg.artist,
            "--album", cfg.album,
            "--genre", cfg.genre,
            "--charter", cfg.charter,
            "--mode", cfg.mode,
            "--min-gap-ms", str(cfg.min_gap_ms),
            "--max-nps", f"{cfg.max_nps:.2f}",
            "--seed", str(cfg.seed),
        ]
        if cfg.fetch_metadata:
            cmd.append("--fetch-metadata")

        self.append_log(f"$ {' '.join(cmd)}\n")
        self.statusBar().showMessage("Generating chart…")
        self.btn_generate.setText("Generating…")

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.SeparateChannels)
        self.proc.setWorkingDirectory(str(repo_root()))

        self.proc.readyReadStandardOutput.connect(self._on_stdout)
        self.proc.readyReadStandardError.connect(self._on_stderr)
        self.proc.finished.connect(lambda code, status: self._on_finished(code, status, out_song))

        self.proc.start(cmd[0], cmd[1:])
        self._update_state()

    def cancel_run(self) -> None:
        if self.proc and self.proc.state() != QProcess.NotRunning:
            self.append_log("\n⏹ Cancel requested…")
            self.proc.kill()

    def _on_stdout(self) -> None:
        if not self.proc:
            return
        data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.append_log(data)

    def _on_stderr(self) -> None:
        if not self.proc:
            return
        data = bytes(self.proc.readAllStandardError()).decode("utf-8", errors="replace")
        if data.strip():
            if not self.log.isVisible():
                self.log_header.setChecked(True)
            self.append_log(data)

    def _on_finished(self, code: int, status: QProcess.ExitStatus, out_song: Path) -> None:
        self.btn_generate.setText("Generate Chart")
        ok = (status == QProcess.NormalExit) and (code == 0)

        if ok and self.cover_path and self.cover_path.exists():
            try:
                dest = out_song / "album.png"
                dest.write_bytes(self.cover_path.read_bytes())
                self.append_log(f"🖼 Copied album art → {dest}")
            except Exception as e:
                self.append_log(f"⚠️ Failed copying album art: {e}")

        generated_cover = out_song / "album.png"
        if generated_cover.exists():
            self.update_cover_preview(generated_cover)

        if ok:
            msg = self._stats_message(out_song) or f"✅ Chart generated.\n\nFolder:\n{out_song}"
            QMessageBox.information(self, "Chart generated", msg)
            self.statusBar().showMessage("Done")
        else:
            if not self.log.isVisible():
                self.log_header.setChecked(True)
            QMessageBox.critical(self, "Generation failed", f"CLI exited with code {code}.\n\n(Logs expanded below.)")
            self.statusBar().showMessage("Failed")

        self.proc = None
        self._update_state()

    def _stats_message(self, out_song: Path) -> str | None:
        stats_path = out_song / "stats.json"
        if not stats_path.exists():
            return None
        try:
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
            return (
                "✅ Chart generated successfully.\n\n"
                f"Notes: {stats.get('total_notes')} | Chords: {stats.get('total_chords')} | Sustains: {stats.get('total_sustains')}\n"
                f"Max NPS (1s): {stats.get('max_nps_1s')} | Avg NPS: {stats.get('avg_nps')}\n"
                f"Chart end: {stats.get('chart_duration_sec')}s\n\n"
                f"Folder:\n{out_song}"
            )
        except Exception:
            return f"✅ Chart generated.\n\nFolder:\n{out_song}"


def main() -> None:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.apply_theme(dark=w.dark_mode)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()