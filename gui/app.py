from __future__ import annotations

import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from PIL import Image, ImageTk  # type: ignore
except ImportError:
    Image = None
    ImageTk = None


def _repo_root() -> Path:
    # repo_root is one level up from /gui
    return Path(__file__).resolve().parents[1]


def _venv_python() -> Path:
    return _repo_root() / ".venv" / "bin" / "python"


class OneClickCharterGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("CH 1-Click Charter")
        self.geometry("600x780")  # a little taller so Generate never gets cut off
        self.minsize(600, 850)
        self.resizable(True, True)

        self.audio_path: Path | None = None
        self.cover_path: Path | None = None
        self.cover_img = None  # keep reference alive

        self._build()

    # ---------------- UI ----------------

    def _build(self) -> None:
        pad = {"padx": 10, "pady": 6}

        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="CH 1-Click Charter", font=("Helvetica", 16, "bold")).pack(pady=(12, 4))
        ttk.Label(root, text="Generate fun, playable Medium charts", foreground="gray").pack(pady=(0, 14))

        # ---- Audio ----
        audio_box = ttk.LabelFrame(root, text="Audio")
        audio_box.pack(fill="x", **pad)

        self.audio_label = ttk.Label(audio_box, text="No file selected", foreground="gray")
        self.audio_label.pack(anchor="w", padx=10, pady=6)

        ttk.Button(audio_box, text="Browse Audio", command=self.pick_audio).pack(
            anchor="w", padx=10, pady=(0, 8)
        )

        # ---- Metadata ----
        meta = ttk.LabelFrame(root, text="Metadata")
        meta.pack(fill="x", **pad)

        self.title_var = tk.StringVar()
        self.artist_var = tk.StringVar()
        self.album_var = tk.StringVar()
        self.genre_var = tk.StringVar(value="Rock")

        self._entry(meta, "Title", self.title_var)
        self._entry(meta, "Artist", self.artist_var)
        self._entry(meta, "Album", self.album_var)
        self._entry(meta, "Genre", self.genre_var)

        art_row = ttk.Frame(meta)
        art_row.pack(fill="x", padx=10, pady=8)

        ttk.Button(art_row, text="Choose Album Art", command=self.pick_cover).pack(side="left")

        self.cover_preview = ttk.Label(art_row, text="No art", width=18, anchor="center")
        self.cover_preview.pack(side="right")

        # ---- Output ----
        out = ttk.LabelFrame(root, text="Output")
        out.pack(fill="x", **pad)

        self.out_dir = tk.StringVar(value="output")

        out_row = ttk.Frame(out)
        out_row.pack(fill="x", padx=10, pady=6)

        ttk.Label(out_row, text="Folder", width=12).pack(side="left")
        ttk.Entry(out_row, textvariable=self.out_dir).pack(
            side="left", fill="x", expand=True, padx=(0, 6)
        )
        ttk.Button(out_row, text="Browse…", command=self.pick_output_dir).pack(side="right")

        # ---- Advanced ----
        adv = ttk.LabelFrame(root, text="Advanced (optional)")
        adv.pack(fill="x", **pad)

        # IMPORTANT: real vs dummy (default to real)
        self.mode_var = tk.StringVar(value="real")
        mode_row = ttk.Frame(adv)
        mode_row.pack(fill="x", padx=10, pady=6)
        ttk.Label(mode_row, text="Mode", width=12).pack(side="left")
        ttk.Combobox(
            mode_row,
            textvariable=self.mode_var,
            values=["real", "dummy"],
            state="readonly",
        ).pack(side="left", fill="x", expand=True)

        # Real-chart knobs
        self.max_nps = tk.DoubleVar(value=2.8)
        self._slider(adv, "Max Notes / Second", self.max_nps, 1.5, 4.0)

        self.min_gap_ms = tk.IntVar(value=140)
        self._slider_int(adv, "Min Gap (ms)", self.min_gap_ms, 80, 220)

        self.seed = tk.IntVar(value=42)
        seed_row = ttk.Frame(adv)
        seed_row.pack(fill="x", padx=10, pady=6)
        ttk.Label(seed_row, text="Seed", width=12).pack(side="left")
        ttk.Entry(seed_row, textvariable=self.seed, width=10).pack(side="left")

        # ---- Generate ----
        self.generate_btn = ttk.Button(root, text="Generate Chart", command=self.run, state="disabled")
        self.generate_btn.pack(pady=18)

    # ---------------- Helpers ----------------

    def _entry(self, parent: ttk.Frame, label: str, var: tk.StringVar) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=10, pady=4)
        ttk.Label(row, text=label, width=12).pack(side="left")
        ttk.Entry(row, textvariable=var).pack(side="right", fill="x", expand=True)

    def _slider(self, parent: ttk.Frame, label: str, var: tk.DoubleVar, lo: float, hi: float) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=10, pady=6)
        ttk.Label(row, text=label).pack(anchor="w")
        ttk.Scale(row, from_=lo, to=hi, variable=var).pack(fill="x")

    def _slider_int(self, parent: ttk.Frame, label: str, var: tk.IntVar, lo: int, hi: int) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=10, pady=6)
        ttk.Label(row, text=label).pack(anchor="w")
        ttk.Scale(row, from_=lo, to=hi, variable=var).pack(fill="x")

    def _update_cover_preview(self, path: Path) -> None:
        if not Image or not ImageTk:
            self.cover_preview.config(text="Preview unavailable")
            return
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((128, 128))
            self.cover_img = ImageTk.PhotoImage(img)
            self.cover_preview.config(image=self.cover_img, text="")
        except Exception:
            self.cover_preview.config(text="Invalid image")

    # ---------------- Actions ----------------

    def pick_audio(self) -> None:
        p = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac")])
        if not p:
            return

        self.audio_path = Path(p)
        self.audio_label.config(text=self.audio_path.name, foreground="black")

        if not self.title_var.get():
            self.title_var.set(self.audio_path.stem)

        self.generate_btn.config(state="normal")

    def pick_cover(self) -> None:
        p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if not p:
            return

        self.cover_path = Path(p)
        self._update_cover_preview(self.cover_path)

    def pick_output_dir(self) -> None:
        p = filedialog.askdirectory()
        if p:
            self.out_dir.set(p)

    def run(self) -> None:
        if not self.audio_path:
            return

        py = _venv_python()
        if not py.exists():
            messagebox.showerror("Error", "Missing .venv. Run: make install")
            return

        title = self.title_var.get().strip() or self.audio_path.stem
        out_root = Path(self.out_dir.get()).expanduser().resolve()
        out_song = out_root / title

        # ✅ CRITICAL: call the repo code through the repo venv, and pass mode/knobs
        cmd = [
            str(py),
            "-m",
            "charter.cli",
            "--audio",
            str(self.audio_path),
            "--out",
            str(out_song),
            "--title",
            title,
            "--artist",
            self.artist_var.get(),
            "--album",
            self.album_var.get(),
            "--genre",
            self.genre_var.get(),
            "--charter",
            "Zullo7569",
            "--fetch-metadata",
            "--mode",
            self.mode_var.get(),
            "--min-gap-ms",
            str(int(self.min_gap_ms.get())),
            "--max-nps",
            f"{self.max_nps.get():.2f}",
            "--seed",
            str(int(self.seed.get())),
        ]

        try:
            subprocess.run(cmd, check=True)

            if self.cover_path:
                dest = out_song / "album.png"
                dest.write_bytes(self.cover_path.read_bytes())
                self._update_cover_preview(dest)

            messagebox.showinfo("Done", "Chart generated successfully.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Generation failed:\n{e}")


def main() -> None:
    app = OneClickCharterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
