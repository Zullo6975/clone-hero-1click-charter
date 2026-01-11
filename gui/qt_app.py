from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QProcess, QSettings, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (QAction, QColor, QDesktopServices, QDragEnterEvent, QDropEvent, QFont,
                           QFontDatabase, QPalette, QPixmap, QPainter,
                           QPainterPath, QPen, QLinearGradient)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup,
                               QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                               QDoubleSpinBox, QFileDialog, QFormLayout,
                               QFrame, QGroupBox, QHBoxLayout, QHeaderView,
                               QInputDialog, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMainWindow, QMessageBox,
                               QProgressBar, QPushButton, QRadioButton,
                               QScrollArea, QSizePolicy, QSlider, QSpinBox,
                               QSplitter, QStyle, QTableWidget,
                               QTableWidgetItem, QTextEdit, QToolButton,
                               QVBoxLayout, QWidget, QTabWidget)

# Import constants
from charter.config import SUPPORT_EMAIL, VENMO_URL, REPO_URL


# ---------------- Paths & Config ----------------
def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)

def repo_root() -> Path:
    if is_frozen(): return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]

def get_python_exec() -> str | Path:
    if is_frozen(): return sys.executable
    return repo_root() / ".venv" / "bin" / "python"

def form_label(text: str, required: bool = False, align=Qt.AlignRight | Qt.AlignVCenter) -> QLabel:
    txt = f"{text} <span style='color:#ff4444;'>*</span>" if required else text
    lbl = QLabel(txt)
    lbl.setAlignment(align)
    lbl.setMinimumWidth(110)
    return lbl

def get_font(size: int = 11, bold: bool = False) -> QFont:
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

# --- PRESETS MANAGEMENT ---
DEFAULT_PRESETS: dict[str, dict[str, float | int]] = {
    "1) Casual": {
        "max_nps": 9.0, "min_gap_ms": 75, "sustain": 40, "chord": 15,
        "hard_gap": 150, "med_gap": 350, "easy_gap": 600
    },
    "2) Standard": {
        "max_nps": 13.0, "min_gap_ms": 55, "sustain": 25, "chord": 22,
        "hard_gap": 120, "med_gap": 220, "easy_gap": 450
    },
    "3) Shred": {
        "max_nps": 17.0, "min_gap_ms": 35, "sustain": 10, "chord": 30,
        "hard_gap": 90, "med_gap": 180, "easy_gap": 350
    },
    "4) Lose Fingerprints": {
        "max_nps": 22.0, "min_gap_ms": 25, "sustain": 5,  "chord": 40,
        "hard_gap": 60, "med_gap": 120, "easy_gap": 250
    },
}

def get_user_preset_path() -> Path:
    p = Path.home() / ".1clickcharter" / "presets.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def load_all_presets() -> dict[str, dict[str, float | int]]:
    merged = DEFAULT_PRESETS.copy()
    user_path = get_user_preset_path()
    if user_path.exists():
        try:
            user_data = json.loads(user_path.read_text(encoding="utf-8"))
            merged.update(user_data)
        except Exception:
            pass # Ignore corrupted file
    return merged

def save_user_preset(name: str, data: dict[str, float | int]) -> None:
    user_path = get_user_preset_path()
    current = {}
    if user_path.exists():
        try:
            current = json.loads(user_path.read_text(encoding="utf-8"))
        except Exception:
            current = {}

    current[name] = data
    user_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

def delete_user_preset(name: str) -> None:
    user_path = get_user_preset_path()
    if not user_path.exists(): return

    try:
        current = json.loads(user_path.read_text(encoding="utf-8"))
        if name in current:
            del current[name]
            user_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    except Exception:
        pass

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

    charter: str = "Zullo7569"
    fetch_metadata: bool = True

