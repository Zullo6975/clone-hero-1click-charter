from __future__ import annotations
from PySide6.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QToolButton, QLabel, QCheckBox,
                               QButtonGroup, QRadioButton, QFrame, QPushButton, QInputDialog, QMessageBox, QStyle, QAbstractSpinBox)
from PySide6.QtCore import Qt

# Import custom widgets and helpers
from gui.utils import form_label
from gui.widgets import SafeComboBox, SafeSpinBox, SafeDoubleSpinBox, SafeSlider, SafeTabWidget
from gui.presets import DEFAULT_PRESETS, load_all_presets, save_user_preset, delete_user_preset

class MetadataWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Song Metadata", parent)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignVCenter)
        layout.setVerticalSpacing(14)

        self.title_edit = QLineEdit()
        self.artist_edit = QLineEdit()
        self.album_edit = QLineEdit()
        self.genre_edit = QLineEdit()
        self.genre_edit.setPlaceholderText("Default: Rock")
        self.charter_edit = QLineEdit()
        self.charter_edit.setPlaceholderText("Default: Zullo7569")

        self.btn_clear = QToolButton()
        self.btn_clear.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_clear.setToolTip("Clear all metadata fields")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_fields)

        layout.addRow(form_label("Title", required=True, align=Qt.AlignCenter), self.title_edit)
        layout.addRow(form_label("Artist", required=True, align=Qt.AlignCenter), self.artist_edit)
        layout.addRow(form_label("Album", align=Qt.AlignCenter), self.album_edit)
        layout.addRow(form_label("Genre", align=Qt.AlignCenter), self.genre_edit)
        layout.addRow(form_label("Charter", align=Qt.AlignCenter), self.charter_edit)

        row_clear = QHBoxLayout()
        row_clear.addStretch()
        row_clear.addWidget(QLabel("Clear Fields "))
        row_clear.addWidget(self.btn_clear)
        layout.addRow("", row_clear)

    def clear_fields(self):
        self.title_edit.clear()
        self.artist_edit.clear()
        self.album_edit.clear()
        self.genre_edit.clear()
        self.charter_edit.clear()

class SettingsWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Chart Settings", parent)
        self.all_presets = {}
        self.init_ui()
        self.refresh_presets()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.chk_adv = QCheckBox("Show Tuning Controls")
        self.chk_adv.setStyleSheet("font-weight: bold; margin-bottom: 6px;")
        self.chk_adv.setCursor(Qt.PointingHandCursor)
        self.chk_adv.toggled.connect(self.toggle_advanced)
        main_layout.addWidget(self.chk_adv)

        self.content_widget = QWidget()
        self.content_widget.setVisible(False)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # Presets Row
        preset_row = QWidget()
        preset_layout = QHBoxLayout(preset_row)
        preset_layout.setContentsMargins(0, 0, 0, 0)

        lbl_preset = QLabel("Expert Style:")
        lbl_preset.setMinimumWidth(100)
        lbl_preset.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.preset_combo = SafeComboBox()
        self.preset_combo.setCursor(Qt.PointingHandCursor)
        self.preset_combo.setMinimumWidth(200)
        # currentIndexChanged to handle clean keys from itemData
        self.preset_combo.currentIndexChanged.connect(self._on_combo_changed)

        self.btn_save_preset = QToolButton()
        self.btn_save_preset.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.btn_save_preset.setToolTip("Save current settings as a new preset")
        self.btn_save_preset.setCursor(Qt.PointingHandCursor)
        self.btn_save_preset.clicked.connect(self.on_save_preset)

        self.btn_del_preset = QToolButton()
        self.btn_del_preset.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_del_preset.setToolTip("Delete selected preset (User presets only)")
        self.btn_del_preset.setCursor(Qt.PointingHandCursor)
        self.btn_del_preset.clicked.connect(self.on_delete_preset)

        preset_layout.addWidget(lbl_preset)
        preset_layout.addWidget(self.preset_combo, 1)
        preset_layout.addWidget(self.btn_save_preset)
        preset_layout.addWidget(self.btn_del_preset)
        content_layout.addWidget(preset_row)

        self.preset_hint = QLabel("Select baseline intensity.")
        self.preset_hint.setStyleSheet("color: palette(disabled-text); font-size: 11pt; margin-left: 110px;")
        content_layout.addWidget(self.preset_hint)

        self.chk_review = QCheckBox("Review Sections before Generation")
        self.chk_review.setToolTip("Show a list of detected sections to rename/edit before creating the chart.")
        self.chk_review.setCursor(Qt.PointingHandCursor)
        row_review = QHBoxLayout()
        row_review.addSpacing(110)
        row_review.addWidget(self.chk_review)
        content_layout.addLayout(row_review)

        # Tabs
        self.tabs = SafeTabWidget()
        self.init_expert_tab()
        self.init_scaling_tab()

        # Help Button in Corner
        self.btn_help = QToolButton()
        self.btn_help.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        self.btn_help.setToolTip("Explanation of Settings")
        self.btn_help.setCursor(Qt.PointingHandCursor)
        self.btn_help.clicked.connect(self.show_explanation)
        self.tabs.setCornerWidget(self.btn_help, Qt.TopRightCorner)

        content_layout.addWidget(self.tabs)

        main_layout.addWidget(self.content_widget)

    def init_expert_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setLabelAlignment(Qt.AlignRight)

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

        self.max_nps_spin = SafeDoubleSpinBox()
        self.max_nps_spin.setRange(1.0, 30.0)
        self.max_nps_spin.setSingleStep(0.1)
        self.max_nps_spin.setValue(13.0)
        self.max_nps_spin.setSuffix(" NPS")
        self.max_nps_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus) # Arrows Enabled

        self.min_gap_spin = SafeSpinBox()
        self.min_gap_spin.setRange(10, 1000)
        self.min_gap_spin.setSingleStep(10)
        self.min_gap_spin.setValue(55)
        self.min_gap_spin.setSuffix(" ms")
        self.min_gap_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus) # Arrows Enabled

        self.seed_spin = SafeSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setValue(0)
        self.seed_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus) # Arrows Enabled

        self.chord_slider = SafeSlider(Qt.Horizontal)
        self.chord_slider.setRange(0, 50)
        self.chord_slider.setValue(22)

        self.sustain_slider = SafeSlider(Qt.Horizontal)
        self.sustain_slider.setRange(0, 100)
        self.sustain_slider.setValue(25)

        self.sustain_gap_spin = SafeDoubleSpinBox()
        self.sustain_gap_spin.setRange(0.1, 2.0)
        self.sustain_gap_spin.setSingleStep(0.1)
        self.sustain_gap_spin.setValue(0.2)
        self.sustain_gap_spin.setSuffix(" s")
        self.sustain_gap_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus) # Arrows Enabled

        self.sustain_buffer_spin = SafeDoubleSpinBox()
        self.sustain_buffer_spin.setRange(0.05, 0.5)
        self.sustain_buffer_spin.setSingleStep(0.05)
        self.sustain_buffer_spin.setValue(0.15)
        self.sustain_buffer_spin.setSuffix(" s")
        self.sustain_buffer_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus) # Arrows Enabled

        form.addRow(form_label("Generation Mode"), row_mode)
        form.addRow(form_label("Max Notes/Sec"), self.max_nps_spin)
        form.addRow(form_label("Min Note Spacing"), self.min_gap_spin)
        form.addRow(form_label("Pattern Variation"), self.seed_spin)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("color: palette(mid);")
        form.addRow(div)

        form.addRow(form_label("Chord Density"), self.chord_slider)
        form.addRow(form_label("Sustain Prob."), self.sustain_slider)
        form.addRow(form_label("Min Gap for Sustain"), self.sustain_gap_spin)
        form.addRow(form_label("Sustain End Buffer"), self.sustain_buffer_spin)

        self.tabs.addTab(tab, "Expert Baseline")

    def init_scaling_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        lbl_info = QLabel("Lower difficulties are created by filtering the Expert chart. "
                          "Edit the 'Gap' (ms) or the 'Target NPS' to adjust difficulty.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: palette(disabled-text); font-style: italic; margin-bottom: 10px; font-size: 11pt;")
        layout.addWidget(lbl_info)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        # Helper to force arrows and set props
        def config_spin(w_ms, w_nps):
            w_ms.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus) # Arrows Enabled
            w_nps.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus) # Arrows Enabled
            w_nps.setToolTip("Approximate max notes per second")
            self._wire_sync(w_ms, w_nps)

        # Hard Controls
        self.spin_hard_gap = SafeSpinBox()
        self.spin_hard_gap.setRange(40, 500) # 25 NPS to 2 NPS
        self.spin_hard_gap.setSuffix(" ms")
        self.spin_hard_nps = SafeDoubleSpinBox()
        self.spin_hard_nps.setRange(2.0, 25.0)
        self.spin_hard_nps.setSingleStep(0.1)
        self.spin_hard_nps.setSuffix(" NPS")
        config_spin(self.spin_hard_gap, self.spin_hard_nps)

        # Medium Controls
        self.spin_med_gap = SafeSpinBox()
        self.spin_med_gap.setRange(100, 1000) # 10 NPS to 1 NPS
        self.spin_med_gap.setSuffix(" ms")
        self.spin_med_nps = SafeDoubleSpinBox()
        self.spin_med_nps.setRange(1.0, 10.0)
        self.spin_med_nps.setSingleStep(0.1)
        self.spin_med_nps.setSuffix(" NPS")
        config_spin(self.spin_med_gap, self.spin_med_nps)

        # Easy Controls
        self.spin_easy_gap = SafeSpinBox()
        self.spin_easy_gap.setRange(125, 2000) # 8 NPS to 0.5 NPS
        self.spin_easy_gap.setSuffix(" ms")
        self.spin_easy_nps = SafeDoubleSpinBox()
        self.spin_easy_nps.setRange(0.5, 8.0)
        self.spin_easy_nps.setSingleStep(0.1)
        self.spin_easy_nps.setSuffix(" NPS")
        config_spin(self.spin_easy_gap, self.spin_easy_nps)

        # Default Values (will be overwritten by presets)
        self.spin_hard_gap.setValue(120)
        self.spin_med_gap.setValue(220)
        self.spin_easy_gap.setValue(450)

        # Helper for rows
        def row(spin_ms, spin_nps):
            h = QHBoxLayout()
            h.addWidget(spin_ms, 1)
            h.addWidget(QLabel("↔"))
            h.addWidget(spin_nps, 1)
            return h

        form.addRow(form_label("Hard Scaling"), row(self.spin_hard_gap, self.spin_hard_nps))
        form.addRow(form_label("Medium Scaling"), row(self.spin_med_gap, self.spin_med_nps))
        form.addRow(form_label("Easy Scaling"), row(self.spin_easy_gap, self.spin_easy_nps))

        layout.addLayout(form)
        layout.addStretch()
        self.tabs.addTab(tab, "Difficulty Scaling")

    def _wire_sync(self, spin_ms: SafeSpinBox, spin_nps: SafeDoubleSpinBox):
        # Prevent feedback loops by blocking signals during programmatic updates
        def on_ms_change(val):
            if val <= 0: return
            new_nps = 1000.0 / val
            spin_nps.blockSignals(True)
            spin_nps.setValue(new_nps)
            spin_nps.blockSignals(False)

        def on_nps_change(val):
            if val <= 0: return
            new_ms = int(1000.0 / val)
            spin_ms.blockSignals(True)
            spin_ms.setValue(new_ms)
            spin_ms.blockSignals(False)

        spin_ms.valueChanged.connect(on_ms_change)
        spin_nps.valueChanged.connect(on_nps_change)

    def toggle_advanced(self, checked: bool):
        self.content_widget.setVisible(checked)

    def show_explanation(self):
        msg = """
        <h3>Difficulty & Tuning Guide</h3>
        <p><b>Expert Baseline:</b> This is how the Expert chart is generated. It sets the maximum intensity.</p>
        <ul>
            <li><b>Max NPS:</b> The speed limit for the hardest sections.</li>
            <li><b>Min Spacing:</b> Minimum time (ms) between any two notes.</li>
            <li><b>Chords/Sustain:</b> Probability of these events occurring.</li>
        </ul>
        <hr/>
        <p><b>Difficulty Scaling:</b> Lower difficulties are created by filtering the Expert chart.</p>
        <ul>
            <li><b>Gap (ms):</b> Notes closer together than this value are removed.</li>
            <li><b>Target NPS:</b> An easier way to think about Gap. "5 NPS" means we try to limit the chart to roughly 5 notes per second.</li>
        </ul>
        <p><i>Example: If Expert has a fast stream (100ms gap), setting Hard Gap to 150ms will force the stream to thin out.</i></p>
        """
        QMessageBox.information(self, "Settings Guide", msg.strip())

    def refresh_presets(self):
        # preserve current key if possible
        current_idx = self.preset_combo.currentIndex()
        current_key = self.preset_combo.itemData(current_idx) if current_idx >= 0 else None

        self.all_presets = load_all_presets()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()

        # 1. Defaults (Sorted 1-4)
        defaults = sorted(list(DEFAULT_PRESETS.keys()))
        for k in defaults:
            self.preset_combo.addItem(k, k) # Text=Key, Data=Key

        # 2. Custom (Sorted Alphabetically, Displayed as "5) Name")
        others = sorted([k for k in self.all_presets.keys() if k not in DEFAULT_PRESETS])
        for i, k in enumerate(others):
            # i starts at 0, so we add 5 to start numbering at 5
            display_name = f"{i + 5}) {k}"
            self.preset_combo.addItem(display_name, k) # Text="5) Name", Data="Name"

        self.preset_combo.addItem("Custom…", None)

        # Restore Selection
        if current_key:
            idx = self.preset_combo.findData(current_key)
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)
            else:
                self.preset_combo.setCurrentText("2) Standard")
        else:
            self.preset_combo.setCurrentText("2) Standard")

        self.preset_combo.blockSignals(False)
        self._update_del_button()

    def _on_combo_changed(self, index: int):
        key = self.preset_combo.itemData(index)
        if key:
            self.apply_preset(key)
        else:
            # Custom selected
            self.preset_hint.setText("Manual control enabled.")
            self._update_del_button()

    def _update_del_button(self):
        idx = self.preset_combo.currentIndex()
        key = self.preset_combo.itemData(idx)
        # Enable delete only if it's a valid key (not Custom) and not a default
        is_default = key in DEFAULT_PRESETS
        self.btn_del_preset.setEnabled(bool(key) and not is_default)

    def apply_preset(self, name: str):
        preset = self.all_presets.get(name)
        if not preset: return

        self.max_nps_spin.setValue(float(preset["max_nps"]))
        self.min_gap_spin.setValue(int(preset["min_gap_ms"]))
        self.sustain_slider.setValue(int(preset["sustain"]))
        self.chord_slider.setValue(int(preset["chord"]))

        self.spin_hard_gap.setValue(int(preset.get("hard_gap", 120)))
        self.spin_med_gap.setValue(int(preset.get("med_gap", 220)))
        self.spin_easy_gap.setValue(int(preset.get("easy_gap", 450)))

        self.preset_hint.setText(f"Active: {preset['max_nps']} NPS | Med Gap: {preset.get('med_gap', 220)}ms")
        self._update_del_button()

    def on_save_preset(self):
        # Ask for name without numbers
        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name (without numbers):")
        if ok and name.strip():
            name = name.strip()
            data = {
                "max_nps": self.max_nps_spin.value(),
                "min_gap_ms": self.min_gap_spin.value(),
                "sustain": self.sustain_slider.value(),
                "chord": self.chord_slider.value(),
                "hard_gap": self.spin_hard_gap.value(),
                "med_gap": self.spin_med_gap.value(),
                "easy_gap": self.spin_easy_gap.value()
            }
            save_user_preset(name, data)
            self.refresh_presets()

            # Select the new item using findData because the Text is different
            idx = self.preset_combo.findData(name)
            if idx >= 0: self.preset_combo.setCurrentIndex(idx)

    def on_delete_preset(self):
        idx = self.preset_combo.currentIndex()
        key = self.preset_combo.itemData(idx)
        if not key or key in DEFAULT_PRESETS: return

        ret = QMessageBox.question(self, "Delete Preset", f"Delete '{key}'?")
        if ret == QMessageBox.Yes:
            delete_user_preset(key)
            self.refresh_presets()


class OutputWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Output Destination  (REQUIRED)", parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        row1 = QHBoxLayout()
        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText("Select output folder...")

        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.setCursor(Qt.PointingHandCursor)

        self.btn_clear = QToolButton()
        self.btn_clear.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.btn_clear.setToolTip("Clear output path")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.dir_edit.clear)

        row1.addWidget(self.dir_edit, 1)
        row1.addWidget(self.btn_browse, 0)
        row1.addWidget(self.btn_clear, 0)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.btn_open_folder = QPushButton("Open Folder")
        self.btn_open_folder.setCursor(Qt.PointingHandCursor)
        self.btn_open_song = QPushButton("Open Last Song")
        self.btn_open_song.setCursor(Qt.PointingHandCursor)

        row2.addWidget(self.btn_open_folder)
        row2.addWidget(self.btn_open_song)
        row2.addStretch()

        layout.addLayout(row1)
        layout.addLayout(row2)
