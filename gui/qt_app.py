from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QProcess, QSettings, QSize, Qt, QTimer
from PySide6.QtGui import (QAction, QColor, QDragEnterEvent, QDropEvent, QFont,
                           QFontDatabase, QIcon, QPalette, QPixmap)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup,
                               QCheckBox, QComboBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QFrame, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMainWindow, QMessageBox,
                               QProgressBar, QPushButton, QRadioButton,
                               QScrollArea, QSizePolicy, QSlider, QSpinBox,
                               QSplitter, QStyle, QTextEdit, QToolButton,
                               QVBoxLayout, QWidget)


# ---------------- Paths & Config ----------------
def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)

def repo_root() -> Path:
    if is_frozen(): return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]

def get_python_exec() -> str | Path:
    if is_frozen(): return sys.executable
    return repo_root() / ".venv" / "bin" / "python"

def form_label(text: str, required: bool = False) -> QLabel:
    txt = f"{text} <span style='color:#ff4444;'>*</span>" if required else text
    lbl = QLabel(txt)
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    lbl.setMinimumWidth(110)
    return lbl

def get_font(size: int = 10, bold: bool = False) -> QFont:
    f = QApplication.font()
    f.setPointSize(size)
    f.setBold(bold)
    return f

# --- Custom Widgets ---
class SafeComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class SafeSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class SafeDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class SafeSlider(QSlider):
    def wheelEvent(self, event):
        event.ignore()

DIFFICULTY_PRESETS: dict[str, dict[str, float | int] | None] = {
    "Medium (Casual)":   {"max_nps": 2.25, "min_gap_ms": 170, "sustain": 50, "chord": 5},
    "Medium (Balanced)": {"max_nps": 2.80, "min_gap_ms": 140, "sustain": 15, "chord": 12},
    "Medium (Intense)":  {"max_nps": 3.40, "min_gap_ms": 110, "sustain": 5,  "chord": 25},
    "Medium (Chaotic)":  {"max_nps": 4.20, "min_gap_ms": 85,  "sustain": 0,  "chord": 40},
    "Custom…":           None,
}

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
    allow_orange: bool
    chord_prob: float
    sustain_len: float
    grid_snap: str
    sustain_threshold: float
    sustain_buffer: float
    rhythmic_glue: bool
    charter: str = "Zullo7569"
    fetch_metadata: bool = True

# ---------------- Theme ----------------
class ThemeManager:
    @staticmethod
    def apply_style(app: QApplication, dark_mode: bool):
        app.setStyle("Fusion")
        font = app.font()
        font.setPointSize(10)
        app.setFont(font)
        palette = QPalette()

        if dark_mode:
            # Dark Theme
            base = QColor(30, 35, 40)
            mid = QColor(45, 50, 55)
            text = QColor(220, 220, 220)
            highlight = QColor(50, 120, 210)

            palette.setColor(QPalette.Window, base)
            palette.setColor(QPalette.WindowText, text)
            palette.setColor(QPalette.Base, mid)
            palette.setColor(QPalette.AlternateBase, base)
            palette.setColor(QPalette.Text, text)
            palette.setColor(QPalette.Button, mid)
            palette.setColor(QPalette.ButtonText, text)
            palette.setColor(QPalette.Highlight, highlight)
            palette.setColor(QPalette.HighlightedText, Qt.white)

            # Interactions
            palette.setColor(QPalette.Light, QColor(60, 65, 70)) # Hover
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 100, 100))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 100, 100))
            palette.setColor(QPalette.PlaceholderText, QColor(120, 130, 140))

        else:
            # Light Theme (Explicitly defined to override Dark OS defaults)
            base = QColor(245, 245, 250)
            white = QColor(255, 255, 255)
            text = QColor(30, 30, 40)
            highlight = QColor(0, 100, 200)
            btn_bg = QColor(255, 255, 255)

            palette.setColor(QPalette.Window, base)
            palette.setColor(QPalette.WindowText, text)
            palette.setColor(QPalette.Base, white)
            palette.setColor(QPalette.AlternateBase, base)
            palette.setColor(QPalette.Text, text)
            palette.setColor(QPalette.Button, btn_bg)
            palette.setColor(QPalette.ButtonText, text)
            palette.setColor(QPalette.Highlight, highlight)
            palette.setColor(QPalette.HighlightedText, white)

            # Explicit Interaction Colors (Fixes OS Dark Mode bleed)
            palette.setColor(QPalette.Light, QColor(255, 255, 255)) # Hover
            palette.setColor(QPalette.Midlight, QColor(230, 230, 240))
            palette.setColor(QPalette.Dark, QColor(200, 200, 210))
            palette.setColor(QPalette.Mid, QColor(210, 210, 220)) # Borders
            palette.setColor(QPalette.Shadow, QColor(150, 150, 160))

            # Disabled States (Explicitly readable grey)
            disabled_text = QColor(160, 160, 170)
            palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
            palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
            palette.setColor(QPalette.PlaceholderText, QColor(150, 150, 160))

        app.setPalette(palette)

        # Stylesheet overrides
        app.setStyleSheet("""
            QGroupBox {
                border: 1px solid palette(mid);
                border-radius: 6px;
                margin-top: 24px;
                padding-top: 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }

            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QListWidget {
                padding: 6px;
                border-radius: 4px;
                border: 1px solid palette(mid);
                background-color: palette(base);
                color: palette(text);
                font-size: 11px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QListWidget:focus, QSlider:focus {
                border: 1px solid palette(highlight);
            }

            /* Disabled Inputs */
            QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
                background-color: palette(window);
                color: palette(disabled-text);
                border: 1px dashed palette(mid);
            }

            QComboBox QAbstractItemView {
                background-color: palette(base);
                color: palette(text);
                selection-background-color: palette(highlight);
                selection-color: palette(highlighted-text);
            }

            QPushButton {
                padding: 8px 16px;
                border-radius: 5px;
                border: 1px solid palette(mid);
                background-color: palette(button);
                color: palette(text);
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: palette(midlight);
                border: 1px solid palette(dark);
            }
            QPushButton:disabled {
                background-color: palette(window);
                color: palette(disabled-text);
                border: 1px solid palette(mid);
            }

            /* PRIMARY BUTTON (Fixed Height) */
            QPushButton#Primary {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                font-weight: bold;
                border: 1px solid palette(highlight);
                min-height: 18px;
                max-height: 18px;
                min-width: 120px;
                max-width: 120px;
            }
            QPushButton#Primary:hover {
                border: 1px solid palette(text);
                background-color: palette(highlight);
            }
            QPushButton#Primary:disabled {
                background-color: palette(mid);
                color: palette(disabled-text);
                border: 1px solid palette(mid);
            }

            QCheckBox { spacing: 8px; font-size: 11px; }

            QStatusBar { background: palette(window); border-top: 1px solid palette(mid); min-height: 50px; max-height: 50px; }
            QStatusBar::item { border: none; }

            QProgressBar {
                border: 1px solid palette(mid);
                border-radius: 4px;
                text-align: center;
                color: palette(text);
                background: palette(base);
            }
            QProgressBar::chunk {
                background-color: palette(highlight);
            }
        """)

