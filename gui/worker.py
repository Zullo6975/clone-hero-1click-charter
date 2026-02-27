from __future__ import annotations
import json
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal

from gui.utils import get_python_exec, repo_root, RunConfig, is_frozen


class GenerationWorker(QObject):
    """
    Handles the background execution of the CLI for analysis, generation, and validation.
    """
    log_message = Signal(str)
    # Emits (success, output_path)
    finished = Signal(bool, Path)

    # CHANGED: density_list (list) -> density_data (dict) to match the new backend structure
    analysis_ready = Signal(list, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc: QProcess | None = None
        self._cfg: RunConfig | None = None
        self._is_analyzing = False
        self._out_song: Path | None = None

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.state() != QProcess.NotRunning

    def cancel(self):
        if self.is_running():
            self._proc.kill()
            self.log_message.emit("Cancelled by user.")

    def start(self, cfg: RunConfig, analyze_first: bool = False):
        if self.is_running():
            return

        self._cfg = cfg
        self._is_analyzing = analyze_first
        self._out_song = (cfg.out_root / cfg.title).resolve()
        self._out_song.mkdir(parents=True, exist_ok=True)

        args = self._build_args(cfg, self._out_song)
        if analyze_first:
            args.append("--analyze-only")
            self.log_message.emit(f"Starting analysis for: {cfg.title}...")
        else:
            self.log_message.emit(f"Starting generation for: {cfg.title}...")

        self._run_process(args)

    def resume_with_overrides(self, override_path: Path):
        """Called after the user accepts the Review Dialog"""
        if not self._cfg or not self._out_song:
            return

        self._is_analyzing = False
        args = self._build_args(self._cfg, self._out_song)
        args.extend(["--section-overrides", str(override_path)])

        self.log_message.emit("Starting final generation with overrides...")
        self._run_process(args)

    def validate(self, song_dir: Path):
        """Runs the validator tool independently"""
        py_exec = get_python_exec()

        if is_frozen():
            cmd_base = [str(py_exec), "--internal-cli"]
        else:
            cmd_base = [str(py_exec), "-m", "charter.cli"]

        args = cmd_base + ["--validate", str(song_dir)]

        validator = QProcess(self)
        validator.finished.connect(
            lambda c, s: self._on_validation_finished(validator, song_dir))
        validator.start(args[0], args[1:])

    def _run_process(self, args: list[str]):
        py_exec = get_python_exec()

        if is_frozen():
            cmd = [str(py_exec), "--internal-cli"]
        else:
            cmd = [str(py_exec), "-m", "charter.cli"]

        full_cmd = cmd + args

        self._proc = QProcess(self)
        self._proc.setProcessChannelMode(QProcess.SeparateChannels)

        if not is_frozen():
            self._proc.setWorkingDirectory(str(repo_root()))

        self._proc.readyReadStandardOutput.connect(self._on_stdout)
        self._proc.readyReadStandardError.connect(self._on_stderr)
        self._proc.finished.connect(self._on_process_finished)
        self._proc.start(full_cmd[0], full_cmd[1:])

    def _build_args(self, cfg: RunConfig, out_path: Path) -> list[str]:
        args = [
            "--audio", str(cfg.audio), "--out", str(out_path),
            "--title", cfg.title, "--artist", cfg.artist,
            "--album", cfg.album, "--genre", cfg.genre,
            "--charter", cfg.charter, "--mode", cfg.mode,
            "--min-gap-ms", str(
                cfg.min_gap_ms), "--max-nps", f"{cfg.max_nps:.2f}",
            "--seed", str(cfg.seed),
            "--chord-prob", str(cfg.chord_prob),
            "--sustain-len", str(cfg.sustain_len),
            "--sustain-threshold", str(cfg.sustain_threshold),
            "--sustain-buffer", str(cfg.sustain_buffer),
            "--hard-gap-ms", str(cfg.hard_gap_ms),
            "--med-gap-ms", str(cfg.med_gap_ms),
            "--easy-gap-ms", str(cfg.easy_gap_ms),
        ]

        # FIX: Only append flags if true.
        # Prevents passing empty strings [""] which crashes argparse on Windows.
        if cfg.fetch_metadata:
            args.append("--fetch-metadata")

        if cfg.write_chart:
            args.append("--write-chart")

        return args

    def _on_stdout(self):
        if self._proc:
            data = bytes(self._proc.readAllStandardOutput()
                         ).decode("utf-8", errors="replace")
            self.log_message.emit(data)

    def _on_stderr(self):
        if self._proc:
            data = bytes(self._proc.readAllStandardError()
                         ).decode("utf-8", errors="replace")
            self.log_message.emit(data)

    def _on_process_finished(self, code: int, status: QProcess.ExitStatus):
        ok = (status == QProcess.NormalExit) and (code == 0)

        if not ok:
            self.finished.emit(False, self._out_song)
            self._proc = None
            return

        if self._is_analyzing:
            # Parse sections.json
            json_path = self._out_song / "sections.json"
            if json_path.exists():
                try:
                    data = json.loads(json_path.read_text(encoding='utf-8'))
                    # Ensure we pass the 'density' field which is now a DICT, not a list
                    self.analysis_ready.emit(
                        data.get("sections", []), data.get("density", {}))
                except Exception as e:
                    self.log_message.emit(f"Error parsing analysis: {e}")
                    self.finished.emit(False, self._out_song)
            else:
                self.log_message.emit(
                    "Analysis failed: sections.json missing.")
                self.finished.emit(False, self._out_song)
        else:
            self.finished.emit(True, self._out_song)

        self._proc = None

    def _on_validation_finished(self, proc: QProcess, song_dir: Path):
        stdout = bytes(proc.readAllStandardOutput()).decode(
            "utf-8", errors="replace")
        stderr = bytes(proc.readAllStandardError()).decode(
            "utf-8", errors="replace")
        report = "\n--- VALIDATION REPORT ---\n" + stdout + stderr
        self.log_message.emit(report)
