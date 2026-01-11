from __future__ import annotations
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget, QHeaderView, QAbstractItemView,
                               QTableWidgetItem, QLineEdit, QDialogButtonBox, QWidget, QPushButton)
from PySide6.QtGui import QDesktopServices, Qt
from PySide6.QtCore import QUrl

# Imports from other GUI modules
from gui.widgets import DensityGraphWidget, SafeTabWidget
from charter.config import SUPPORT_EMAIL, VENMO_URL, REPO_URL

# ---------------- Review Dialog ----------------
class SectionReviewDialog(QDialog):
    def __init__(self, sections: list[dict], density_data: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review Sections")
        self.resize(500, 600)
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
        self.table.setColumnCount(2)
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
        lbl.setStyleSheet("font-size: 11pt; font-weight: bold;")
        lbl.setAlignment(Qt.AlignCenter)

        sub = QLabel("We're happy to help. Please check the docs or send us a message.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color: palette(disabled-text);")
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
        txt.setStyleSheet("line-height: 1.4;")

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
