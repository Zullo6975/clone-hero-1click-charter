from __future__ import annotations

from pathlib import Path

from charter.config import REPO_URL, SUPPORT_EMAIL, VENMO_URL
# Imports from other GUI modules
from gui.widgets import DensityGraphWidget, SafeTabWidget
from PySide6.QtCore import QUrl
from PySide6.QtGui import QBrush, QColor, QDesktopServices, Qt
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QDialogButtonBox,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QTabWidget, QVBoxLayout, QWidget)

# Try to import mutagen for metadata reading
try:
    import mutagen  # type: ignore
    from mutagen.easyid3 import EasyID3  # type: ignore
    from mutagen.flac import FLAC  # type: ignore
    from mutagen.oggvorbis import OggVorbis  # type: ignore
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

# ---------------- Batch Entry Dialog (NEW) ----------------
class BatchEntryDialog(QDialog):
    def __init__(self, file_paths: list[Path], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Batch Add: {len(file_paths)} Songs")
        self.resize(900, 500)
        self.files = file_paths
        self.result_data = []

        layout = QVBoxLayout(self)

        lbl = QLabel("Verify Metadata for Batch Processing")
        lbl.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(lbl)

        sub = QLabel("Edit these fields now to ensure your charts are named correctly. Tab to move quickly.")
        sub.setStyleSheet("color: palette(disabled-text); margin-bottom: 5px;")
        layout.addWidget(sub)

        # Table Setup
        self.table = QTableWidget()
        self.columns = ["Filename", "Title", "Artist", "Album", "Genre", "Year", "Charter"]
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setRowCount(len(self.files))

        # Styling
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Pre-fill data
        self._populate_table()
        layout.addWidget(self.table)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Add to Queue")
        btns.accepted.connect(self.collect_data_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate_table(self):
        for r, path in enumerate(self.files):
            # 0. Filename (Read-onlyish, acting as label)
            item_fn = QTableWidgetItem(path.name)
            item_fn.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item_fn.setForeground(QBrush(QColor("gray")))
            self.table.setItem(r, 0, item_fn)

            # Metadata defaults
            meta = self._read_metadata(path)

            # Columns 1-6: Title, Artist, Album, Genre, Year, Charter
            defaults = [
                meta.get("title", path.stem),
                meta.get("artist", "Unknown Artist"),
                meta.get("album", ""),
                meta.get("genre", "Rock"),
                meta.get("year", ""),
                "Zullo7569" # Default charter
            ]

            for c, val in enumerate(defaults, 1):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

        # Resize columns to content
        self.table.resizeColumnsToContents()
        # Cap filename width so it doesn't take over
        if self.table.columnWidth(0) > 250: self.table.setColumnWidth(0, 250)

    def _read_metadata(self, path: Path) -> dict:
        """Best-effort metadata reader using Mutagen if available."""
        if not HAS_MUTAGEN: return {}

        data = {}
        try:
            f = mutagen.File(str(path))
            if not f: return {}

            # Helper to get first item safely
            def get_tag(keys):
                for k in keys:
                    if k in f.tags:
                        val = f.tags[k]
                        return val[0] if isinstance(val, list) else str(val)
                return None

            # ID3 (MP3)
            if isinstance(f.tags, mutagen.id3.ID3) or hasattr(f, 'tags'):
                # Try EasyID3 keys first if mapped, else raw frames
                data["title"] = get_tag(['TIT2', 'title'])
                data["artist"] = get_tag(['TPE1', 'artist'])
                data["album"] = get_tag(['TALB', 'album'])
                data["genre"] = get_tag(['TCON', 'genre'])
                data["year"] = get_tag(['TDRC', 'date', 'year'])

            # Vorbis (Ogg/FLAC) uses simpler keys usually
            if not data["title"] and 'title' in f.tags:
                data["title"] = f.tags['title'][0]
            if not data["artist"] and 'artist' in f.tags:
                data["artist"] = f.tags['artist'][0]

        except Exception:
            pass

        # Clean None values
        return {k: v for k, v in data.items() if v}

    def collect_data_and_accept(self):
        self.result_data = []
        for r in range(self.table.rowCount()):
            # Map columns back to config object structure
            # Path is implicit from self.files[r]
            row_data = {
                "path": self.files[r],
                "title": self.table.item(r, 1).text().strip(),
                "artist": self.table.item(r, 2).text().strip(),
                "album": self.table.item(r, 3).text().strip(),
                "genre": self.table.item(r, 4).text().strip(),
                "year": self.table.item(r, 5).text().strip(),
                "charter": self.table.item(r, 6).text().strip(),
            }
            self.result_data.append(row_data)
        self.accept()

    def get_data(self) -> list[dict]:
        return self.result_data

# ---------------- Review Dialog ----------------
class SectionReviewDialog(QDialog):
    def __init__(self, sections: list[dict], density_data: list[dict] | dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review Sections")
        self.resize(575, 675)
        self.sections = sections

        # Handle backward compatibility (if data is just a list)
        if isinstance(density_data, list):
            self.density_map = {"Expert": density_data}
        else:
            self.density_map = density_data

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 1. Density Graphs (Now in Tabs)
        lbl_graph = QLabel("Note Density & Structure")
        lbl_graph.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_graph)

        self.graph_tabs = SafeTabWidget()
        self.graphs = {} # Keep track of graph widgets to update them all later

        # Order of tabs
        diffs = ["Expert", "Hard", "Medium", "Easy"]

        for diff in diffs:
            if diff not in self.density_map: continue

            data = self.density_map[diff]
            graph = DensityGraphWidget(data, sections)
            self.graph_tabs.addTab(graph, diff)
            self.graphs[diff] = graph

        layout.addWidget(self.graph_tabs)

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
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        # Tighten padding to remove space between X and scrollbar
        self.table.setStyleSheet("QTableWidget::item { padding: 0px; margin: 0px; border: none; }")

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

            # Minimize internal margins/padding for the line edit to sit flush
            le.setStyleSheet("QLineEdit { border: none; background: transparent; padding: 2px 0px; margin: 0px; }")

            self.table.setItem(i, 0, t_item)
            self.table.setCellWidget(i, 1, le)

    def on_name_changed(self, row: int, new_name: str):
        if 0 <= row < len(self.sections):
            self.sections[row]['name'] = new_name
            # Update ALL graph instances so lines move/update on all tabs
            for graph in self.graphs.values():
                graph.set_sections(self.sections)

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
        tabs = SafeTabWidget()
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
        lbl.setStyleSheet("font-size: 12pt; font-weight: bold;")
        lbl.setAlignment(Qt.AlignCenter)

        sub = QLabel("We're happy to help. Please check the docs or send us a message.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color: palette(disabled-text); font-size: 11pt;")
        sub.setAlignment(Qt.AlignCenter)

        # Center buttons and limit width
        btn_layout = QVBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)

        btn_email = QPushButton("📧 Email Support")
        btn_email.setCursor(Qt.PointingHandCursor)
        btn_email.setMinimumHeight(40)
        btn_email.setFixedWidth(150)
        btn_email.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"mailto:{SUPPORT_EMAIL}")))

        btn_issue = QPushButton("🐞 Report on GitHub")
        btn_issue.setCursor(Qt.PointingHandCursor)
        btn_issue.setMinimumHeight(40)
        btn_issue.setFixedWidth(150)
        btn_issue.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"{REPO_URL}/issues")))

        btn_layout.addWidget(btn_email)
        btn_layout.addWidget(btn_issue)

        lay.addStretch()
        lay.addWidget(lbl)
        lay.addWidget(sub)
        lay.addStretch()
        lay.addLayout(btn_layout)
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
        txt.setStyleSheet("line-height: 1.4; font-size: 11pt;")

        btn_venmo = QPushButton("💙 Tip with Venmo")
        btn_venmo.setCursor(Qt.PointingHandCursor)
        btn_venmo.setMinimumHeight(45)
        btn_venmo.setFixedWidth(150)
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
        lay.addWidget(btn_venmo, 0, Qt.AlignCenter)
        lay.addStretch()

        return w
