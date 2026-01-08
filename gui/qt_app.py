from __future__ import annotations
import sys
import json
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QSize, QTimer, QSettings
from PySide6.QtGui import QFont, QPixmap, QAction, QPalette, QColor, QDragEnterEvent, QDropEvent, QFontDatabase
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
    QStyle,
    QSlider
)

# ---------------- Paths & Config ----------------
def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)

def repo_root() -> Path:
    if is_frozen(): return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]

def get_python_exec() -> str | Path:
    if is_frozen(): return sys.executable
    return repo_root() / ".venv" / "bin" / "python"

def form_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    lbl.setMinimumWidth(110)
    return lbl

def get_font(size: int = 10, bold: bool = False) -> QFont:
    f = QApplication.font()
    f.setPointSize(size)
    f.setBold(bold)
    return f

DIFFICULTY_PRESETS: dict[str, dict[str, float | int] | None] = {
    "Medium (Casual)":   {"max_nps": 2.25, "min_gap_ms": 170},
    "Medium (Balanced)": {"max_nps": 2.80, "min_gap_ms": 140},
    "Medium (Intense)":  {"max_nps": 3.35, "min_gap_ms": 115},
    "Medium (Chaotic)":  {"max_nps": 3.90, "min_gap_ms": 95},
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
    charter: str = "Zullo7569"
    fetch_metadata: bool = True

# ---------------- Theme ----------------
class ThemeManager:
    @staticmethod
    def apply_style(app: QApplication, dark_mode: bool):
        app.setStyle("Fusion")
        palette = QPalette()
        if dark_mode:
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
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 100, 100))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 100, 100))
            palette.setColor(QPalette.PlaceholderText, QColor(120, 130, 140))
        else:
            base = QColor(240, 240, 245)
            white = QColor(255, 255, 255)
            text = QColor(20, 20, 30)
            highlight = QColor(0, 100, 200)
            palette.setColor(QPalette.Window, base)
            palette.setColor(QPalette.WindowText, text)
            palette.setColor(QPalette.Base, white)
            palette.setColor(QPalette.AlternateBase, base)
            palette.setColor(QPalette.Text, text)
            palette.setColor(QPalette.Button, white)
            palette.setColor(QPalette.ButtonText, text)
            palette.setColor(QPalette.Highlight, highlight)
            palette.setColor(QPalette.HighlightedText, white)
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(150, 150, 160))
            palette.setColor(QPalette.PlaceholderText, QColor(140, 140, 150))
        app.setPalette(palette)

        app.setStyleSheet("""
            QGroupBox { border: 1px solid palette(mid); border-radius: 6px; margin-top: 24px; padding-top: 12px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLineEdit, QComboBox { padding: 6px; border-radius: 4px; border: 1px solid palette(mid); background-color: palette(base); }
            QLineEdit:focus, QComboBox:focus { border: 1px solid palette(highlight); }
            QPushButton { padding: 8px 16px; border-radius: 5px; border: 1px solid palette(mid); background-color: palette(button); }
            QPushButton:hover { background-color: palette(light); }
            QPushButton#Primary { background-color: palette(highlight); color: palette(highlighted-text); font-weight: bold; border: 1px solid palette(highlight); }
            QPushButton#Primary:hover { border: 1px solid palette(text); }
            QCheckBox { spacing: 8px; }
            QLabel#HealthGood { color: #2ecc71; font-weight: bold; }
            QLabel#HealthWarn { color: #f1c40f; font-weight: bold; }
            QLabel#HealthBad { color: #e74c3c; font-weight: bold; }
        """)