# ---------------- Theme ----------------
class ThemeManager:
    @staticmethod
    def apply_style(app: QApplication, dark_mode: bool):
        app.setStyle("Fusion")

        font = QFont()
        font.setPointSize(11)
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

            palette.setColor(QPalette.Light, QColor(60, 65, 70))
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 100, 100))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 100, 100))
            palette.setColor(QPalette.PlaceholderText, QColor(120, 130, 140))

        else:
            # Light Theme
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

            palette.setColor(QPalette.Light, QColor(255, 255, 255))
            palette.setColor(QPalette.Midlight, QColor(230, 230, 240))
            palette.setColor(QPalette.Dark, QColor(200, 200, 210))
            palette.setColor(QPalette.Mid, QColor(210, 210, 220))
            palette.setColor(QPalette.Shadow, QColor(150, 150, 160))

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
                font-size: 12pt;
                max-width: 550px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }

            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QListWidget {
                padding: 5px;
                border-radius: 4px;
                border: 1px solid palette(mid);
                background-color: palette(base);
                color: palette(text);
                min-height: 18px;
                max-width: 425px;
                font-size: 11pt;
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

            /* STANDARD BUTTONS - SCALED DOWN */
            QPushButton {
                padding: 5px 10px;
                border-radius: 5px;
                border: 1px solid palette(mid);
                background-color: palette(button);
                color: palette(text);
                font-size: 11pt; /* Slightly smaller font */
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

            /* PRIMARY BUTTON (GENERATE) */
            QPushButton#Primary {
                padding: 6px 12px;
                border-radius: 5px;
                border: 1px solid palette(mid);
                background-color: palette(button);
                color: palette(text);
                font-size: 11pt; /* Slightly smaller font */
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

            QCheckBox { spacing: 8px; }

            /* STATUS BAR */
            QStatusBar {
                background: palette(window);
                border-top: 1px solid palette(mid);
                min-height: 50px;
                max-height: 50px;
            }
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

            /* POPUPS: Explicit 500px width */
            QMessageBox {
                min-width: 500px;
            }
            QMessageBox QLabel {
                min-width: 500px;
            }

            /* TABS */
            QTabWidget::pane {
                border: 1px solid palette(mid);
                border-radius: 4px;
                top: -1px;
            }
            QTabBar::tab {
                background: palette(button);
                border: 1px solid palette(mid);
                border-bottom-color: palette(mid);
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: palette(base);
                border-bottom-color: palette(base);
                font-weight: bold;
            }
        """)

# ---------------- Log Window ----------------
class LogWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logs")
        self.resize(700, 350)
        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMinimumSize(700, 350)

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

# ---------------- Density Visualizer ----------------
class DensityGraphWidget(QWidget):
    def __init__(self, density_data: list[dict], sections: list[dict], parent=None):
        super().__init__(parent)
        self._density = density_data
        self._sections = sections
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background-color: #2b2b2b; border: 1px solid #3d3d3d; border-radius: 4px;")

    def set_sections(self, sections: list[dict]):
        self._sections = sections
        self.update() # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill Background
        painter.fillRect(self.rect(), QColor(43, 43, 43))

        w = self.width()
        h = self.height()

        if not self._density:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Density Data")
            return

        # Determine Scaling
        max_t = self._density[-1]['t']
        if max_t <= 0: max_t = 1.0

        max_nps = 0.0
        for d in self._density:
            if d['nps'] > max_nps: max_nps = d['nps']
        if max_nps < 5.0: max_nps = 5.0 # Minimum ceiling for visualization

        # Margins
        margin_b = 20
        plot_h = h - margin_b

        # 1. Draw Density Path
        path = QPainterPath()
        path.moveTo(0, plot_h) # Start bottom-left

        for d in self._density:
            x = (d['t'] / max_t) * w
            # nps relative to max, inverted Y
            ratio = d['nps'] / max_nps
            y = plot_h - (ratio * plot_h)
            path.lineTo(x, y)

        path.lineTo(w, plot_h) # Finish bottom-right
        path.closeSubpath()

        # Gradient Fill
        grad = QLinearGradient(0, 0, 0, plot_h)
        grad.setColorAt(0.0, QColor(0, 180, 255, 120))
        grad.setColorAt(1.0, QColor(0, 180, 255, 10))
        painter.fillPath(path, grad)

        # Line Stroke (Redraw line without closing loop)
        painter.setPen(QPen(QColor(0, 200, 255), 2))
        line_path = QPainterPath()
        first = True
        for d in self._density:
            x = (d['t'] / max_t) * w
            ratio = d['nps'] / max_nps
            y = plot_h - (ratio * plot_h)
            if first:
                line_path.moveTo(x, y)
                first = False
            else:
                line_path.lineTo(x, y)
        painter.drawPath(line_path)

        # 2. Draw Section Lines & Names
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1, Qt.DashLine))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)

        for i, s in enumerate(self._sections):
            t = s.get('start', 0.0)
            if t > max_t: continue

            x = (t / max_t) * w
            painter.drawLine(int(x), 0, int(x), h)

            name = s.get('name', '')
            # Stagger text height to prevent overlap
            text_y = h - 6 if i % 2 == 0 else h - 18

            # Text shadow for readability
            painter.setPen(QColor(0,0,0, 180))
            painter.drawText(int(x) + 5, text_y + 1, name)

            painter.setPen(QColor(220, 220, 220))
            painter.drawText(int(x) + 4, text_y, name)

            # Reset pen for next line
            painter.setPen(QPen(QColor(255, 255, 255, 120), 1, Qt.DashLine))

# ---------------- Review Dialog ----------------
class SectionReviewDialog(QDialog):
    def __init__(self, sections: list[dict], density_data: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review Sections")
        self.resize(500, 600) # Increased width for graph
        self.sections = sections

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 1. Density Graph
        lbl_graph = QLabel("Note Density & Structure")
        lbl_graph.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_graph)

        self.graph = DensityGraphWidget(density_data, sections)
        layout.addWidget(self.graph)

        # 2. Table Header
        lbl = QLabel("Section List (Rename Only)")
        lbl.setStyleSheet("color: palette(text); font-weight: bold; margin-top: 10px;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(2) # Time, Name
        self.table.setHorizontalHeaderLabels(["Start Time (s)", "Section Name"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)

        self.refresh_table()
        layout.addWidget(self.table)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def refresh_table(self):
        self.table.setRowCount(len(self.sections))

        for i, s in enumerate(self.sections):
            # 1. TIME (Read Only)
            t_val = float(s.get('start', 0.0))
            t_item = QTableWidgetItem(f"{t_val:.2f}")
            t_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            t_item.setTextAlignment(Qt.AlignCenter)

            # 2. NAME EDIT
            le = QLineEdit(str(s.get('name', '')))
            le.setPlaceholderText("Section Name")
            le.setClearButtonEnabled(True)
            le.textChanged.connect(lambda txt, idx=i: self.on_name_changed(idx, txt))

            self.table.setItem(i, 0, t_item)
            self.table.setCellWidget(i, 1, le)

    def on_name_changed(self, row: int, new_name: str):
        if 0 <= row < len(self.sections):
            self.sections[row]['name'] = new_name
            # Update the graph labels in real-time
            self.graph.set_sections(self.sections)

    def get_sections(self) -> list[dict]:
        return self.sections

# ---------------- Support Dialog ----------------
class SupportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help & Support")
        self.resize(400, 320)

        layout = QVBoxLayout(self)

        # Tabs for separation of concerns
        tabs = QTabWidget()
        tabs.addTab(self._build_help_tab(), "Tech Support")
        tabs.addTab(self._build_donate_tab(), "Support Development")

        layout.addWidget(tabs)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close, 0, Qt.AlignRight)

    def _build_help_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(15)
        lay.setContentsMargins(20, 30, 20, 20)

        lbl = QLabel("Having trouble with a chart? Found a bug?")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 11pt; font-weight: bold;")
        lbl.setAlignment(Qt.AlignCenter)

        sub = QLabel("We're happy to help. Please check the docs or send us a message.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color: palette(disabled-text);")
        sub.setAlignment(Qt.AlignCenter)

        btn_email = QPushButton("📧 Email Support")
        btn_email.setCursor(Qt.PointingHandCursor)
        btn_email.setMinimumHeight(40)
        btn_email.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"mailto:{SUPPORT_EMAIL}")))

        btn_issue = QPushButton("🐞 Report on GitHub")
        btn_issue.setCursor(Qt.PointingHandCursor)
        btn_issue.setMinimumHeight(40)
        btn_issue.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"{REPO_URL}/issues")))

        lay.addStretch()
        lay.addWidget(lbl)
        lay.addWidget(sub)
        lay.addStretch()
        lay.addWidget(btn_email)
        lay.addWidget(btn_issue)
        lay.addStretch()
        return w

    def _build_donate_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(15)
        lay.setContentsMargins(20, 30, 20, 20)

        lbl = QLabel("Enjoying 1-Click Charter?")
        lbl.setStyleSheet("font-size: 12pt; font-weight: bold;")
        lbl.setAlignment(Qt.AlignCenter)

        txt = QLabel(
            "This tool is free and open source. If it saved you time, "
            "consider buying me a coffee to keep the development going!"
        )
        txt.setWordWrap(True)
        txt.setAlignment(Qt.AlignCenter)
        txt.setStyleSheet("line-height: 1.4;")

        btn_venmo = QPushButton("💙 Tip with Venmo")
        btn_venmo.setCursor(Qt.PointingHandCursor)
        btn_venmo.setMinimumHeight(45)
        # Venmo Brand Colors
        btn_venmo.setStyleSheet("""
            QPushButton {
                background-color: #008CFF;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0074D4;
            }
        """)
        btn_venmo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(VENMO_URL)))

        lay.addStretch()
        lay.addWidget(lbl)
        lay.addWidget(txt)
        lay.addStretch()
        lay.addWidget(btn_venmo)
        lay.addStretch()

        return w

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

        # STATE
        self.song_queue: list[Path] = []
        self._is_analyzing = False
        self._pending_generation_cfg: RunConfig | None = None
        self._pending_generation_out: Path | None = None

        self.log_window = LogWindow()
        self.dark_mode = self.settings.value("dark_mode", True, type=bool)
        self._title_user_edited = False

        self._build_ui()
        self._wire()
        self._restore_settings()

        ThemeManager.apply_style(QApplication.instance(), self.dark_mode)

        # Load Presets
        self.refresh_presets()
        last_preset = self.settings.value("preset", "Standard", type=str)

        # Fallback if old "Medium" preset is cached
        if last_preset not in self.all_presets:
            last_preset = "2) Standard"

        self.preset_combo.setCurrentText(last_preset)
        self.apply_preset(self.preset_combo.currentText())
        self._update_queue_display()

        self._update_state()
        QTimer.singleShot(100, self.snap_to_content)
        self.status_label.setText("Ready")

    def closeEvent(self, event) -> None:
        self.log_window.close()
        self.settings.setValue("dark_mode", self.chk_dark.isChecked())
        c_val = self.charter_edit.text().strip() or "Zullo7569"
        self.settings.setValue("charter", c_val)
        self.settings.setValue("out_dir", self.out_dir_edit.text())
        self.settings.setValue("preset", self.preset_combo.currentText())
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)

    def show_support_dialog(self) -> None:
        dlg = SupportDialog(self)
        dlg.exec()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # --- HEADER ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.setSpacing(16)
        header_layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel()
        icon_path = repo_root() / "icons" / "icon_og.png"
        if icon_path.exists():
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                pix = pix.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_lbl.setPixmap(pix)

        title_lbl = QLabel("CloneHero 1-Click Charter")
        title_lbl.setFont(get_font(32, True))
        title_lbl.setStyleSheet("color: palette(text);")

        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        main_layout.addWidget(header_widget)

        # --- BODY ---
        line = QFrame()
        line.setFixedHeight(1)
        line.setFixedWidth(750)
        line.setStyleSheet("background-color: rgba(0, 0, 0, 0.12);")
        main_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignHCenter)

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
        sidebar_layout.setContentsMargins(0, 0, 16, 0)
        sidebar_layout.setSpacing(20)

        # Audio Input Group
        grp_audio = QGroupBox("Input Audio (REQUIRED)")
        grp_audio_layout = QVBoxLayout(grp_audio)
        self.audio_label = QLabel("Drag Audio Files Here")
        self.audio_label.setAlignment(Qt.AlignCenter)
        self.audio_label.setWordWrap(True)
        self.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text); font-size: 11pt;")

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
        queue_layout.setContentsMargins(10, 10, 10, 10)
        queue_layout.setSpacing(10)

        self.queue_list = QListWidget()
        self.queue_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.queue_list.setMaximumHeight(60)
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
        self.cover_preview.setFixedSize(280, 280)
        self.cover_preview.setStyleSheet("border: 2px dashed palette(mid); border-radius: 6px; color: palette(disabled-text); font-style: italic; font-size: 11pt;")

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
        self.main_widget.setMinimumWidth(700)

        main_layout_inner = QVBoxLayout(self.main_widget)
        main_layout_inner.setContentsMargins(16, 0, 0, 0)
        main_layout_inner.setSpacing(24)

        # Metadata
        grp_meta = QGroupBox("Song Metadata")
        form_meta = QFormLayout(grp_meta)
        form_meta.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_meta.setLabelAlignment(Qt.AlignVCenter)
        form_meta.setVerticalSpacing(14)

        self.title_edit = QLineEdit()
        self.title_edit.setAlignment(Qt.AlignLeft)
        self.artist_edit = QLineEdit()
        self.artist_edit.setAlignment(Qt.AlignLeft)
        self.album_edit = QLineEdit()
        self.album_edit.setAlignment(Qt.AlignLeft)
        self.genre_edit = QLineEdit()
        self.genre_edit.setAlignment(Qt.AlignLeft)
        self.genre_edit.setPlaceholderText("Default: Rock")
        self.charter_edit = QLineEdit()
        self.charter_edit.setAlignment(Qt.AlignLeft)
        self.charter_edit.setPlaceholderText("Default: Zullo7569")

        self.btn_clear_meta = QToolButton()
        self.btn_clear_meta.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_clear_meta.setToolTip("Clear all metadata fields")
        self.btn_clear_meta.setCursor(Qt.PointingHandCursor)

        form_meta.addRow(form_label("Title", required=True, align=Qt.AlignCenter), self.title_edit)
        form_meta.addRow(form_label("Artist", required=True, align=Qt.AlignCenter), self.artist_edit)
        form_meta.addRow(form_label("Album", align=Qt.AlignCenter), self.album_edit)
        form_meta.addRow(form_label("Genre", align=Qt.AlignCenter), self.genre_edit)
        form_meta.addRow(form_label("Charter", align=Qt.AlignCenter), self.charter_edit)

        row_clear = QHBoxLayout()
        row_clear.addStretch()
        row_clear.addWidget(QLabel("Clear Fields "))
        row_clear.addWidget(self.btn_clear_meta)
        form_meta.addRow("", row_clear)

        main_layout_inner.addWidget(grp_meta)

        # Configuration
        self.adv_container = QGroupBox("Chart Settings")
        adv_layout = QVBoxLayout(self.adv_container)

        self.chk_adv = QCheckBox("Show Tuning Controls")
        self.chk_adv.setStyleSheet("font-weight: bold; margin-bottom: 6px;")
        self.chk_adv.setCursor(Qt.PointingHandCursor)

        self.adv_content = QWidget()
        self.adv_content.setVisible(False)
        # Use VBox for the main container to allow mixing widgets (Presets) and Tabs
        adv_inner_layout = QVBoxLayout(self.adv_content)
        adv_inner_layout.setContentsMargins(0, 0, 0, 0)
        adv_inner_layout.setSpacing(12)

        # 1. PRESETS ROW (Global)
        preset_row_widget = QWidget()
        preset_layout = QHBoxLayout(preset_row_widget)
        preset_layout.setContentsMargins(0, 0, 0, 0)

        lbl_preset = QLabel("Expert Style:")
        lbl_preset.setMinimumWidth(100)
        lbl_preset.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.preset_combo = SafeComboBox()
        self.preset_combo.setCursor(Qt.PointingHandCursor)
        self.preset_combo.setMinimumWidth(200)

        self.btn_save_preset = QToolButton()
        self.btn_save_preset.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.btn_save_preset.setToolTip("Save current settings as a new preset")
        self.btn_save_preset.setCursor(Qt.PointingHandCursor)

        self.btn_del_preset = QToolButton()
        self.btn_del_preset.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_del_preset.setToolTip("Delete selected preset (User presets only)")
        self.btn_del_preset.setCursor(Qt.PointingHandCursor)

        preset_layout.addWidget(lbl_preset)
        preset_layout.addWidget(self.preset_combo, 1)
        preset_layout.addWidget(self.btn_save_preset)
        preset_layout.addWidget(self.btn_del_preset)

        adv_inner_layout.addWidget(preset_row_widget)

        self.preset_hint = QLabel("Select baseline intensity.")
        self.preset_hint.setStyleSheet("color: palette(disabled-text); font-size: 11pt; margin-left: 110px;")
        adv_inner_layout.addWidget(self.preset_hint)

        self.chk_review = QCheckBox("Review Sections before Generation")
        self.chk_review.setToolTip("Show a list of detected sections to rename/edit before creating the chart.")
        self.chk_review.setCursor(Qt.PointingHandCursor)
        # Right align the review checkbox slightly
        row_review = QHBoxLayout()
        row_review.addSpacing(110)
        row_review.addWidget(self.chk_review)
        adv_inner_layout.addLayout(row_review)

        # 2. TABS
        self.tabs_config = QTabWidget()

        # --- TAB 1: EXPERT BASELINE ---
        tab_expert = QWidget()
        form_expert = QFormLayout(tab_expert)
        form_expert.setLabelAlignment(Qt.AlignRight)

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
        self.max_nps_spin.setRange(1.0, 30.0)
        self.max_nps_spin.setSingleStep(0.1)
        self.max_nps_spin.setSuffix(" NPS")
        self.max_nps_spin.setMinimumHeight(26)

        self.min_gap_spin = SafeSpinBox()
        self.min_gap_spin.setRange(10, 1000)
        self.min_gap_spin.setSingleStep(10)
        self.min_gap_spin.setSuffix(" ms")
        self.min_gap_spin.setMinimumHeight(26)

        self.seed_spin = SafeSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setMinimumHeight(26)
        self.seed_spin.setToolTip("Seed for random generation.")

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

        self.sustain_gap_spin = SafeDoubleSpinBox()
        self.sustain_gap_spin.setRange(0.1, 2.0)
        self.sustain_gap_spin.setSingleStep(0.1)
        self.sustain_gap_spin.setValue(0.2)
        self.sustain_gap_spin.setSuffix(" s")

        self.sustain_buffer_spin = SafeDoubleSpinBox()
        self.sustain_buffer_spin.setRange(0.05, 0.5)
        self.sustain_buffer_spin.setSingleStep(0.05)
        self.sustain_buffer_spin.setValue(0.15)
        self.sustain_buffer_spin.setSuffix(" s")

        form_expert.addRow(form_label("Generation Mode"), row_mode)
        form_expert.addRow(form_label("Max Notes/Sec"), self.max_nps_spin)
        form_expert.addRow(form_label("Min Note Spacing"), self.min_gap_spin)
        form_expert.addRow(form_label("Pattern Variation"), self.seed_spin)

        div3 = QFrame()
        div3.setFrameShape(QFrame.HLine)
        div3.setStyleSheet("color: palette(mid);")
        form_expert.addRow(div3)

        form_expert.addRow(form_label("Chord Density"), self.chord_slider)
        form_expert.addRow(form_label("Sustain Prob."), self.sustain_slider)
        form_expert.addRow(form_label("Min Gap for Sustain"), self.sustain_gap_spin)
        form_expert.addRow(form_label("Sustain End Buffer"), self.sustain_buffer_spin)

        self.tabs_config.addTab(tab_expert, "Expert Baseline")

        # --- TAB 2: DIFFICULTY SCALING ---
        tab_scaling = QWidget()
        lay_scaling = QVBoxLayout(tab_scaling)

        lbl_info = QLabel("Lower difficulties are created by filtering the Expert chart. "
                          "Increasing the 'Gap' removes more notes, making it easier.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: palette(disabled-text); font-style: italic; margin-bottom: 10px;")
        lay_scaling.addWidget(lbl_info)

        form_scaling = QFormLayout()
        form_scaling.setLabelAlignment(Qt.AlignRight)

        self.spin_hard_gap = SafeSpinBox()
        self.spin_hard_gap.setRange(50, 500)
        self.spin_hard_gap.setValue(120)
        self.spin_hard_gap.setSuffix(" ms")
        self.spin_hard_gap.setToolTip("Minimum gap for HARD difficulty")
        self.spin_hard_gap.valueChanged.connect(self._update_scaling_labels)

        self.lbl_hard_desc = QLabel()
        self.lbl_hard_desc.setStyleSheet("color: palette(disabled-text);")

        self.spin_med_gap = SafeSpinBox()
        self.spin_med_gap.setRange(100, 800)
        self.spin_med_gap.setValue(220)
        self.spin_med_gap.setSuffix(" ms")
        self.spin_med_gap.setToolTip("Minimum gap for MEDIUM difficulty")
        self.spin_med_gap.valueChanged.connect(self._update_scaling_labels)

        self.lbl_med_desc = QLabel()
        self.lbl_med_desc.setStyleSheet("color: palette(disabled-text);")

        self.spin_easy_gap = SafeSpinBox()
        self.spin_easy_gap.setRange(200, 1500)
        self.spin_easy_gap.setValue(450)
        self.spin_easy_gap.setSuffix(" ms")
        self.spin_easy_gap.setToolTip("Minimum gap for EASY difficulty")
        self.spin_easy_gap.valueChanged.connect(self._update_scaling_labels)

        self.lbl_easy_desc = QLabel()
        self.lbl_easy_desc.setStyleSheet("color: palette(disabled-text);")

        # Side-by-side Layouts
        row_h = QHBoxLayout()
        row_h.addWidget(self.spin_hard_gap)
        row_h.addWidget(self.lbl_hard_desc)
        form_scaling.addRow(form_label("Hard Gap"), row_h)

        row_m = QHBoxLayout()
        row_m.addWidget(self.spin_med_gap)
        row_m.addWidget(self.lbl_med_desc)
        form_scaling.addRow(form_label("Medium Gap"), row_m)

        row_e = QHBoxLayout()
        row_e.addWidget(self.spin_easy_gap)
        row_e.addWidget(self.lbl_easy_desc)
        form_scaling.addRow(form_label("Easy Gap"), row_e)

        lay_scaling.addLayout(form_scaling)
        lay_scaling.addStretch()

        self.tabs_config.addTab(tab_scaling, "Difficulty Scaling")

        adv_inner_layout.addWidget(self.tabs_config)

        adv_layout.addWidget(self.chk_adv)
        adv_layout.addWidget(self.adv_content)
        main_layout_inner.addWidget(self.adv_container)

        # Output (Left Aligned Buttons)
        grp_out = QGroupBox("Output Destination")
        out_container_layout = QVBoxLayout(grp_out)

        out_row1 = QHBoxLayout()
        self.out_dir_edit = QLineEdit("")
        self.out_dir_edit.setPlaceholderText("Select output folder...")

        self.btn_pick_output = QPushButton("Browse...")
        self.btn_pick_output.setCursor(Qt.PointingHandCursor)

        self.btn_clear_out = QToolButton()
        self.btn_clear_out.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_clear_out.setToolTip("Clear output path")
        self.btn_clear_out.setCursor(Qt.PointingHandCursor)
        self.btn_clear_out.setMinimumHeight(26)

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
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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

        self.btn_support = QPushButton("Support")
        self.btn_support.setCursor(Qt.PointingHandCursor)
        self.btn_support.clicked.connect(self.show_support_dialog)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("FooterBtn")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)

        # ---------------- STATUS BAR WIDGETS ----------------
        # Container for Left side of status bar (Label + Progress)
        self.status_container = QWidget()
        self.status_layout = QHBoxLayout(self.status_container)
        self.status_layout.setContentsMargins(27, 0, 0, 0)
        self.status_layout.setSpacing(15)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: palette(text); font-weight: bold;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(12)

        self.status_layout.addWidget(self.status_label)
        self.status_layout.addWidget(self.progress_bar)
        self.status_layout.addStretch()

        self.statusBar().addWidget(self.status_container, 1)

        self.btn_generate = QPushButton("  GENERATE  ")
        self.btn_generate.setObjectName("Primary")
        self.btn_generate.setCursor(Qt.PointingHandCursor)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: palette(mid);")

        footer_layout.addWidget(self.chk_dark)
        footer_layout.addWidget(self.btn_show_logs)
        footer_layout.addWidget(self.btn_help)
        footer_layout.addWidget(self.btn_support)
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
        self.btn_save_preset.clicked.connect(self.on_save_preset)
        self.btn_del_preset.clicked.connect(self.on_delete_preset)

        self.chk_adv.toggled.connect(self.on_toggle_advanced)

        for w in [self.out_dir_edit, self.title_edit, self.artist_edit]:
            w.textChanged.connect(self._update_state)

    def snap_to_content(self) -> None:
        if self.centralWidget():
            self.centralWidget().layout().activate()
        h = self.sidebar_widget.sizeHint().height()
        h = max(h, 600)
        w = 310 + 625 + 40
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
        geom = self.settings.value("geometry")
        if geom: self.restoreGeometry(geom)

    # --- Preset Logic ---
    def refresh_presets(self) -> None:
        current = self.preset_combo.currentText()
        self.all_presets = load_all_presets()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        defaults = sorted(list(DEFAULT_PRESETS.keys()))
        others = sorted([k for k in self.all_presets.keys() if k not in DEFAULT_PRESETS])

        self.preset_combo.addItems(defaults + others)
        self.preset_combo.addItem("Custom…")

        # Fallback Logic
        if current in self.all_presets:
            self.preset_combo.setCurrentText(current)
        else:
            self.preset_combo.setCurrentText("2) Standard")
        self.preset_combo.blockSignals(False)

        is_default = self.preset_combo.currentText() in DEFAULT_PRESETS
        self.btn_del_preset.setEnabled(not is_default and self.preset_combo.currentText() != "Custom…")

    def on_save_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")
        if ok and name.strip():
            name = name.strip()
            data = {
                "max_nps": self.max_nps_spin.value(),
                "min_gap_ms": self.min_gap_spin.value(),
                "sustain": self.sustain_slider.value(),
                "chord": self.chord_slider.value(),
                # NEW: Save scaling values too
                "hard_gap": self.spin_hard_gap.value(),
                "med_gap": self.spin_med_gap.value(),
                "easy_gap": self.spin_easy_gap.value()
            }
            save_user_preset(name, data)
            self.refresh_presets()
            self.preset_combo.setCurrentText(name)
            self.statusBar().showMessage(f"Saved preset: {name}")

    def on_delete_preset(self) -> None:
        name = self.preset_combo.currentText()
        if name in DEFAULT_PRESETS:
            return

        ret = QMessageBox.question(self, "Delete Preset", f"Are you sure you want to delete '{name}'?")
        if ret == QMessageBox.Yes:
            delete_user_preset(name)
            self.refresh_presets()
            self.statusBar().showMessage(f"Deleted preset: {name}")

    def apply_preset(self, name: str) -> None:
        preset = self.all_presets.get(name)
        is_custom = preset is None

        if is_custom:
            self.preset_hint.setText("Manual control enabled.")
        else:
            # Expert Settings
            self.max_nps_spin.setValue(float(preset["max_nps"]))
            self.min_gap_spin.setValue(int(preset["min_gap_ms"]))
            self.sustain_slider.setValue(int(preset["sustain"]))
            self.chord_slider.setValue(int(preset["chord"]))

            # Difficulty Scaling Settings
            self.spin_hard_gap.setValue(int(preset.get("hard_gap", 120)))
            self.spin_med_gap.setValue(int(preset.get("med_gap", 220)))
            self.spin_easy_gap.setValue(int(preset.get("easy_gap", 450)))

            self.preset_hint.setText(f"Active: {preset['max_nps']} NPS | Med Gap: {preset.get('med_gap', 220)}ms")

        is_default = name in DEFAULT_PRESETS
        self.btn_del_preset.setEnabled(not is_default and name != "Custom…")

        # Trigger label update manually since signals might be blocked or not fired
        self._update_scaling_labels()

    def _update_scaling_labels(self):
        # Hard
        h_ms = self.spin_hard_gap.value()
        h_nps = 1000.0 / h_ms if h_ms > 0 else 0
        self.lbl_hard_desc.setText(f"(Max ~{h_nps:.1f} notes/sec)")

        # Med
        m_ms = self.spin_med_gap.value()
        m_nps = 1000.0 / m_ms if m_ms > 0 else 0
        self.lbl_med_desc.setText(f"(Max ~{m_nps:.1f} notes/sec)")

        # Easy
        e_ms = self.spin_easy_gap.value()
        e_nps = 1000.0 / e_ms if e_ms > 0 else 0
        self.lbl_easy_desc.setText(f"(Max ~{e_nps:.1f} notes/sec)")

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
        self.status_label.setText(f"Loaded: {self.audio_path.name}")
        self._update_state()
        QTimer.singleShot(0, self.snap_to_content)

    def clear_audio(self) -> None:
        self.clear_song_info()
        if self.song_queue:
            next_song = self.song_queue.pop(0)
            self._update_queue_display()
            self.load_audio(next_song)
            self.status_label.setText(f"Queue: Loaded {next_song.name}")
        else:
            self.audio_path = None
            self.audio_label.setText("Drag Audio Files Here")
            self.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text); font-size: 11pt;")
            self._update_state()
            self.audio_label.adjustSize()
            self.status_label.setText("Audio cleared")
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

            # HARDCODED PRO DEFAULTS (UI Widgets Removed)
            allow_orange=True,
            rhythmic_glue=True,
            grid_snap="1/16",

            chord_prob=self.chord_slider.value() / 100.0,
            sustain_len=self.sustain_slider.value() / 100.0,
            sustain_threshold=float(self.sustain_gap_spin.value()),
            sustain_buffer=float(self.sustain_buffer_spin.value()),

            # Scaling
            hard_gap_ms=int(self.spin_hard_gap.value()),
            med_gap_ms=int(self.spin_med_gap.value()),
            easy_gap_ms=int(self.spin_easy_gap.value()),

            fetch_metadata=True
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

        self._pending_generation_cfg = cfg
        self._pending_generation_out = out_song

        # Determine if we should analyze first
        if self.chk_review.isChecked():
            self._is_analyzing = True
            label = "Generating...."
            extra_args = ["--analyze-only"]
        else:
            self._is_analyzing = False
            label = "Generating...."
            extra_args = []

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
            # NO grid-snap arg
            "--sustain-threshold", str(cfg.sustain_threshold),
            "--sustain-buffer", str(cfg.sustain_buffer),

            # New Scaling Args
            "--hard-gap-ms", str(cfg.hard_gap_ms),
            "--med-gap-ms", str(cfg.med_gap_ms),
            "--easy-gap-ms", str(cfg.easy_gap_ms)
        ])

        # CLEANUP: No flags for orange/glue needed (defaults are true)

        if cfg.fetch_metadata: cmd.append("--fetch-metadata")

        cmd.extend(extra_args)

        self.log_window.clear()
        if self._is_analyzing:
            self.append_log(f"Starting analysis for: {cfg.title}...")
        else:
            self.append_log(f"Starting generation for: {cfg.title}...")

        self.status_label.setText("")
        self.btn_generate.setText(label)
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
        ok = (status == QProcess.NormalExit) and (code == 0)

        if not ok:
            self.btn_generate.setText("  GENERATE  ")
            self.progress_bar.setVisible(False)
            reason = "Unknown error."
            logs = self.log_window.get_text()
            for line in reversed(logs.splitlines()):
                if "Error" in line or "Exception" in line:
                    reason = line.strip()
                    break
            QMessageBox.critical(self, "Process Failed", f"Failed.\n\nReason: {reason}\n\nCheck logs for full details.")
            self.status_label.setText("Failed")
            self.proc = None
            self._update_state()
            return

        if self._is_analyzing:
            self._is_analyzing = False
            json_path = out_song / "sections.json"
            if json_path.exists():
                try:
                    data = json.loads(json_path.read_text(encoding='utf-8'))
                    sections = data.get("sections", [])
                    density = data.get("density", [])

                    dlg = SectionReviewDialog(sections, density, self)
                    if dlg.exec():
                        overrides = dlg.get_sections()
                        override_path = out_song / "overrides.json"
                        override_path.write_text(json.dumps(overrides, indent=2))
                        self.run_generation_phase2(override_path)
                    else:
                        self.btn_generate.setText("  GENERATE  ")
                        self.progress_bar.setVisible(False)
                        self.status_label.setText("Cancelled")
                        self.proc = None
                        self._update_state()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to parse analysis data: {e}")
                    self.btn_generate.setText("  GENERATE  ")
                    self.progress_bar.setVisible(False)
                    self.proc = None
                    self._update_state()
            else:
                QMessageBox.critical(self, "Error", "Analysis finished but sections.json was not found.")
                self.btn_generate.setText("  GENERATE  ")
                self.progress_bar.setVisible(False)
                self.proc = None
                self._update_state()
            return

        self.btn_generate.setText("  GENERATE  ")
        self.progress_bar.setVisible(False)

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
            self.status_label.setText(f"Chart generated! Loaded next: {next_song.name}")
        else:
            self.clear_song_info()
            self.audio_path = None
            self.audio_label.setText("Drag Audio Files Here")
            self.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text); font-size: 11pt;")
            self._update_state()
            self.status_label.setText("Queue Finished")

        self.proc = None
        self._update_state()

    def run_generation_phase2(self, override_path: Path) -> None:
        cfg = self._pending_generation_cfg
        out_song = self._pending_generation_out

        if not cfg or not out_song: return

        py_exec = get_python_exec()
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
            # NO grid-snap arg
            "--sustain-threshold", str(cfg.sustain_threshold),
            "--sustain-buffer", str(cfg.sustain_buffer),
            "--section-overrides", str(override_path),

            # New Scaling Args
            "--hard-gap-ms", str(cfg.hard_gap_ms),
            "--med-gap-ms", str(cfg.med_gap_ms),
            "--easy-gap-ms", str(cfg.easy_gap_ms)
        ])

        # Cleanup: No flags for orange/glue

        if cfg.fetch_metadata: cmd.append("--fetch-metadata")

        self.append_log(f"Starting Final Generation (with overrides)...")

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.SeparateChannels)
        if not is_frozen(): self.proc.setWorkingDirectory(str(repo_root()))
        self.proc.readyReadStandardOutput.connect(self._on_stdout)
        self.proc.readyReadStandardError.connect(self._on_stderr)
        self.proc.finished.connect(lambda c, s: self._on_finished(c, s, out_song))
        self.proc.start(cmd[0], cmd[1:])

    def run_health_check(self, song_dir: Path) -> None:
        self.status_label.setText("Validating...")
        QTimer.singleShot(0, self.snap_to_content)
        py_exec = get_python_exec()

        if is_frozen():
            cmd = [str(py_exec), "--internal-cli"]
        else:
            cmd = [str(py_exec), "-m", "charter.cli"]

        cmd.extend(["--validate", str(song_dir)])

        self.validator_proc = QProcess(self)
        self.validator_proc.finished.connect(lambda c, s: self._on_health_finished(c, s, song_dir))
        self.validator_proc.start(cmd[0], cmd[1:])

    def _on_health_finished(self, code: int, status: QProcess.ExitStatus, song_dir: Path) -> None:
        stdout = bytes(self.validator_proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        stderr = bytes(self.validator_proc.readAllStandardError()).decode("utf-8", errors="replace")

        full_output = stdout + stderr

        if not full_output.strip():
            full_output = "[No output from validator process]"

        warnings = []
        for line in full_output.splitlines():
            line = line.strip()
            line_lower = line.lower()
            if line.startswith("- ") or "warning" in line_lower or "error" in line_lower or "traceback" in line_lower:
                warnings.append(line)

        self.append_log("\n--- VALIDATION REPORT ---")
        self.append_log(full_output)

        if not self.song_queue:
            msg = f"Chart generated successfully!\n\nLocation:\n{song_dir}"

            if warnings:
                msg += "\n\nWarnings/Errors:\n" + "\n".join(f"• {w[:80]}" for w in warnings[:5])
                if len(warnings) > 5: msg += "\n... (check logs for more)"

            title = "Generation Complete" if not warnings else "Complete (With Warnings)"
            icon = QMessageBox.Information if not warnings else QMessageBox.Warning

            msg_box = QMessageBox(icon, title, msg, QMessageBox.Ok, self)
            msg_box.setMinimumWidth(500)
            msg_box.exec()

            self.status_label.setText("Ready")

        self.validator_proc = None

def main() -> None:
    if "--internal-cli" in sys.argv:
        sys.argv.remove("--internal-cli")
        from charter import cli
        sys.exit(cli.main())

    app = QApplication(sys.argv)
    font = QApplication.font()
    font.setPointSize(10)
    app.setFont(font)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
