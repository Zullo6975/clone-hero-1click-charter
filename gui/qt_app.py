from __future__ import annotations
import sys
import json
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QSize
from PySide6.QtGui import QFont, QPixmap, QAction, QPalette, QColor, QIcon
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
    QStyleFactory,
    QStyle,
)

# ---------------- Paths ----------------
def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)

def repo_root() -> Path:
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]

def get_python_exec() -> str | Path:
    if is_frozen():
        return sys.executable
    return repo_root() / ".venv" / "bin" / "python"

# ---------------- Difficulty presets ----------------
DIFFICULTY_PRESETS: dict[str, dict[str, float | int] | None] = {
    "Medium (Casual)":   {"max_nps": 2.25, "min_gap_ms": 170},
    "Medium (Balanced)": {"max_nps": 2.80, "min_gap_ms": 140},
    "Medium (Intense)":  {"max_nps": 3.35, "min_gap_ms": 115},
    "Medium (Chaotic)":  {"max_nps": 3.90, "min_gap_ms": 95},
    "Custom…":           None,
}

# ---------------- Theme Manager ----------------
class ThemeManager:
    """
    Manages the Fusion palette to ensure consistent, non-clashing colors
    across the entire application.
    """
    @staticmethod
    def apply_style(app: QApplication, dark_mode: bool):
        app.setStyle("Fusion")

        palette = QPalette()
        if dark_mode:
            # Modern Dark Slate Palette
            base = QColor(25, 30, 40)
            alt_base = QColor(35, 40, 50)
            text = QColor(240, 240, 240)
            disabled_text = QColor(127, 127, 127)
            highlight = QColor(64, 156, 255)  # Soft Blue

            palette.setColor(QPalette.Window, base)
            palette.setColor(QPalette.WindowText, text)
            palette.setColor(QPalette.Base, alt_base)
            palette.setColor(QPalette.AlternateBase, base)
            palette.setColor(QPalette.ToolTipBase, text)
            palette.setColor(QPalette.ToolTipText, base)
            palette.setColor(QPalette.Text, text)
            palette.setColor(QPalette.Button, base)
            palette.setColor(QPalette.ButtonText, text)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, highlight)
            palette.setColor(QPalette.Highlight, highlight)
            palette.setColor(QPalette.HighlightedText, Qt.black)
            palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
        else:
            # Clean Light Palette
            base = QColor(245, 245, 250)
            white = QColor(255, 255, 255)
            text = QColor(20, 25, 30)
            disabled_text = QColor(120, 120, 120)
            highlight = QColor(50, 100, 220)  # Deep Blue

            palette.setColor(QPalette.Window, base)
            palette.setColor(QPalette.WindowText, text)
            palette.setColor(QPalette.Base, white)
            palette.setColor(QPalette.AlternateBase, base)
            palette.setColor(QPalette.ToolTipBase, white)
            palette.setColor(QPalette.ToolTipText, text)
            palette.setColor(QPalette.Text, text)
            palette.setColor(QPalette.Button, base)
            palette.setColor(QPalette.ButtonText, text)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, highlight)
            palette.setColor(QPalette.Highlight, highlight)
            palette.setColor(QPalette.HighlightedText, white)
            palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)

        app.setPalette(palette)

        # Minimal stylesheet just for specific tweaks (padding/radius)
        # We rely on Palette for colors to avoid clashes.
        app.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid palette(mid);
                border-radius: 6px;
                margin-top: 22px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 6px;
                border-radius: 4px;
                border: 1px solid palette(mid);
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid palette(highlight);
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: 1px solid palette(mid);
            }
            QPushButton:hover {
                background-color: palette(midlight);
            }
            QPushButton#Primary {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                font-weight: bold;
                border: 1px solid palette(highlight);
            }
            QPushButton#Primary:hover {
                border: 1px solid palette(text);
            }
        """)

# ---------------- Helpers ----------------
def form_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    # Allow label to shrink if needed, but prefer visible
    lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
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
    charter: str = "Zullo7569"
    fetch_metadata: bool = True

# ---------------- Main Window ----------------
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CH 1-Click Charter")
        self.resize(1000, 750)

        self.audio_path: Path | None = None
        self.cover_path: Path | None = None
        self.last_out_song: Path | None = None
        self.proc: QProcess | None = None

        self.dark_mode = False
        self._title_user_edited = False

        self._build_ui()
        self._wire()

        # Apply initial theme
        ThemeManager.apply_style(QApplication.instance(), self.dark_mode)

        self.apply_preset(self.preset_combo.currentText())
        self._update_state()
        self.statusBar().showMessage("Ready")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        # Use a vertical layout for the whole window first?
        # No, horizontal splitter is good, but let's make it smarter.
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter)

        # ================= Sidebar =================
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 10, 0) # Right margin for separation
        sidebar_layout.setSpacing(16)

        # Title Block
        title_block = QVBoxLayout()
        title_lbl = QLabel("CH 1-Click")
        title_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
        sub_lbl = QLabel("Automated Charting Tool")
        sub_lbl.setStyleSheet("color: palette(disabled-text);")
        title_block.addWidget(title_lbl)
        title_block.addWidget(sub_lbl)
        sidebar_layout.addLayout(title_block)

        # Theme Toggle
        self.chk_dark = QCheckBox("Dark Mode")
        sidebar_layout.addWidget(self.chk_dark)

        # Audio Section
        grp_audio = QGroupBox("Input Audio")
        grp_audio_layout = QVBoxLayout(grp_audio)

        self.audio_label = QLabel("No file selected")
        self.audio_label.setStyleSheet("color: palette(disabled-text); font-style: italic;")
        self.audio_label.setWordWrap(True)

        row_audio_btns = QHBoxLayout()
        self.btn_pick_audio = QPushButton("Browse...")
        self.btn_pick_audio.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))

        self.btn_clear_audio = QToolButton()
        self.btn_clear_audio.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_clear_audio.setToolTip("Clear Selection")

        row_audio_btns.addWidget(self.btn_pick_audio, 1)
        row_audio_btns.addWidget(self.btn_clear_audio, 0)

        grp_audio_layout.addWidget(self.audio_label)
        grp_audio_layout.addLayout(row_audio_btns)
        sidebar_layout.addWidget(grp_audio)

        # Art Section
        grp_art = QGroupBox("Album Art")
        grp_art_layout = QVBoxLayout(grp_art)

        self.cover_preview = QLabel("Preview")
        self.cover_preview.setAlignment(Qt.AlignCenter)
        self.cover_preview.setMinimumHeight(150)
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

        # Tools Section
        grp_tools = QGroupBox("Quick Actions")
        grp_tools_layout = QVBoxLayout(grp_tools)
        self.btn_open_output = QPushButton("Open Output Folder")
        self.btn_open_song = QPushButton("Open Last Song")
        grp_tools_layout.addWidget(self.btn_open_output)
        grp_tools_layout.addWidget(self.btn_open_song)
        sidebar_layout.addWidget(grp_tools)

        sidebar_layout.addStretch(1)

        # Wrap sidebar in scroll area just in case small screen
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setWidget(sidebar_widget)
        sidebar_scroll.setFrameShape(QFrame.NoFrame)

        # ================= Main Panel =================
        main_widget = QWidget()
        main_layout_inner = QVBoxLayout(main_widget)
        main_layout_inner.setContentsMargins(10, 0, 0, 0)
        main_layout_inner.setSpacing(20)

        # Metadata Group
        grp_meta = QGroupBox("Song Metadata")
        form_meta = QFormLayout(grp_meta)
        form_meta.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_meta.setLabelAlignment(Qt.AlignRight)

        self.title_edit = QLineEdit()
        self.artist_edit = QLineEdit()
        self.album_edit = QLineEdit()
        self.genre_edit = QLineEdit("Rock")

        form_meta.addRow(form_label("Title"), self.title_edit)
        form_meta.addRow(form_label("Artist"), self.artist_edit)
        form_meta.addRow(form_label("Album"), self.album_edit)
        form_meta.addRow(form_label("Genre"), self.genre_edit)

        main_layout_inner.addWidget(grp_meta)

        # Output Path Group
        grp_out = QGroupBox("Output Destination")
        out_layout = QHBoxLayout(grp_out)
        self.out_dir_edit = QLineEdit("output")
        self.btn_pick_output = QPushButton("Browse...")
        out_layout.addWidget(self.out_dir_edit, 1)
        out_layout.addWidget(self.btn_pick_output, 0)
        main_layout_inner.addWidget(grp_out)

        # Advanced Settings (Collapsible)
        self.adv_container = QGroupBox("Configuration")
        adv_layout = QVBoxLayout(self.adv_container)

        # Toggle Button for Advanced
        self.btn_toggle_adv = QPushButton("Show Advanced Settings")
        self.btn_toggle_adv.setCheckable(True)
        self.btn_toggle_adv.setFlat(True)
        # Use built-in arrow icon
        self.btn_toggle_adv.setIcon(self.style().standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton))
        self.btn_toggle_adv.setStyleSheet("text-align: left; font-weight: bold;")

        # Hidden Content
        self.adv_content = QWidget()
        self.adv_content.setVisible(False)
        adv_form = QFormLayout(self.adv_content)
        adv_form.setLabelAlignment(Qt.AlignRight)

        # Presets
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(DIFFICULTY_PRESETS.keys()))
        self.preset_combo.setCurrentText("Medium (Balanced)")
        self.preset_hint = QLabel("Select a preset to auto-configure settings.")
        self.preset_hint.setStyleSheet("color: palette(disabled-text); font-size: 11px;")

        adv_form.addRow(form_label("Difficulty"), self.preset_combo)
        adv_form.addRow(QLabel(""), self.preset_hint)

        # Custom Controls
        self.custom_controls = QWidget()
        custom_form = QFormLayout(self.custom_controls)
        custom_form.setContentsMargins(0,0,0,0)

        # Mode
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

        # Spinboxes
        self.max_nps_spin = QDoubleSpinBox()
        self.max_nps_spin.setRange(1.0, 10.0)
        self.max_nps_spin.setSingleStep(0.1)
        self.max_nps_spin.setSuffix(" nps")

        self.min_gap_spin = QSpinBox()
        self.min_gap_spin.setRange(10, 1000)
        self.min_gap_spin.setSingleStep(10)
        self.min_gap_spin.setSuffix(" ms")

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 999999)

        custom_form.addRow(form_label("Generation Mode"), row_mode)
        custom_form.addRow(form_label("Max Density"), self.max_nps_spin)
        custom_form.addRow(form_label("Min Note Gap"), self.min_gap_spin)
        custom_form.addRow(form_label("Random Seed"), self.seed_spin)

        adv_form.addRow(self.custom_controls)

        adv_layout.addWidget(self.btn_toggle_adv)
        adv_layout.addWidget(self.adv_content)

        main_layout_inner.addWidget(self.adv_container)

        # Action Buttons
        row_actions = QHBoxLayout()
        self.btn_generate = QPushButton("GENERATE CHART")
        self.btn_generate.setObjectName("Primary")
        self.btn_generate.setMinimumHeight(50)
        self.btn_generate.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_generate.setCursor(Qt.PointingHandCursor)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setMinimumHeight(50)

        row_actions.addWidget(self.btn_generate, 1)
        row_actions.addWidget(self.btn_cancel, 0)
        main_layout_inner.addLayout(row_actions)

        # Logs
        self.grp_logs = QGroupBox("Logs")
        log_layout = QVBoxLayout(self.grp_logs)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        self.log_view.setPlaceholderText("Process output will appear here...")
        log_layout.addWidget(self.log_view)

        # Collapsible log logic
        self.btn_toggle_log = QPushButton("Show Logs")
        self.btn_toggle_log.setCheckable(True)
        self.btn_toggle_log.setFlat(True)
        self.btn_toggle_log.setIcon(self.style().standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton))

        # Add to layout
        main_layout_inner.addWidget(self.btn_toggle_log)
        main_layout_inner.addWidget(self.grp_logs)

        # Initially hide logs
        self.grp_logs.setVisible(False)

        # Add scroll to main area
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setWidget(main_widget)
        main_scroll.setFrameShape(QFrame.NoFrame)

        splitter.addWidget(sidebar_scroll)
        splitter.addWidget(main_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3) # Main area is 3x larger

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

        self.btn_toggle_adv.toggled.connect(self.on_toggle_advanced)
        self.btn_toggle_log.toggled.connect(self.on_toggle_logs)

        for w in [self.out_dir_edit, self.title_edit]:
            w.textChanged.connect(self._update_state)

    # ---------- Logic ----------
    def on_dark_toggle(self, checked: bool) -> None:
        self.dark_mode = checked
        ThemeManager.apply_style(QApplication.instance(), self.dark_mode)

    def on_toggle_advanced(self, checked: bool) -> None:
        self.adv_content.setVisible(checked)
        icon = QStyle.SP_ArrowDown if checked else QStyle.SP_ToolBarHorizontalExtensionButton
        self.btn_toggle_adv.setIcon(self.style().standardIcon(icon))

    def on_toggle_logs(self, checked: bool) -> None:
        self.grp_logs.setVisible(checked)
        icon = QStyle.SP_ArrowDown if checked else QStyle.SP_ToolBarHorizontalExtensionButton
        self.btn_toggle_log.setIcon(self.style().standardIcon(icon))

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
        # Auto-scroll
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def update_cover_preview(self, image_path: Path | None) -> None:
        if not image_path or not image_path.exists():
            self.cover_preview.setPixmap(QPixmap())
            self.cover_preview.setText("Preview")
            self.cover_preview.setMinimumHeight(150)
            return

        pix = QPixmap(str(image_path))
        if pix.isNull():
            self.cover_preview.setText("Invalid Image")
            return

        # Scale nicely
        scaled = pix.scaled(QSize(250, 250), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.cover_preview.setText("")
        self.cover_preview.setPixmap(scaled)
        self.cover_preview.setMinimumHeight(scaled.height() + 10)

    # ---------- Pickers ----------
    def pick_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose Audio", "", "Audio (*.mp3 *.wav *.ogg *.flac)")
        if not path: return
        self.audio_path = Path(path)
        self.audio_label.setText(self.audio_path.name)
        self.audio_label.setStyleSheet("color: palette(text); font-weight: bold;")

        if (not self._title_user_edited) and (not self.title_edit.text().strip()):
            self.title_edit.setText(self.audio_path.stem)

        self.statusBar().showMessage(f"Selected: {self.audio_path.name}")
        self._update_state()

    def clear_audio(self) -> None:
        self.audio_path = None
        self.audio_label.setText("No file selected")
        self.audio_label.setStyleSheet("color: palette(disabled-text); font-style: italic;")
        self._update_state()

    def pick_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose Art", "", "Images (*.png *.jpg *.jpeg)")
        if not path: return
        self.cover_path = Path(path)
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
        # Cross-platform open
        proc = QProcess(self)
        if sys.platform == "darwin":
            proc.start("open", [str(p)])
        elif sys.platform == "win32":
            proc.start("explorer", [str(p)])
        else:
            proc.start("xdg-open", [str(p)])

    # ---------- Execution ----------
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

        if is_frozen():
            cmd = [str(py_exec), "--internal-cli"]
        else:
            cmd = [str(py_exec), "-m", "charter.cli"]

        cmd.extend([
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
        ])
        if cfg.fetch_metadata:
            cmd.append("--fetch-metadata")

        self.log_view.clear()
        if not self.grp_logs.isVisible():
            self.btn_toggle_log.setChecked(True)

        self.append_log(f"Starting generation for: {cfg.title}...")
        self.btn_generate.setText("Generating...")

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.SeparateChannels)
        if not is_frozen():
            self.proc.setWorkingDirectory(str(repo_root()))

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
            except Exception as e:
                self.append_log(f"Cover copy failed: {e}")

        # Update preview if we fetched one
        gen_cover = out_song / "album.png"
        if gen_cover.exists():
            self.update_cover_preview(gen_cover)

        if ok:
            QMessageBox.information(self, "Success", f"Chart created!\n\nLocation:\n{out_song}")
            self.statusBar().showMessage("Generation Complete")
        else:
            QMessageBox.critical(self, "Failed", f"Process exited with code {code}. See logs.")
            self.statusBar().showMessage("Generation Failed")

        self.proc = None
        self._update_state()

def main() -> None:
    app = QApplication(sys.argv)
    # Default to system font
    font = QApplication.font()
    font.setPointSize(10)
    app.setFont(font)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