# ---------------- Log Window ----------------
class LogWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logs")
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono_font.setPointSize(11)
        self.text_edit.setFont(mono_font)
        layout.addWidget(self.text_edit)

        row_btns = QHBoxLayout()
        btn_clear = QPushButton("Clear Logs")
        btn_clear.clicked.connect(self.text_edit.clear)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.hide)
        row_btns.addStretch()
        row_btns.addWidget(btn_clear)
        row_btns.addWidget(btn_close)
        layout.addLayout(row_btns)

    def append_text(self, text: str):
        self.text_edit.append(text)
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

    def clear(self):
        self.text_edit.clear()

    def get_text(self) -> str:
        return self.text_edit.toPlainText()

# ---------------- Main Window ----------------
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CloneHero 1-Click Charter")
        self.setAcceptDrops(True)
        self.settings = QSettings("Zullo", "1ClickCharter")

        self.audio_path: Path | None = None
        self.cover_path: Path | None = None
        self.last_out_song: Path | None = None
        self.proc: QProcess | None = None
        self.validator_proc: QProcess | None = None

        # QUEUE SYSTEM
        self.song_queue: list[Path] = []

        self.log_window = LogWindow()
        self.dark_mode = self.settings.value("dark_mode", True, type=bool)
        self._title_user_edited = False

        self._build_ui()
        self._wire()
        self._restore_settings()

        self.resize(980, 750)
        ThemeManager.apply_style(QApplication.instance(), self.dark_mode)
        self.apply_preset(self.preset_combo.currentText())
        self._update_state()
        QTimer.singleShot(100, self.snap_to_content)
        self.statusBar().showMessage("Ready")

    def closeEvent(self, event) -> None:
        self.log_window.close()
        self.settings.setValue("dark_mode", self.chk_dark.isChecked())
        c_val = self.charter_edit.text().strip() or "Zullo7569"
        self.settings.setValue("charter", c_val)
        self.settings.setValue("out_dir", self.out_dir_edit.text())
        self.settings.setValue("preset", self.preset_combo.currentText())
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # --- HEADER ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(16)
        header_layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel()
        icon_path = repo_root() / "icons" / "icon_og.png"
        if icon_path.exists():
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                pix = pix.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_lbl.setPixmap(pix)

        title_lbl = QLabel("CloneHero 1-Click Charter")
        title_lbl.setFont(get_font(40, True))
        title_lbl.setStyleSheet("color: palette(text);")

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        main_layout.addWidget(header_widget)

        # --- BODY ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter)

        # ================= Sidebar =================
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.sidebar_widget.setMinimumWidth(340)
        self.sidebar_widget.setMaximumWidth(340)

        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 12, 0)
        sidebar_layout.setSpacing(18)

        # Audio Input Group
        grp_audio = QGroupBox("Input Audio (REQUIRED)")
        grp_audio_layout = QVBoxLayout(grp_audio)
        self.audio_label = QLabel("Drag Audio Files Here")
        self.audio_label.setAlignment(Qt.AlignCenter)
        self.audio_label.setWordWrap(True)
        self.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text); font-size: 11px;")

        # ADD Button
        self.btn_add_audio = QPushButton("Add Songs...")
        self.btn_add_audio.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.btn_add_audio.setToolTip("Add files to queue")
        self.btn_add_audio.setCursor(Qt.PointingHandCursor)

        self.btn_clear_audio = QToolButton()
        self.btn_clear_audio.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_clear_audio.setCursor(Qt.PointingHandCursor)
        self.btn_clear_audio.setToolTip("Skip current song")

        row_audio_btns = QHBoxLayout()
        row_audio_btns.addWidget(self.btn_add_audio, 1)
        row_audio_btns.addWidget(self.btn_clear_audio, 0)

        grp_audio_layout.addWidget(self.audio_label)
        grp_audio_layout.addLayout(row_audio_btns)
        sidebar_layout.addWidget(grp_audio)

        # Queue Box
        self.grp_queue = QGroupBox("Pending Queue")
        self.grp_queue.setVisible(True)

        queue_layout = QVBoxLayout(self.grp_queue)
        queue_layout.setContentsMargins(8, 8, 8, 8)
        queue_layout.setSpacing(8)

        self.queue_list = QListWidget()
        self.queue_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.queue_list.setMaximumHeight(65)
        self.queue_list.setStyleSheet("border: 1px solid palette(mid); border-radius: 4px;")

        self.btn_clear_queue_all = QPushButton("Clear Queue")
        self.btn_clear_queue_all.setCursor(Qt.PointingHandCursor)

        queue_layout.addWidget(self.queue_list)
        queue_layout.addWidget(self.btn_clear_queue_all)

        sidebar_layout.addWidget(self.grp_queue)

        # Art
        grp_art = QGroupBox("Album Art")
        grp_art_layout = QVBoxLayout(grp_art)

        self.cover_preview = QLabel("Drag Art Here")
        self.cover_preview.setAlignment(Qt.AlignCenter)
        self.cover_preview.setFixedSize(260, 260)
        self.cover_preview.setStyleSheet("border: 2px dashed palette(mid); border-radius: 6px; color: palette(disabled-text); font-style: italic; font-size: 11px;")

        row_art_btns = QHBoxLayout()
        self.btn_pick_cover = QPushButton("Image...")
        self.btn_pick_cover.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.btn_pick_cover.setCursor(Qt.PointingHandCursor)

        self.btn_clear_cover = QToolButton()
        self.btn_clear_cover.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_clear_cover.setCursor(Qt.PointingHandCursor)

        row_art_btns.addWidget(self.btn_pick_cover, 1)
        row_art_btns.addWidget(self.btn_clear_cover, 0)

        grp_art_layout.addStretch()
        grp_art_layout.addWidget(self.cover_preview, 0, Qt.AlignCenter)
        grp_art_layout.addStretch()
        grp_art_layout.addLayout(row_art_btns)

        sidebar_layout.addWidget(grp_art)
        sidebar_layout.addStretch(1)

        # ================= Main Panel =================
        self.main_widget = QWidget()
        self.main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.main_widget.setMinimumWidth(500)

        main_layout_inner = QVBoxLayout(self.main_widget)
        main_layout_inner.setContentsMargins(12, 0, 0, 0)
        main_layout_inner.setSpacing(22)

        # Metadata
        grp_meta = QGroupBox("Song Metadata")
        form_meta = QFormLayout(grp_meta)
        form_meta.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_meta.setLabelAlignment(Qt.AlignRight)
        form_meta.setVerticalSpacing(12)

        self.title_edit = QLineEdit()
        self.artist_edit = QLineEdit()
        self.album_edit = QLineEdit()
        self.genre_edit = QLineEdit()
        self.genre_edit.setPlaceholderText("Default: Rock")
        self.charter_edit = QLineEdit()
        self.charter_edit.setPlaceholderText("Default: Zullo7569")

        self.btn_clear_meta = QToolButton()
        self.btn_clear_meta.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_clear_meta.setToolTip("Clear all metadata fields")
        self.btn_clear_meta.setCursor(Qt.PointingHandCursor)

        form_meta.addRow(form_label("Title", required=True), self.title_edit)
        form_meta.addRow(form_label("Artist", required=True), self.artist_edit)
        form_meta.addRow(form_label("Album"), self.album_edit)
        form_meta.addRow(form_label("Genre"), self.genre_edit)
        form_meta.addRow(form_label("Charter"), self.charter_edit)

        row_clear = QHBoxLayout()
        row_clear.addStretch()
        row_clear.addWidget(QLabel("Clear Fields "))
        row_clear.addWidget(self.btn_clear_meta)
        form_meta.addRow("", row_clear)

        main_layout_inner.addWidget(grp_meta)

        # Configuration
        self.adv_container = QGroupBox("Configuration")
        adv_layout = QVBoxLayout(self.adv_container)

        self.chk_adv = QCheckBox("Show Advanced Settings")
        self.chk_adv.setStyleSheet("font-weight: bold; margin-bottom: 6px;")
        self.chk_adv.setCursor(Qt.PointingHandCursor)

        self.adv_content = QWidget()
        self.adv_content.setVisible(False)
        adv_form = QFormLayout(self.adv_content)
        adv_form.setLabelAlignment(Qt.AlignRight)
        adv_form.setVerticalSpacing(10)
        adv_form.setContentsMargins(10, 0, 0, 0)

        self.preset_combo = SafeComboBox()
        self.preset_combo.addItems(list(DIFFICULTY_PRESETS.keys()))
        self.preset_combo.setCurrentText("Medium (Balanced)")
        self.preset_combo.setCursor(Qt.PointingHandCursor)

        self.preset_hint = QLabel("Select a preset to auto-configure settings.")
        self.preset_hint.setStyleSheet("color: palette(disabled-text); font-size: 11px;")

        adv_form.addRow(form_label("Difficulty"), self.preset_combo)
        adv_form.addRow(QLabel(""), self.preset_hint)

        self.custom_controls = QWidget()
        custom_form = QFormLayout(self.custom_controls)
        custom_form.setContentsMargins(0, 0, 0, 0)
        custom_form.setVerticalSpacing(10)

        self.mode_group = QButtonGroup(self)
        self.mode_real = QRadioButton("Real (Audio Analysis)")
        self.mode_dummy = QRadioButton("Dummy (Metronome)")
        self.mode_real.setCursor(Qt.PointingHandCursor)
        self.mode_dummy.setCursor(Qt.PointingHandCursor)
        self.mode_real.setChecked(True)
        self.mode_group.addButton(self.mode_real)
        self.mode_group.addButton(self.mode_dummy)

        row_mode = QHBoxLayout()
        row_mode.addWidget(self.mode_real)
        row_mode.addWidget(self.mode_dummy)
        row_mode.addStretch()

        self.max_nps_spin = SafeDoubleSpinBox()
        self.max_nps_spin.setRange(1.0, 10.0)
        self.max_nps_spin.setSingleStep(0.1)
        self.max_nps_spin.setSuffix(" NPS")
        self.max_nps_spin.setMinimumHeight(30)

        self.min_gap_spin = SafeSpinBox()
        self.min_gap_spin.setRange(10, 1000)
        self.min_gap_spin.setSingleStep(10)
        self.min_gap_spin.setSuffix(" ms")
        self.min_gap_spin.setMinimumHeight(30)

        self.seed_spin = SafeSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setMinimumHeight(30)
        self.seed_spin.setToolTip("Seed for random generation.")

        self.chk_orange = QCheckBox("Allow Orange Lane")
        self.chk_orange.setChecked(True)
        self.chk_orange.setCursor(Qt.PointingHandCursor)

        self.chord_slider = SafeSlider()
        self.chord_slider.setOrientation(Qt.Horizontal)
        self.chord_slider.setRange(0, 50)
        self.chord_slider.setValue(12)
        self.chord_slider.setCursor(Qt.PointingHandCursor)

        self.sustain_slider = SafeSlider()
        self.sustain_slider.setOrientation(Qt.Horizontal)
        self.sustain_slider.setRange(0, 100)
        self.sustain_slider.setValue(50)
        self.sustain_slider.setCursor(Qt.PointingHandCursor)

        self.grid_combo = SafeComboBox()
        self.grid_combo.addItems(["1/4", "1/8", "1/16"])
        self.grid_combo.setCurrentText("1/8")
        self.grid_combo.setCursor(Qt.PointingHandCursor)

        # New Sustain Tuning
        self.sustain_gap_spin = SafeDoubleSpinBox()
        self.sustain_gap_spin.setRange(0.1, 2.0)
        self.sustain_gap_spin.setSingleStep(0.1)
        self.sustain_gap_spin.setValue(0.8)
        self.sustain_gap_spin.setSuffix(" s")

        self.sustain_buffer_spin = SafeDoubleSpinBox()
        self.sustain_buffer_spin.setRange(0.05, 0.5)
        self.sustain_buffer_spin.setSingleStep(0.05)
        self.sustain_buffer_spin.setValue(0.15)
        self.sustain_buffer_spin.setSuffix(" s")

        # NEW CHECKBOX
        self.chk_rhythm_glue = QCheckBox("Rhythmic Glue (Repeat Patterns)")
        self.chk_rhythm_glue.setChecked(True)
        self.chk_rhythm_glue.setToolTip("If a rhythm repeats, force the same strum/chord pattern.")

        custom_form.addRow(form_label("Generation Mode"), row_mode)
        custom_form.addRow(form_label("Max Notes/Sec"), self.max_nps_spin)
        custom_form.addRow(form_label("Min Note Spacing"), self.min_gap_spin)
        custom_form.addRow(form_label("Pattern Variation"), self.seed_spin)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("color: palette(mid);")
        custom_form.addRow(div)

        custom_form.addRow(form_label("Grid Snap"), self.grid_combo)
        custom_form.addRow(form_label("5th Lane"), self.chk_orange)
        custom_form.addRow(form_label("Consistency"), self.chk_rhythm_glue)
        custom_form.addRow(form_label("Chord Density"), self.chord_slider)
        custom_form.addRow(form_label("Sustain Prob."), self.sustain_slider)

        # Sustain Tuning Group
        custom_form.addRow(form_label("Min Gap for Sustain"), self.sustain_gap_spin)
        custom_form.addRow(form_label("Sustain End Buffer"), self.sustain_buffer_spin)

        adv_form.addRow(self.custom_controls)
        adv_layout.addWidget(self.chk_adv)
        adv_layout.addWidget(self.adv_content)
        main_layout_inner.addWidget(self.adv_container)

        # Output (Left Aligned Buttons)
        grp_out = QGroupBox("Output Destination")
        out_container_layout = QVBoxLayout(grp_out)

        out_row1 = QHBoxLayout()
        self.out_dir_edit = QLineEdit("")
        self.out_dir_edit.setPlaceholderText("Select output folder... (Required)")

        self.btn_pick_output = QPushButton("Browse...")
        self.btn_pick_output.setCursor(Qt.PointingHandCursor)

        self.btn_clear_out = QToolButton()
        self.btn_clear_out.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_clear_out.setToolTip("Clear output path")
        self.btn_clear_out.setCursor(Qt.PointingHandCursor)

        out_row1.addWidget(self.out_dir_edit, 1)
        out_row1.addWidget(self.btn_pick_output, 0)
        out_row1.addWidget(self.btn_clear_out, 0)

        out_row2 = QHBoxLayout()
        out_row2.setSpacing(8)

        self.btn_open_output = QPushButton("Open Folder")
        self.btn_open_output.setCursor(Qt.PointingHandCursor)
        self.btn_open_song = QPushButton("Open Last Song")
        self.btn_open_song.setCursor(Qt.PointingHandCursor)

        out_row2.addWidget(self.btn_open_output)
        out_row2.addWidget(self.btn_open_song)
        out_row2.addStretch() # Push left

        out_container_layout.addLayout(out_row1)
        out_container_layout.addLayout(out_row2)

        grp_out.setTitle("Output Destination  (REQUIRED)")
        main_layout_inner.addWidget(grp_out)

        main_layout_inner.addStretch(1)

        # SCROLL AREA
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setWidget(self.main_widget)
        main_scroll.setFrameShape(QFrame.NoFrame)

        splitter.addWidget(self.sidebar_widget)
        splitter.addWidget(main_scroll)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Footer
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 5, 20, 5)
        footer_layout.setSpacing(16)

        self.chk_dark = QCheckBox("Dark Mode")
        self.chk_dark.setChecked(self.dark_mode)
        self.chk_dark.setCursor(Qt.PointingHandCursor)

        self.btn_show_logs = QPushButton("Show Logs")
        self.btn_show_logs.setCursor(Qt.PointingHandCursor)

        self.btn_help = QPushButton("Help")
        self.btn_help.setCursor(Qt.PointingHandCursor)
        self.btn_help.clicked.connect(self.show_help)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setMinimumHeight(18)

        # New Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate mode (bouncing)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedWidth(45)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(18)

        self.btn_generate = QPushButton("GENERATE CHART")
        self.btn_generate.setObjectName("Primary")
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.setMinimumHeight(18)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: palette(mid);")

        footer_layout.addWidget(self.progress_bar)
        footer_layout.addWidget(sep)
        footer_layout.addWidget(self.chk_dark)
        footer_layout.addWidget(self.btn_show_logs)
        footer_layout.addWidget(self.btn_help)
        footer_layout.addWidget(sep)

        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_generate)

        self.statusBar().addPermanentWidget(footer)

        # Menu
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)
        act_clear_log = QAction("Clear Log", self)
        act_clear_log.triggered.connect(lambda: self.log_window.clear())

        menu = self.menuBar().addMenu("File")
        menu.addAction(act_clear_log)
        menu.addSeparator()
        menu.addAction(act_quit)

    def _wire(self) -> None:
        self.btn_add_audio.clicked.connect(self.add_to_queue_dialog)
        self.btn_clear_audio.clicked.connect(self.clear_audio)
        self.btn_pick_cover.clicked.connect(self.pick_cover)
        self.btn_clear_cover.clicked.connect(self.clear_cover)
        self.btn_pick_output.clicked.connect(self.pick_output_dir)
        self.btn_open_output.clicked.connect(self.open_output_root)
        self.btn_open_song.clicked.connect(self.open_last_song)
        self.btn_generate.clicked.connect(self.run_generate)
        self.btn_cancel.clicked.connect(self.cancel_run)

        self.btn_clear_queue_all.clicked.connect(self.clear_queue)

        self.btn_clear_meta.clicked.connect(self.clear_metadata)
        self.btn_clear_out.clicked.connect(self.clear_output_dir)
        self.btn_show_logs.clicked.connect(self.log_window.show)

        self.title_edit.textEdited.connect(lambda _: setattr(self, "_title_user_edited", True))
        self.chk_dark.toggled.connect(self.on_dark_toggle)
        self.preset_combo.currentTextChanged.connect(self.apply_preset)

        self.chk_adv.toggled.connect(self.on_toggle_advanced)

        for w in [self.out_dir_edit, self.title_edit, self.artist_edit]:
            w.textChanged.connect(self._update_state)

    def snap_to_content(self) -> None:
        if self.centralWidget():
            self.centralWidget().layout().activate()
        h = self.sidebar_widget.sizeHint().height()
        h = max(h, 600)
        w = 310 + 550 + 40
        self.resize(w, h)

    def show_help(self) -> None:
        msg = """
        <h3>How to Use 1-Click Charter</h3>
        <ol>
            <li><b>Add Audio:</b> Drag files or click "+ Add".</li>
            <li><b>Metadata:</b> Fill in Title/Artist for the current song.</li>
            <li><b>Generate:</b> Process the current song. If queue items exist, the next one loads automatically.</li>
        </ol>
        <p><b>Queue:</b> The small box below the audio input shows pending songs. Use the Trash icon on the input box to skip the current song.</p>
        """
        QMessageBox.information(self, "Help", msg.strip())

    def clear_metadata(self) -> None:
        self.title_edit.clear()
        self.artist_edit.clear()
        self.album_edit.clear()
        self.genre_edit.clear()
        self.charter_edit.clear()
        self._title_user_edited = False
        self._update_state()

    def clear_song_info(self) -> None:
        self.title_edit.clear()
        self.artist_edit.clear()
        self.album_edit.clear()
        self.clear_cover()
        self._title_user_edited = False

    def clear_output_dir(self) -> None:
        self.out_dir_edit.clear()
        self._update_state()

    def clear_queue(self) -> None:
        self.song_queue.clear()
        self._update_queue_display()

    def clear_for_next_run(self) -> None:
        self.clear_audio()
        self.clear_cover()
        self.title_edit.clear()
        self.artist_edit.clear()
        self.album_edit.clear()
        self._title_user_edited = False
        self._update_state()

    def _restore_settings(self) -> None:
        saved_charter = self.settings.value("charter", "Zullo7569", type=str)
        if saved_charter != "Zullo7569":
            self.charter_edit.setText(saved_charter)
        saved_out = self.settings.value("out_dir", "", type=str)
        self.out_dir_edit.setText(saved_out)
        last_preset = self.settings.value("preset", "Medium (Balanced)", type=str)
        self.preset_combo.setCurrentText(last_preset)
        geom = self.settings.value("geometry")
        if geom: self.restoreGeometry(geom)

    # ---------- Logic / Processing ----------
    def _update_queue_display(self) -> None:
        self.queue_list.clear()
        self.btn_clear_queue_all.setEnabled(bool(self.song_queue))
        for i, path in enumerate(self.song_queue):
            item = QListWidgetItem(self.queue_list)
            wid = QWidget()
            hbox = QHBoxLayout(wid)
            hbox.setContentsMargins(4, 0, 4, 0)
            lbl = QLabel(path.name)
            lbl.setStyleSheet("background: transparent; font-size: 11px;")
            btn = QToolButton()
            btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("border: none;")
            btn.clicked.connect(lambda checked=False, idx=i: self.remove_queue_item(idx))
            hbox.addWidget(lbl, 1)
            hbox.addWidget(btn, 0)
            item.setSizeHint(wid.sizeHint())
            self.queue_list.setItemWidget(item, wid)
        QTimer.singleShot(10, self.snap_to_content)

    def remove_queue_item(self, index: int) -> None:
        if 0 <= index < len(self.song_queue):
            self.song_queue.pop(index)
            self._update_queue_display()

    def add_to_queue_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Add Audio to Queue", "", "Audio (*.mp3 *.wav *.ogg *.flac)")
        if not files: return
        new_paths = [Path(f) for f in files]
        if not self.audio_path and new_paths:
            first = new_paths.pop(0)
            self.load_audio(first)
        self.song_queue.extend(new_paths)
        self._update_queue_display()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        audio_exts = {".mp3", ".wav", ".ogg", ".flac"}
        img_exts = {".jpg", ".jpeg", ".png"}
        new_songs = []
        found_cover = None
        for url in urls:
            path = Path(url.toLocalFile())
            if not path.exists(): continue
            if path.is_file():
                if path.suffix.lower() in audio_exts:
                    new_songs.append(path)
                elif path.suffix.lower() in img_exts:
                    found_cover = path
            elif path.is_dir():
                for f in path.rglob("*"):
                    if f.is_file() and f.suffix.lower() in audio_exts:
                        new_songs.append(f)
        if found_cover: self.load_cover(found_cover)
        if new_songs:
            if not self.audio_path:
                first = new_songs.pop(0)
                self.load_audio(first)
            self.song_queue.extend(new_songs)
            self._update_queue_display()

    def on_dark_toggle(self, checked: bool) -> None:
        self.dark_mode = checked
        ThemeManager.apply_style(QApplication.instance(), self.dark_mode)

    def on_toggle_advanced(self, checked: bool) -> None:
        self.adv_content.setVisible(checked)

    def apply_preset(self, name: str) -> None:
        preset = DIFFICULTY_PRESETS.get(name)
        is_custom = preset is None
        self.custom_controls.setVisible(is_custom)
        if is_custom:
            self.preset_hint.setText("Manual control enabled. Adjust density and gap below.")
        else:
            self.max_nps_spin.setValue(float(preset["max_nps"]))
            self.min_gap_spin.setValue(int(preset["min_gap_ms"]))
            self.sustain_slider.setValue(int(preset["sustain"]))
            self.chord_slider.setValue(int(preset["chord"]))

            self.preset_hint.setText(f"Preset Active: {preset['max_nps']} NPS | {preset['min_gap_ms']}ms Gap")

    def _update_state(self) -> None:
        running = self.proc is not None and self.proc.state() != QProcess.NotRunning
        has_audio = self.audio_path is not None and self.audio_path.exists()
        has_title = bool(self.title_edit.text().strip())
        has_artist = bool(self.artist_edit.text().strip())
        has_out = bool(self.out_dir_edit.text().strip())

        self.btn_generate.setEnabled((not running) and has_audio and has_title and has_artist and has_out)
        self.btn_cancel.setEnabled(running)

        self.btn_open_output.setEnabled(bool(self.out_dir_edit.text().strip()))
        self.btn_open_song.setEnabled(self.last_out_song is not None and self.last_out_song.exists())

    def append_log(self, text: str) -> None:
        t = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not t: return
        self.log_window.append_text(t)

    def update_cover_preview(self, image_path: Path | None) -> None:
        if not image_path or not image_path.exists():
            self.cover_preview.setPixmap(QPixmap())
            self.cover_preview.setText("Drag Art Here")
            return
        pix = QPixmap(str(image_path))
        if pix.isNull():
            self.cover_preview.setText("Invalid Image")
            return
        scaled = pix.scaled(QSize(250, 250), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.cover_preview.setText("")
        self.cover_preview.setPixmap(scaled)

    def pick_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose Audio", "", "Audio (*.mp3 *.wav *.ogg *.flac)")
        if not path: return
        self.load_audio(Path(path))

    def load_audio(self, path: Path) -> None:
        self.audio_path = path
        self.audio_label.setText(self.audio_path.name)
        self.audio_label.setStyleSheet("color: palette(text); font-weight: bold;")
        if (not self._title_user_edited) and (not self.title_edit.text().strip()):
            self.title_edit.setText(self.audio_path.stem)
        self.statusBar().showMessage(f"Loaded: {self.audio_path.name}")
        self._update_state()
        QTimer.singleShot(0, self.snap_to_content)

    def clear_audio(self) -> None:
        self.clear_song_info()
        if self.song_queue:
            next_song = self.song_queue.pop(0)
            self._update_queue_display()
            self.load_audio(next_song)
            self.statusBar().showMessage(f"Queue: Loaded {next_song.name}")
        else:
            self.audio_path = None
            self.audio_label.setText("Drag Audio Files Here")
            self.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text); font-size: 11px;")
            self._update_state()
            self.audio_label.adjustSize()
            self.statusBar().showMessage("Audio cleared")
            QTimer.singleShot(10, self.snap_to_content)

    def pick_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose Art", "", "Images (*.png *.jpg *.jpeg)")
        if not path: return
        self.load_cover(Path(path))

    def load_cover(self, path: Path) -> None:
        self.cover_path = path
        self.update_cover_preview(self.cover_path)

    def clear_cover(self) -> None:
        self.cover_path = None
        self.update_cover_preview(None)

    def pick_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose Output Folder")
        if path: self.out_dir_edit.setText(path)

    def open_output_root(self) -> None:
        out_root = Path(self.out_dir_edit.text()).expanduser().resolve()
        out_root.mkdir(parents=True, exist_ok=True)
        self._open_in_finder(out_root)

    def open_last_song(self) -> None:
        if self.last_out_song and self.last_out_song.exists():
            self._open_in_finder(self.last_out_song)

    def _open_in_finder(self, p: Path) -> None:
        proc = QProcess(self)
        if sys.platform == "darwin": proc.start("open", [str(p)])
        elif sys.platform == "win32": proc.start("explorer", [str(p)])
        else: proc.start("xdg-open", [str(p)])

    def build_cfg(self) -> RunConfig | None:
        if not self.audio_path: return None
        audio = self.audio_path.expanduser().resolve()
        if not audio.exists():
            QMessageBox.critical(self, "Error", "Audio file missing.")
            return None
        out_txt = self.out_dir_edit.text().strip()
        if not out_txt:
            QMessageBox.critical(self, "Error", "Output folder is required.")
            return None
        out_root = Path(out_txt).expanduser().resolve()
        title = self.title_edit.text().strip()
        if not title: return None
        mode_val = "real" if self.mode_real.isChecked() else "dummy"
        genre_val = self.genre_edit.text().strip() or "Rock"
        charter_val = self.charter_edit.text().strip() or "Zullo7569"
        return RunConfig(
            audio=audio, out_root=out_root, title=title,
            artist=self.artist_edit.text().strip(), album=self.album_edit.text().strip(),
            genre=genre_val, mode=mode_val,
            max_nps=float(self.max_nps_spin.value()),
            min_gap_ms=int(self.min_gap_spin.value()),
            seed=int(self.seed_spin.value()),
            charter=charter_val,
            allow_orange=self.chk_orange.isChecked(),
            chord_prob=self.chord_slider.value() / 100.0,
            sustain_len=self.sustain_slider.value() / 100.0,
            grid_snap=self.grid_combo.currentText(),
            sustain_threshold=float(self.sustain_gap_spin.value()),
            sustain_buffer=float(self.sustain_buffer_spin.value()),
            rhythmic_glue=self.chk_rhythm_glue.isChecked()
        )

    def run_generate(self) -> None:
        if self.proc and self.proc.state() != QProcess.NotRunning: return
        cfg = self.build_cfg()
        if not cfg: return
        py_exec = get_python_exec()
        if not is_frozen() and not Path(py_exec).exists():
            QMessageBox.critical(self, "Error", "Missing .venv python.")
            return
        out_song = (cfg.out_root / cfg.title).resolve()
        out_song.mkdir(parents=True, exist_ok=True)
        self.last_out_song = out_song
        if is_frozen(): cmd = [str(py_exec), "--internal-cli"]
        else: cmd = [str(py_exec), "-m", "charter.cli"]
        cmd.extend([
            "--audio", str(cfg.audio), "--out", str(out_song),
            "--title", cfg.title, "--artist", cfg.artist,
            "--album", cfg.album, "--genre", cfg.genre,
            "--charter", cfg.charter, "--mode", cfg.mode,
            "--min-gap-ms", str(cfg.min_gap_ms), "--max-nps", f"{cfg.max_nps:.2f}",
            "--seed", str(cfg.seed),
            "--chord-prob", str(cfg.chord_prob),
            "--sustain-len", str(cfg.sustain_len),
            "--grid-snap", cfg.grid_snap,
            "--sustain-threshold", str(cfg.sustain_threshold),
            "--sustain-buffer", str(cfg.sustain_buffer)
        ])
        if not cfg.allow_orange: cmd.append("--no-orange")
        if not self.chk_rhythm_glue.isChecked(): cmd.append("--no-rhythmic-glue")
        if cfg.fetch_metadata: cmd.append("--fetch-metadata")
        self.log_window.clear()
        self.append_log(f"Starting generation for: {cfg.title}...")

        self.btn_generate.setText("Analyzing...")
        self.btn_generate.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.SeparateChannels)
        if not is_frozen(): self.proc.setWorkingDirectory(str(repo_root()))
        self.proc.readyReadStandardOutput.connect(self._on_stdout)
        self.proc.readyReadStandardError.connect(self._on_stderr)
        self.proc.finished.connect(lambda c, s: self._on_finished(c, s, out_song))
        self.proc.start(cmd[0], cmd[1:])
        self._update_state()

    def cancel_run(self) -> None:
        if self.proc:
            self.proc.kill()
            self.append_log("Cancelled by user.")

    def _on_stdout(self) -> None:
        if not self.proc: return
        data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.append_log(data)

    def _on_stderr(self) -> None:
        if not self.proc: return
        data = bytes(self.proc.readAllStandardError()).decode("utf-8", errors="replace")
        self.append_log(data)

    def _on_finished(self, code: int, status: QProcess.ExitStatus, out_song: Path) -> None:
        self.btn_generate.setText("GENERATE CHART")
        self.progress_bar.setVisible(False)

        ok = (status == QProcess.NormalExit) and (code == 0)

        if ok:
            if self.cover_path and self.cover_path.exists():
                try:
                    dest = out_song / "album.png"
                    dest.write_bytes(self.cover_path.read_bytes())
                    self.append_log(f"Cover copied to {dest}")
                except Exception as e: self.append_log(f"Cover copy failed: {e}")
            gen_cover = out_song / "album.png"
            if gen_cover.exists(): self.update_cover_preview(gen_cover)
            self.run_health_check(out_song)

            if self.song_queue:
                next_song = self.song_queue.pop(0)
                self.clear_song_info()
                self.load_audio(next_song)
                self._update_queue_display()
                self.statusBar().showMessage(f"Chart generated! Loaded next: {next_song.name}")
            else:
                self.clear_song_info()
                self.audio_path = None
                self.audio_label.setText("Drag Audio Files Here")
                self.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text); font-size: 11px;")
                self._update_state()
                self.statusBar().showMessage("Queue Finished")
        else:
            reason = "Unknown error."
            logs = self.log_window.get_text()
            for line in reversed(logs.splitlines()):
                if "Error" in line or "Exception" in line:
                    reason = line.strip()
                    break
            QMessageBox.critical(self, "Generation Failed", f"Failed to generate chart.\n\nReason: {reason}\n\nCheck logs for full details.")
            self.statusBar().showMessage("Generation Failed")
        self.proc = None
        self._update_state()

    def run_health_check(self, song_dir: Path) -> None:
        self.statusBar().showMessage("Validating...")
        QTimer.singleShot(0, self.snap_to_content)
        py_exec = get_python_exec()
        script = repo_root() / "tools" / "validator.py"
        self.validator_proc = QProcess(self)
        self.validator_proc.finished.connect(lambda c, s: self._on_health_finished(c, s, song_dir))
        self.validator_proc.start(str(py_exec), [str(script), str(song_dir), "--summary"])

    def _on_health_finished(self, code: int, status: QProcess.ExitStatus, song_dir: Path) -> None:
        output = bytes(self.validator_proc.readAllStandardOutput()).decode("utf-8")
        warnings = []
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("- ") and "WARNINGS" in output:
                warnings.append(line[2:])
        self.append_log("\n--- VALIDATION REPORT ---")
        self.append_log(output)

        if not self.song_queue:
            msg = f"Chart generated successfully!\n\nLocation:\n{song_dir}"
            if warnings: msg += "\n\nWarnings:\n" + "\n".join(f"• {w}" for w in warnings)
            title = "Generation Complete" if not warnings else "Complete (With Warnings)"
            QMessageBox.information(self, title, msg) if not warnings else QMessageBox.warning(self, title, msg)
            self.statusBar().showMessage("Ready")

        self.validator_proc = None

def main() -> None:
    app = QApplication(sys.argv)
    font = QApplication.font()
    font.setPointSize(10)
    app.setFont(font)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
