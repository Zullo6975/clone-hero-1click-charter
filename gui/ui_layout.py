from __future__ import annotations

from gui.panels import MetadataWidget, OutputWidget, SettingsWidget
from gui.utils import get_font, repo_root
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QCheckBox, QFrame, QGroupBox, QHBoxLayout,
                               QLabel, QListWidget, QProgressBar, QPushButton,
                               QScrollArea, QSplitter, QStyle, QToolButton,
                               QVBoxLayout, QWidget)


class UiBuilder:
    def setup_ui(self, window):
        """
        Builds the complete UI and attaches widgets to the window instance.
        """
        central = QWidget()
        window.setCentralWidget(central)

        # ROOT LAYOUT: Zero margins so lines touch edges
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header (Now handles its own internal padding)
        self._build_header(window, main_layout)

        # Splitter Body
        window.splitter = QSplitter(Qt.Horizontal)
        window.splitter.setHandleWidth(1)
        # Visual line for the splitter handle
        # Light gray #d0d0d0, no margins
        window.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #d0d0d0;
                margin: 0px;
            }
        """)
        window.splitter.setChildrenCollapsible(False)
        main_layout.addWidget(window.splitter)

        # SIDEBAR (Audio, Queue, Art)
        window.sidebar_widget = QWidget()
        window.sidebar_widget.setMinimumWidth(340)
        window.sidebar_widget.setMaximumWidth(340)

        # Sidebar Padding: Restored here since root has 0
        sidebar_layout = QVBoxLayout(window.sidebar_widget)
        sidebar_layout.setContentsMargins(24, 24, 16, 24)
        sidebar_layout.setSpacing(20)
        self._build_sidebar_content(window, sidebar_layout)

        # MAIN PANEL (Meta, Config, Output)
        window.main_widget = QWidget()
        window.main_widget.setMinimumWidth(700)

        # Main Panel Padding: Restored here
        main_inner = QVBoxLayout(window.main_widget)
        main_inner.setContentsMargins(16, 24, 24, 24)
        main_inner.setSpacing(24)

        window.meta_panel = MetadataWidget()
        main_inner.addWidget(window.meta_panel)

        window.settings_panel = SettingsWidget()
        main_inner.addWidget(window.settings_panel)

        window.out_panel = OutputWidget()
        main_inner.addWidget(window.out_panel)
        main_inner.addStretch(1)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(window.main_widget)
        scroll.setFrameShape(QFrame.NoFrame)

        window.splitter.addWidget(window.sidebar_widget)
        window.splitter.addWidget(scroll)
        window.splitter.setStretchFactor(1, 1)

        # Footer
        self._build_footer(window)

    def _build_header(self, window, layout):
        # Header Container
        w = QWidget()
        # Header Internal Padding (Top/Left/Right=24, Bottom=12)
        h = QHBoxLayout(w)
        h.setContentsMargins(24, 24, 24, 12)
        h.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel()
        icon_path = repo_root() / "icons" / "icon_og.png"
        if icon_path.exists():
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                icon_lbl.setPixmap(pix.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        title_lbl = QLabel("CloneHero 1-Click Charter")
        title_lbl.setFont(get_font(32, True))

        h.addWidget(icon_lbl)
        h.addWidget(title_lbl)
        layout.addWidget(w)

        # Header Separator Line (Full Width)
        line = QFrame()
        line.setObjectName("HeaderLine")
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #d0d0d0; border: none;")
        layout.addWidget(line)

    def _build_sidebar_content(self, window, layout):
        # Audio
        grp_audio = QGroupBox("Input Audio (REQUIRED)")
        v = QVBoxLayout(grp_audio)
        window.audio_label = QLabel("Drag Audio Files Here")
        window.audio_label.setAlignment(Qt.AlignCenter)
        window.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text); font-size: 11pt;")

        window.btn_add_audio = QPushButton("Add Songs...")
        window.btn_add_audio.setIcon(window.style().standardIcon(QStyle.SP_DirOpenIcon))

        window.btn_clear_audio = QToolButton()
        window.btn_clear_audio.setIcon(window.style().standardIcon(QStyle.SP_DialogDiscardButton))

        h = QHBoxLayout()
        h.addWidget(window.btn_add_audio, 1)
        h.addWidget(window.btn_clear_audio, 0)
        v.addWidget(window.audio_label)
        v.addLayout(h)
        layout.addWidget(grp_audio)

        # Queue
        window.grp_queue = QGroupBox("Pending Queue")
        v_q = QVBoxLayout(window.grp_queue)

        window.queue_list = QListWidget()
        window.queue_list.setMaximumHeight(90)
        # Disable horizontal scrolling
        window.queue_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Queue Control Row
        row_q_btns = QHBoxLayout()
        window.btn_run_queue = QPushButton("▶ Run Queue")
        window.btn_run_queue.setCursor(Qt.PointingHandCursor)
        window.btn_run_queue.setToolTip("Process all songs in the queue automatically.")

        window.btn_clear_queue = QPushButton("Clear")
        window.btn_clear_queue.setCursor(Qt.PointingHandCursor)

        row_q_btns.addWidget(window.btn_run_queue, 1)
        row_q_btns.addWidget(window.btn_clear_queue, 0)

        v_q.addWidget(window.queue_list)
        v_q.addLayout(row_q_btns)
        layout.addWidget(window.grp_queue)

        # Art
        grp_art = QGroupBox("Album Art")
        v_a = QVBoxLayout(grp_art)
        window.cover_preview = QLabel("Drag Art Here")
        window.cover_preview.setAlignment(Qt.AlignCenter)
        window.cover_preview.setFixedSize(280, 280)
        window.cover_preview.setStyleSheet("border: 2px dashed palette(mid); border-radius: 6px; color: palette(disabled-text); font-style: italic; font-size: 11pt;")

        window.btn_pick_cover = QPushButton("Image...")
        window.btn_clear_cover = QToolButton()
        window.btn_clear_cover.setIcon(window.style().standardIcon(QStyle.SP_DialogDiscardButton))

        h_a = QHBoxLayout()
        h_a.addWidget(window.btn_pick_cover, 1)
        h_a.addWidget(window.btn_clear_cover, 0)
        v_a.addStretch()
        v_a.addWidget(window.cover_preview, 0, Qt.AlignCenter)
        v_a.addStretch()
        v_a.addLayout(h_a)
        layout.addWidget(grp_art)
        layout.addStretch()

    def _build_footer(self, window):
        # UPDATED: Footer Separator Horiz (Top border on status bar)
        # Since root layout has 0 margins, this touches left/right edges.
        window.statusBar().setStyleSheet("QStatusBar { border-top: 1px solid #d0d0d0; background: palette(window); }")

        # We put the footer logic into the status bar area to keep it sticky at bottom
        footer_widget = QWidget()
        lay = QHBoxLayout(footer_widget)
        lay.setContentsMargins(0, 5, 20, 5)
        lay.setSpacing(10)

        # Helper for vertical lines
        def vline():
            f = QFrame()
            f.setFrameShape(QFrame.VLine)
            f.setFixedWidth(1)
            # UPDATED: Light gray, no margins
            f.setStyleSheet("background-color: #d0d0d0; border: none;")
            return f

        # --- LEFT CONTROLS ---
        lay.addWidget(vline())

        window.chk_dark = QCheckBox("Dark Mode")
        window.chk_dark.setStyleSheet("font-size: 11pt;")
        window.chk_dark.setChecked(window.dark_mode)
        lay.addWidget(window.chk_dark)

        lay.addWidget(vline())

        window.btn_show_logs = QPushButton("Show Logs")
        window.btn_help = QPushButton("Help")
        window.btn_support = QPushButton("Support")

        lay.addWidget(window.btn_show_logs)
        lay.addWidget(window.btn_help)
        lay.addWidget(window.btn_support)

        # --- SPACER ---
        lay.addStretch()

        # --- RIGHT CONTROLS ---
        lay.addWidget(vline())

        window.btn_cancel = QPushButton("Cancel")
        window.btn_generate = QPushButton("GENERATE")
        window.btn_generate.setObjectName("Primary")
        window.btn_generate.setToolTip("Generate chart for the CURRENT song only.")

        lay.addWidget(window.btn_cancel)
        lay.addWidget(window.btn_generate)

        window.statusBar().addPermanentWidget(footer_widget, 1)

        # --- PROGRESS BAR (Left side of status bar) ---
        window.status_container = QWidget()
        s_lay = QHBoxLayout(window.status_container)
        s_lay.setContentsMargins(20, 0, 0, 0)

        window.status_label = QLabel("Ready")
        window.status_label.setStyleSheet("font-weight: bold; font-size: 11pt;")

        window.progress_bar = QProgressBar()
        window.progress_bar.setRange(0, 0)
        window.progress_bar.setVisible(False)
        window.progress_bar.setFixedWidth(200)
        window.progress_bar.setFixedHeight(12)

        s_lay.addWidget(window.status_label)
        s_lay.addWidget(window.progress_bar)
        s_lay.addStretch() # Push everything else to the right

        # Insert status container at index 0 (leftmost)
        window.statusBar().insertWidget(0, window.status_container, 1)

        # Menu
        menu = window.menuBar().addMenu("File")
        menu.addAction("Clear Log", window.log_window.clear)
        menu.addSeparator()
        menu.addAction("Quit", window.close)