# ---------------- Main Window ----------------
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CH 1-Click Charter")
        self.setAcceptDrops(True)
        self.settings = QSettings("Zullo", "1ClickCharter")

        self.audio_path: Path | None = None
        self.cover_path: Path | None = None
        self.last_out_song: Path | None = None
        self.proc: QProcess | None = None
        self.validator_proc: QProcess | None = None
        self.dark_mode = self.settings.value("dark_mode", True, type=bool)
        self._title_user_edited = False

        self._build_ui()
        self._wire()
        self._restore_settings()

        # FIX: Ensure window starts at a healthy size so it isn't squashed
        self.resize(950, 650)

        ThemeManager.apply_style(QApplication.instance(), self.dark_mode)
        self.apply_preset(self.preset_combo.currentText())
        self._update_state()

        QTimer.singleShot(0, self.snap_to_content)
        self.statusBar().showMessage("Ready")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter)

        # ================= Sidebar (Fixed Width) =================
        sidebar_widget = QWidget()
        sidebar_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sidebar_widget.setMinimumWidth(280)

        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 12, 0)
        sidebar_layout.setSpacing(18)

        # Title
        title_block = QVBoxLayout()
        title_lbl = QLabel("CH 1-Click")
        title_lbl.setFont(get_font(22, True))
        sub_lbl = QLabel("Automated Charting Tool")
        sub_lbl.setStyleSheet("color: palette(disabled-text); font-size: 13px;")
        title_block.addWidget(title_lbl)
        title_block.addWidget(sub_lbl)
        sidebar_layout.addLayout(title_block)

        # Audio
        grp_audio = QGroupBox("Input Audio")
        grp_audio_layout = QVBoxLayout(grp_audio)
        self.audio_label = QLabel("Drag & drop audio here")
        self.audio_label.setWordWrap(True)
        self.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text);")

        row_audio_btns = QHBoxLayout()
        self.btn_pick_audio = QPushButton("Browse...")
        self.btn_pick_audio.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.btn_clear_audio = QToolButton()
        self.btn_clear_audio.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        row_audio_btns.addWidget(self.btn_pick_audio, 1)
        row_audio_btns.addWidget(self.btn_clear_audio, 0)

        grp_audio_layout.addWidget(self.audio_label)
        grp_audio_layout.addLayout(row_audio_btns)
        sidebar_layout.addWidget(grp_audio)

        # Art
        grp_art = QGroupBox("Album Art")
        grp_art_layout = QVBoxLayout(grp_art)
        self.cover_preview = QLabel("Drag Art Here")
        self.cover_preview.setAlignment(Qt.AlignCenter)
        self.cover_preview.setFixedSize(260, 260)
        self.cover_preview.setStyleSheet("border: 2px dashed palette(mid); border-radius: 6px; color: palette(disabled-text);")

        row_art_btns = QHBoxLayout()
        self.btn_pick_cover = QPushButton("Image...")
        self.btn_pick_cover.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.btn_clear_cover = QToolButton()
        self.btn_clear_cover.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        row_art_btns.addWidget(self.btn_pick_cover, 1)
        row_art_btns.addWidget(self.btn_clear_cover, 0)

        grp_art_layout.addWidget(self.cover_preview)
        grp_art_layout.addLayout(row_art_btns)
        sidebar_layout.addWidget(grp_art)

        # Tools
        grp_tools = QGroupBox("Quick Actions")
        grp_tools_layout = QVBoxLayout(grp_tools)
        self.btn_open_output = QPushButton("Open Output Folder")
        self.btn_open_song = QPushButton("Open Last Song")
        grp_tools_layout.addWidget(self.btn_open_output)
        grp_tools_layout.addWidget(self.btn_open_song)
        sidebar_layout.addWidget(grp_tools)

        sidebar_layout.addStretch(1)

        # ================= Main Panel (Scrollable) =================
        main_widget = QWidget()
        main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # FIX: Force the Right Panel to have your preferred width
        main_widget.setMinimumWidth(525)

        main_layout_inner = QVBoxLayout(main_widget)
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
        self.charter_edit = QLineEdit("Zullo7569")

        form_meta.addRow(form_label("Title"), self.title_edit)
        form_meta.addRow(form_label("Artist"), self.artist_edit)
        form_meta.addRow(form_label("Album"), self.album_edit)
        form_meta.addRow(form_label("Genre"), self.genre_edit)
        form_meta.addRow(form_label("Charter"), self.charter_edit)
        main_layout_inner.addWidget(grp_meta)

        # Output
        grp_out = QGroupBox("Output Destination")
        out_layout = QHBoxLayout(grp_out)
        self.out_dir_edit = QLineEdit("output")
        self.btn_pick_output = QPushButton("Browse...")
        out_layout.addWidget(self.out_dir_edit, 1)
        out_layout.addWidget(self.btn_pick_output, 0)
        main_layout_inner.addWidget(grp_out)

        # Advanced
        self.adv_container = QGroupBox("Configuration")
        adv_layout = QVBoxLayout(self.adv_container)

        self.chk_adv = QCheckBox("Show Advanced Settings")
        self.chk_adv.setStyleSheet("font-weight: bold; margin-bottom: 6px;")

        self.adv_content = QWidget()
        self.adv_content.setVisible(False)
        adv_form = QFormLayout(self.adv_content)
        adv_form.setLabelAlignment(Qt.AlignRight)
        adv_form.setVerticalSpacing(10)
        adv_form.setContentsMargins(10, 0, 0, 0)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(DIFFICULTY_PRESETS.keys()))
        self.preset_combo.setCurrentText("Medium (Balanced)")
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
        self.mode_real.setChecked(True)
        self.mode_group.addButton(self.mode_real)
        self.mode_group.addButton(self.mode_dummy)

        row_mode = QHBoxLayout()
        row_mode.addWidget(self.mode_real)
        row_mode.addWidget(self.mode_dummy)
        row_mode.addStretch()

        self.max_nps_spin = QDoubleSpinBox()
        self.max_nps_spin.setRange(1.0, 10.0)
        self.max_nps_spin.setSingleStep(0.1)
        self.max_nps_spin.setSuffix(" NPS")
        self.max_nps_spin.setMinimumHeight(30)
        self.max_nps_spin.setToolTip("Target density of notes per second.")

        self.min_gap_spin = QSpinBox()
        self.min_gap_spin.setRange(10, 1000)
        self.min_gap_spin.setSingleStep(10)
        self.min_gap_spin.setSuffix(" ms")
        self.min_gap_spin.setMinimumHeight(30)
        self.min_gap_spin.setToolTip("Minimum millisecond gap between notes.")

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setMinimumHeight(30)
        self.seed_spin.setToolTip("Seed for random generation.")

        # New Controls
        self.chk_orange = QCheckBox("Allow Orange Lane")
        self.chk_orange.setChecked(True)

        self.chord_slider = QSlider(Qt.Horizontal)
        self.chord_slider.setRange(0, 50)
        self.chord_slider.setValue(12)
        self.chord_slider.setToolTip("How often single notes become chords.")

        self.sustain_slider = QSlider(Qt.Horizontal)
        self.sustain_slider.setRange(0, 100)
        self.sustain_slider.setValue(50)
        self.sustain_slider.setToolTip("How often long gaps become sustains vs. taps.")

        self.grid_combo = QComboBox()
        self.grid_combo.addItems(["1/4", "1/8", "1/16"])
        self.grid_combo.setCurrentText("1/8")

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
        custom_form.addRow(form_label("Chord Density"), self.chord_slider)
        custom_form.addRow(form_label("Sustain Length"), self.sustain_slider)

        adv_form.addRow(self.custom_controls)
        adv_layout.addWidget(self.chk_adv)
        adv_layout.addWidget(self.adv_content)
        main_layout_inner.addWidget(self.adv_container)

        # Health Status
        self.health_bar = QFrame()
        self.health_bar.setVisible(False)
        self.health_bar.setStyleSheet("background-color: palette(alternate-base); border-radius: 6px; padding: 4px;")
        hb_layout = QHBoxLayout(self.health_bar)
        hb_layout.setContentsMargins(8, 4, 8, 4)
        self.health_icon = QLabel("●")
        self.health_icon.setFont(get_font(14, True))
        self.health_text = QLabel("Checking...")
        self.health_text.setFont(get_font(10, True))
        hb_layout.addWidget(self.health_icon)
        hb_layout.addWidget(self.health_text, 1)
        main_layout_inner.addWidget(self.health_bar)

        # Actions
        row_actions = QHBoxLayout()
        self.btn_generate = QPushButton("GENERATE CHART")
        self.btn_generate.setObjectName("Primary")
        self.btn_generate.setMinimumHeight(48)
        self.btn_generate.setFont(get_font(11, True))
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setMinimumHeight(48)
        row_actions.addWidget(self.btn_generate, 1)
        row_actions.addWidget(self.btn_cancel, 0)
        main_layout_inner.addLayout(row_actions)

        # Logs
        self.grp_logs = QGroupBox("Logs")
        log_layout = QVBoxLayout(self.grp_logs)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono_font.setPointSize(10)
        self.log_view.setFont(mono_font)
        self.log_view.setPlaceholderText("Process output...")
        log_layout.addWidget(self.log_view)

        row_toggles = QHBoxLayout()
        row_toggles.setSpacing(16)
        self.chk_dark = QCheckBox("Dark Mode")
        self.chk_dark.setChecked(self.dark_mode)
        self.chk_dark.setStyleSheet("font-weight: bold;")
        self.chk_log = QCheckBox("Show Logs")
        self.chk_log.setStyleSheet("font-weight: bold;")
        row_toggles.addWidget(self.chk_dark)
        row_toggles.addWidget(self.chk_log)
        row_toggles.addStretch(1)

        main_layout_inner.addLayout(row_toggles)
        main_layout_inner.addWidget(self.grp_logs)
        self.grp_logs.setVisible(False)
        main_layout_inner.addStretch(1)

        # SCROLL AREA
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setWidget(main_widget)
        main_scroll.setFrameShape(QFrame.NoFrame)

        splitter.addWidget(sidebar_widget)
        splitter.addWidget(main_scroll)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Menu
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)
        act_clear = QAction("Clear Log", self)
        act_clear.triggered.connect(lambda: self.log_view.clear())

        menu = self.menuBar().addMenu("File")
        menu.addAction(act_clear)
        menu.addSeparator()
        menu.addAction(act_quit)

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
        self.chk_dark.toggled.connect(self.on_dark_toggle)
        self.preset_combo.currentTextChanged.connect(self.apply_preset)

        self.chk_adv.toggled.connect(self.on_toggle_advanced)
        self.chk_log.toggled.connect(self.on_toggle_logs)

        for w in [self.out_dir_edit, self.title_edit]:
            w.textChanged.connect(self._update_state)

    def snap_to_content(self) -> None:
        """
        Forces window height to match the sidebar's preferred height.
        """
        QApplication.processEvents()
        if self.centralWidget():
            self.centralWidget().layout().activate()

        self.resize(self.width(), 0)
        self.adjustSize()

    # ---------- Persistence, DragDrop, Logic, Pickers, Execution ----------
    def _restore_settings(self) -> None:
        self.charter_edit.setText(self.settings.value("charter", "Zullo7569", type=str))
        self.out_dir_edit.setText(self.settings.value("out_dir", "output", type=str))
        last_preset = self.settings.value("preset", "Medium (Balanced)", type=str)
        self.preset_combo.setCurrentText(last_preset)
        geom = self.settings.value("geometry")
        if geom: self.restoreGeometry(geom)

    def closeEvent(self, event) -> None:
        self.settings.setValue("dark_mode", self.chk_dark.isChecked())
        self.settings.setValue("charter", self.charter_edit.text())
        self.settings.setValue("out_dir", self.out_dir_edit.text())
        self.settings.setValue("preset", self.preset_combo.currentText())
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if not path.exists(): continue
            suffix = path.suffix.lower()
            if suffix in {".mp3", ".wav", ".ogg", ".flac"}:
                self.load_audio(path)
                break
            elif suffix in {".jpg", ".jpeg", ".png"}:
                self.load_cover(path)
                break

    def on_dark_toggle(self, checked: bool) -> None:
        self.dark_mode = checked
        ThemeManager.apply_style(QApplication.instance(), self.dark_mode)

    def on_toggle_advanced(self, checked: bool) -> None:
        self.adv_content.setVisible(checked)
        # We don't necessarily snap here because scrolling handles it,
        # but it keeps the window clean if user expands.
        QTimer.singleShot(0, self.snap_to_content)

    def on_toggle_logs(self, checked: bool) -> None:
        self.grp_logs.setVisible(checked)
        QTimer.singleShot(0, self.snap_to_content)

    def apply_preset(self, name: str) -> None:
        preset = DIFFICULTY_PRESETS.get(name)
        is_custom = preset is None
        self.custom_controls.setVisible(is_custom)
        if is_custom:
            self.preset_hint.setText("Manual control enabled. Adjust density and gap below.")
        else:
            self.max_nps_spin.setValue(float(preset["max_nps"]))
            self.min_gap_spin.setValue(int(preset["min_gap_ms"]))
            self.preset_hint.setText(f"Preset Active: {preset['max_nps']} NPS | {preset['min_gap_ms']}ms Gap")
        QTimer.singleShot(0, self.snap_to_content)

    def _update_state(self) -> None:
        running = self.proc is not None and self.proc.state() != QProcess.NotRunning
        has_audio = self.audio_path is not None and self.audio_path.exists()
        self.btn_generate.setEnabled((not running) and has_audio)
        self.btn_cancel.setEnabled(running)
        self.btn_open_song.setEnabled(self.last_out_song is not None and self.last_out_song.exists())

    def append_log(self, text: str) -> None:
        t = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not t: return
        self.log_view.append(t)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

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
        self.audio_path = None
        self.audio_label.setText("Drag & drop audio here")
        self.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text);")
        self._update_state()
        self.audio_label.adjustSize()
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
        out_root = Path(self.out_dir_edit.text()).expanduser().resolve()
        title = self.title_edit.text().strip() or audio.stem
        mode_val = "real" if self.mode_real.isChecked() else "dummy"
        return RunConfig(
            audio=audio, out_root=out_root, title=title,
            artist=self.artist_edit.text().strip(), album=self.album_edit.text().strip(),
            genre=self.genre_edit.text().strip(), mode=mode_val,
            max_nps=float(self.max_nps_spin.value()),
            min_gap_ms=int(self.min_gap_spin.value()),
            seed=int(self.seed_spin.value()),
            charter=self.charter_edit.text().strip(),
            allow_orange=self.chk_orange.isChecked(),
            chord_prob=self.chord_slider.value() / 100.0,
            sustain_len=self.sustain_slider.value() / 100.0,
            grid_snap=self.grid_combo.currentText()
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
            "--grid-snap", cfg.grid_snap
        ])
        if not cfg.allow_orange: cmd.append("--no-orange")
        if cfg.fetch_metadata: cmd.append("--fetch-metadata")
        self.log_view.clear()
        if not self.grp_logs.isVisible(): self.chk_log.setChecked(True)
        self.health_bar.setVisible(False)
        self.append_log(f"Starting generation for: {cfg.title}...")
        self.btn_generate.setText("Generating...")
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
        ok = (status == QProcess.NormalExit) and (code == 0)
        if ok and self.cover_path and self.cover_path.exists():
            try:
                dest = out_song / "album.png"
                dest.write_bytes(self.cover_path.read_bytes())
                self.append_log(f"Cover copied to {dest}")
            except Exception as e: self.append_log(f"Cover copy failed: {e}")
        gen_cover = out_song / "album.png"
        if gen_cover.exists(): self.update_cover_preview(gen_cover)
        if ok:
            self.run_health_check(out_song)
            self.statusBar().showMessage("Generation Complete")
        else:
            QMessageBox.critical(self, "Failed", f"Process exited with code {code}. See logs.")
            self.statusBar().showMessage("Generation Failed")
        self.proc = None
        self._update_state()

    def run_health_check(self, song_dir: Path) -> None:
        self.health_bar.setVisible(True)
        self.health_icon.setText("⏳")
        self.health_text.setText("Validating chart health...")
        self.health_icon.setObjectName("HealthWarn")
        self.health_text.setStyleSheet("")
        QTimer.singleShot(0, self.snap_to_content)
        py_exec = get_python_exec()
        script = repo_root() / "tools" / "validator.py"
        self.validator_proc = QProcess(self)
        self.validator_proc.finished.connect(lambda c, s: self._on_health_finished(c, s))
        self.validator_proc.start(str(py_exec), [str(script), str(song_dir), "--summary"])

    def _on_health_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        output = bytes(self.validator_proc.readAllStandardOutput()).decode("utf-8")
        if code == 0:
            self.health_icon.setText("●")
            self.health_icon.setObjectName("HealthGood")
            self.health_text.setText("Chart Healthy (Ready to Play)")
            self.health_text.setStyleSheet("color: palette(text);")
            if "WARNINGS:" in output:
                self.health_icon.setObjectName("HealthWarn")
                self.health_text.setText("Playable (See Logs for Warnings)")
        else:
            self.health_icon.setText("●")
            self.health_icon.setObjectName("HealthBad")
            self.health_text.setText("Chart Errors Detected")
        self.health_icon.style().unpolish(self.health_icon)
        self.health_icon.style().polish(self.health_icon)
        self.append_log("\n--- VALIDATION REPORT ---")
        self.append_log(output)
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
