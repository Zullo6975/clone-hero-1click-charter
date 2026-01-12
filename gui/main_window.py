from __future__ import annotations
import json
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTimer, QProcess
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QFileDialog,
                               QListWidgetItem, QWidget, QHBoxLayout, QLabel, QToolButton, QStyle)

from charter.config import REPO_URL
from gui.utils import repo_root, RunConfig
from gui.theme import ThemeManager
from gui.widgets import LogWindow
from gui.dialogs import SectionReviewDialog, SupportDialog, BatchEntryDialog
from gui.worker import GenerationWorker

# Import the UI Builder
from gui.ui_layout import UiBuilder

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CloneHero 1-Click Charter")
        self.setAcceptDrops(True)
        self.settings = QSettings("Zullo", "1ClickCharter")

        self.audio_path: Path | None = None
        self.cover_path: Path | None = None
        self.last_out_song: Path | None = None

        self.validator_proc: QProcess | None = None

        self.song_queue: list[dict] = []
        self._title_user_edited = False
        self._is_batch_running = False

        self.log_window = LogWindow()
        self.worker = GenerationWorker(self)

        self.dark_mode = self.settings.value("dark_mode", True, type=bool)

        # --- UI SETUP ---
        self.ui_builder = UiBuilder()
        self.ui_builder.setup_ui(self)
        # ----------------

        self._wire()
        self._restore_settings()

        ThemeManager.apply_style(QApplication.instance(), self.dark_mode)

        # Load Presets
        self.settings_panel.refresh_presets()
        last_preset = self.settings.value("preset", "2) Standard", type=str)

        idx = self.settings_panel.preset_combo.findText(last_preset)
        if idx >= 0:
            self.settings_panel.preset_combo.setCurrentIndex(idx)
        else:
            self.settings_panel.preset_combo.setCurrentText("2) Standard")

        self.settings_panel.apply_preset(self.settings_panel.preset_combo.currentText())

        self._update_queue_display()
        # Initial State Update will happen via QTimer to ensure UI is ready
        QTimer.singleShot(100, self.snap_to_content)
        self.status_label.setText("Ready")

    def closeEvent(self, event) -> None:
        self.log_window.close()
        self.settings.setValue("dark_mode", self.chk_dark.isChecked())

        c_val = self.meta_panel.charter_edit.text().strip() or "Zullo7569"
        self.settings.setValue("charter", c_val)
        self.settings.setValue("out_dir", self.out_panel.dir_edit.text())
        self.settings.setValue("preset", self.settings_panel.preset_combo.currentText())
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)

    def _restore_settings(self) -> None:
        """Restores window geometry and last used text fields."""
        saved_charter = self.settings.value("charter", "Zullo7569", type=str)
        if saved_charter != "Zullo7569":
            self.meta_panel.charter_edit.setText(saved_charter)

        saved_out = self.settings.value("out_dir", "", type=str)
        self.out_panel.dir_edit.setText(saved_out)

        geom = self.settings.value("geometry")
        if geom: self.restoreGeometry(geom)

    def _wire(self):
        # Sidebar
        self.btn_add_audio.clicked.connect(self.add_to_queue_dialog)
        self.btn_clear_audio.clicked.connect(self.clear_audio)
        self.btn_clear_queue.clicked.connect(self.clear_queue)
        self.btn_pick_cover.clicked.connect(self.pick_cover)
        self.btn_clear_cover.clicked.connect(self.clear_cover)

        self.btn_run_queue.clicked.connect(self.run_batch_queue)

        # Output
        self.out_panel.btn_browse.clicked.connect(self.pick_output_dir)
        self.out_panel.btn_open_folder.clicked.connect(self.open_output_root)
        self.out_panel.btn_open_song.clicked.connect(self.open_last_song)

        # Footer
        self.chk_dark.toggled.connect(self.on_dark_toggle)
        self.btn_show_logs.clicked.connect(self.log_window.show)
        self.btn_help.clicked.connect(self.show_help)
        self.btn_support.clicked.connect(lambda: SupportDialog(self).exec())

        # Worker / Generation
        self.btn_generate.clicked.connect(self.run_generate)
        self.btn_cancel.clicked.connect(self.worker.cancel)

        self.worker.log_message.connect(self.log_window.append_text)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.analysis_ready.connect(self.on_analysis_ready)

        # State updates
        for w in [self.out_panel.dir_edit, self.meta_panel.title_edit, self.meta_panel.artist_edit]:
            w.textChanged.connect(self._update_state)

    def show_help(self) -> None:
        msg = """
        <h3>How to Use 1-Click Charter</h3>
        <ul>
            <li><b>Generate:</b> Process ONLY the currently loaded song.</li>
            <li><b>Run Queue:</b> Process current song + all pending songs automatically.</li>
        </ul>
        <p><b>Batch Add:</b> Drag multiple files to open the Batch Editor.</p>
        """
        QMessageBox.information(self, "Help", msg.strip())

    def _update_state(self):
        running = self.worker.is_running()
        has_audio = self.audio_path is not None and self.audio_path.exists()
        has_title = bool(self.meta_panel.title_edit.text().strip())
        has_artist = bool(self.meta_panel.artist_edit.text().strip())
        has_out = bool(self.out_panel.dir_edit.text().strip())
        has_queue = bool(self.song_queue)

        # 1. Main Generate Button (Single Song)
        self.btn_generate.setEnabled((not running) and has_audio and has_title and has_artist and has_out)
        self.btn_cancel.setEnabled(running)

        # 2. Batch Run Button Logic
        # Enabled ONLY if we have a queue (2+ songs total)
        # We allow it even if has_out is False so the user can click it and see the "Setup Required" warning
        self.btn_run_queue.setEnabled((not running) and has_queue)

        # Tooltip Feedback
        if not has_queue:
            self.btn_run_queue.setToolTip("Add more songs to create a batch.")
        elif not has_out:
            self.btn_run_queue.setToolTip("Click to set Output Folder.")
        else:
            total_count = len(self.song_queue) + (1 if has_audio else 0)
            self.btn_run_queue.setToolTip(f"Process {total_count} song(s) in sequence.")

        self.out_panel.btn_open_folder.setEnabled(has_out)
        self.out_panel.btn_open_song.setEnabled(self.last_out_song is not None and self.last_out_song.exists())

    def run_generate(self):
        """Standard Generation - ONE SONG ONLY"""
        self._is_batch_running = False
        self._start_generation_process()

    def run_batch_queue(self):
        """Batch Generation - Process Current + Loop Queue"""
        # VALIDATION CHECKS with POPUPS
        has_audio = self.audio_path is not None and self.audio_path.exists()
        has_out = bool(self.out_panel.dir_edit.text().strip())
        has_queue = bool(self.song_queue)

        if not has_out:
            QMessageBox.warning(self, "Setup Required", "Please select an <b>Output Folder</b> before starting the queue.")
            self.out_panel.btn_browse.click() # Auto-trigger the browse dialog
            return

        if not has_queue:
            # Should be unreachable if disabled, but safe to keep
            QMessageBox.information(self, "Queue Empty", "Add more songs to start a batch run.")
            return

        # Start Batch
        if not self.audio_path and self.song_queue:
            self._pop_next_song()

        self._is_batch_running = True
        self._start_generation_process()

    def _start_generation_process(self):
        cfg = self.build_cfg()
        if not cfg: return

        self.log_window.clear()
        self.btn_generate.setText("Generating....")
        self.btn_generate.setEnabled(False)
        self.btn_run_queue.setEnabled(False)

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Working...")

        analyze = self.settings_panel.chk_review.isChecked()
        self.worker.start(cfg, analyze_first=analyze)
        # Note: We do NOT call _update_state() here because we want buttons disabled manually above

    def on_analysis_ready(self, sections, density):
        dlg = SectionReviewDialog(sections, density, self)
        if dlg.exec():
            overrides = dlg.get_sections()
            out_json = (self.worker._out_song / "overrides.json")
            out_json.write_text(json.dumps(overrides, indent=2))
            self.worker.resume_with_overrides(out_json)
        else:
            self.worker.cancel()
            self.reset_ui_after_run()
            self.status_label.setText("Cancelled")
            self._is_batch_running = False

    def on_worker_finished(self, success: bool, out_song: Path):
        self.reset_ui_after_run()
        if not success:
            self.status_label.setText("Failed")
            self._is_batch_running = False
            QMessageBox.critical(self, "Process Failed", "Check logs for details.")
            return

        self.last_out_song = out_song

        if self.cover_path and self.cover_path.exists():
            try:
                (out_song / "album.png").write_bytes(self.cover_path.read_bytes())
                self.log_window.append_text("Cover copied.")
            except: pass

        self.status_label.setText("Validating...")
        self.run_health_check(out_song)

        # AUTO-QUEUE LOGIC
        if self._is_batch_running and self.song_queue:
            self._pop_next_song()
            self.status_label.setText(f"Batch: Starting {self.audio_path.name}...")
            QTimer.singleShot(1000, self._start_generation_process)
        else:
            self._is_batch_running = False
            self.status_label.setText("Finished")
            if not self.song_queue:
                self._clear_song_info()
                self.audio_path = None
                self.audio_label.setText("Drag Audio Files Here")
                self.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text); font-size: 11pt;")

        self._update_state()

    def _pop_next_song(self):
        if not self.song_queue: return

        next_s_data = self.song_queue.pop(0)
        self._clear_song_info()

        if isinstance(next_s_data, dict):
            self.load_audio(next_s_data["path"])
            self.meta_panel.title_edit.setText(next_s_data.get("title", ""))
            self.meta_panel.artist_edit.setText(next_s_data.get("artist", ""))
            self.meta_panel.album_edit.setText(next_s_data.get("album", ""))
            self.meta_panel.genre_edit.setText(next_s_data.get("genre", ""))
            if next_s_data.get("charter"):
                self.meta_panel.charter_edit.setText(next_s_data["charter"])
        else:
            self.load_audio(next_s_data)

        self._update_queue_display()

    def reset_ui_after_run(self):
        self.btn_generate.setText("  GENERATE  ")
        self.progress_bar.setVisible(False)
        self._update_state()

    def build_cfg(self) -> RunConfig | None:
        if not self.audio_path: return None
        out_txt = self.out_panel.dir_edit.text().strip()
        if not out_txt:
            QMessageBox.critical(self, "Error", "Output folder required.")
            return None

        mp = self.meta_panel
        sp = self.settings_panel

        return RunConfig(
            audio=self.audio_path,
            out_root=Path(out_txt).expanduser().resolve(),
            title=mp.title_edit.text().strip(),
            artist=mp.artist_edit.text().strip(),
            album=mp.album_edit.text().strip(),
            genre=mp.genre_edit.text().strip() or "Rock",
            charter=mp.charter_edit.text().strip() or "Zullo7569",

            mode="real" if sp.mode_real.isChecked() else "dummy",
            max_nps=sp.max_nps_spin.value(),
            min_gap_ms=sp.min_gap_spin.value(),
            seed=sp.seed_spin.value(),

            allow_orange=True, rhythmic_glue=True, grid_snap="1/16",

            chord_prob=sp.chord_slider.value()/100.0,
            sustain_len=sp.sustain_slider.value()/100.0,
            sustain_threshold=sp.sustain_gap_spin.value(),
            sustain_buffer=sp.sustain_buffer_spin.value(),

            hard_gap_ms=sp.spin_hard_gap.value(),
            med_gap_ms=sp.spin_med_gap.value(),
            easy_gap_ms=sp.spin_easy_gap.value(),
            fetch_metadata=True
        )

    # --- Helpers ---
    def append_log(self, text: str):
        self.log_window.append_text(text)

    def load_audio(self, path: Path):
        self.audio_path = path
        self.audio_label.setText(path.name)
        self.audio_label.setStyleSheet("color: palette(text); font-weight: bold;")
        if not self._title_user_edited and not self.meta_panel.title_edit.text().strip():
            self.meta_panel.title_edit.setText(path.stem)
        self._update_state()

    def clear_audio(self):
        self._clear_song_info()

        if self.song_queue:
            self._pop_next_song()
            self.status_label.setText(f"Queue: Loaded {self.audio_path.name}")
        else:
            self.audio_path = None
            self.audio_label.setText("Drag Audio Files Here")
            self.audio_label.setStyleSheet("font-style: italic; color: palette(disabled-text); font-size: 11pt;")
            self.status_label.setText("Audio cleared")
            self._update_state()
            self.audio_label.adjustSize()
            QTimer.singleShot(10, self.snap_to_content)

    def _clear_song_info(self):
        self.meta_panel.clear_fields()
        self.clear_cover()
        self._title_user_edited = False

    def add_to_queue_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Add Audio", "", "Audio (*.mp3 *.wav *.ogg *.flac)")
        if not files: return
        paths = [Path(f) for f in files]

        if not self.audio_path and paths:
            self.load_audio(paths.pop(0))

        self.song_queue.extend(paths)
        self._update_queue_display()

    def _update_queue_display(self):
        self.queue_list.clear()
        self.btn_clear_queue.setEnabled(bool(self.song_queue))
        for i, item_data in enumerate(self.song_queue):
            item = QListWidgetItem(self.queue_list)
            wid = QWidget()
            h = QHBoxLayout(wid)
            h.setContentsMargins(4,0,4,0)

            if isinstance(item_data, dict):
                name = item_data["path"].name
                if item_data.get("title"):
                    name = f"{item_data['title']} - {item_data.get('artist', 'Unknown')}"
            else:
                name = item_data.name

            lbl = QLabel(name)
            lbl.setStyleSheet("background: transparent; font-size: 11px;")
            h.addWidget(lbl, 1)

            btn = QToolButton()
            btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
            btn.setFixedSize(20, 20)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("border: none; background: transparent;")

            btn.clicked.connect(lambda checked=False, idx=i: self._remove_queue_item(idx))
            h.addWidget(btn, 0)
            item.setSizeHint(wid.sizeHint())
            self.queue_list.setItemWidget(item, wid)

        self._update_state()

    def _remove_queue_item(self, idx):
        if 0 <= idx < len(self.song_queue):
            self.song_queue.pop(idx)
            self._update_queue_display()

    def clear_queue(self):
        self.song_queue.clear()
        self._update_queue_display()

    def pick_cover(self):
        p, _ = QFileDialog.getOpenFileName(self, "Art", "", "Images (*.png *.jpg)")
        if p: self.load_cover(Path(p))

    def load_cover(self, p: Path):
        self.cover_path = p
        self.cover_preview.setPixmap(QPixmap(str(p)).scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.cover_preview.setText("")

    def clear_cover(self):
        self.cover_path = None
        self.cover_preview.setPixmap(QPixmap())
        self.cover_preview.setText("Drag Art Here")

    def pick_output_dir(self):
        p = QFileDialog.getExistingDirectory(self, "Output Folder")
        if p: self.out_panel.dir_edit.setText(p)

    def open_output_root(self):
        self._open(Path(self.out_panel.dir_edit.text()))

    def open_last_song(self):
        if self.last_out_song: self._open(self.last_out_song)

    def _open(self, p: Path):
        QProcess.startDetached("open" if sys.platform=="darwin" else "explorer" if sys.platform=="win32" else "xdg-open", [str(p)])

    def on_dark_toggle(self, checked):
        ThemeManager.apply_style(QApplication.instance(), checked)

    def snap_to_content(self):
        if self.centralWidget(): self.centralWidget().layout().activate()
        self.resize(1000, 700)

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls(): e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        urls = e.mimeData().urls()
        audio_ext = {".mp3", ".wav", ".ogg", ".flac"}
        img_ext = {".jpg", ".png", ".jpeg"}
        new_s = []
        for u in urls:
            p = Path(u.toLocalFile())
            if p.suffix.lower() in audio_ext: new_s.append(p)
            elif p.suffix.lower() in img_ext: self.load_cover(p)

        if new_s:
            if not self.audio_path: self.load_audio(new_s.pop(0))
            self.song_queue.extend(new_s)
            self._update_queue_display()

    # --- Health Check / Validation Popup Logic ---
    def run_health_check(self, song_dir: Path) -> None:
        from gui.utils import get_python_exec, is_frozen

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

        is_middle_of_batch = self._is_batch_running and bool(self.song_queue)

        if not is_middle_of_batch:
            self.status_label.setText("Ready")

            if self._is_batch_running and not self.song_queue:
                msg = f"Batch processing complete!\n\nLast Chart:\n{song_dir}"
            else:
                msg = f"Chart generated successfully!\n\nLocation:\n{song_dir}"

            if warnings:
                msg += "\n\nWarnings/Errors:\n" + "\n".join(f"• {w[:80]}" for w in warnings[:5])
                if len(warnings) > 5: msg += "\n... (check logs for more)"

            title = "Generation Complete" if not warnings else "Complete (With Warnings)"
            icon = QMessageBox.Information if not warnings else QMessageBox.Warning

            def show_box():
                self.activateWindow()
                mbox = QMessageBox(icon, title, msg, QMessageBox.Ok, self)
                mbox.setMinimumWidth(450)
                mbox.setWindowModality(Qt.ApplicationModal)
                mbox.exec()

            QTimer.singleShot(100, show_box)

        self.validator_proc = None
