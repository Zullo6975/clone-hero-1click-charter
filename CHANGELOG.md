# Changelog

## [1.1.0] - 2026-01-09

### The "Musicality" Update

This major update focuses on making the generated charts feel less random and more like real music, while also making the app fully standalone.

### 🎸 Audio Engine Overhaul

- **Smart Sections:** The engine now analyzes note density to automatically detect and label **"Guitar Solos"**.
- **Pitch Contouring:** Notes now statistically follow the direction of the melody (if the song goes up, the notes go Right; if down, Left).
- **Rhythmic Glue:** Detected repeated rhythmic motifs in the audio and forced the chart to use consistent patterns for them.
- **Sustain Physics:** Completely rewritten sustain logic with configurable "Minimum Gap" and "End Buffer" to prevent impossible holds.
- **Audio Normalization:** All input songs are now auto-leveled to **-14 LUFS** to ensure consistent volume in-game.

### 📦 Core & Packaging

- **Standalone Audio Engine:** **FFmpeg** and **FFprobe** are now bundled inside the application. Users no longer need to install anything manually—just download and run.

### 🖥️ UI/UX Improvements

- **Cleaner Layout:** Moved the Progress Bar to the status bar to declutter the footer.
- **Readability:** Increased global font size to 11pt and standardized button heights.
- **Stability:** Fixed layout shifting when scrollbars appear and prevented text resizing bugs when toggling Dark Mode.

## [1.0.2] - 2026-01-08

### Image Replacement

Fixing a lost image.

## [1.0.1] - 2026-01-08

### Documentation Updates

Highlighting the usage of AI.

## [1.0.0] - 2026-01-08

### Initial Release

The first official release of **CloneHero 1-Click Charter**, a tool designed to make creating fun, playable charts accessible to everyone.

### ✨ Core Features

- **One-Click Generation:** Drag and drop audio files to instantly generate a chart.
- **Smart Analysis:** Uses `librosa` audio analysis to sync notes to the beat (groove-locked to 1/8 grid).
- **Medium Difficulty Focus:** Default settings are tuned for a "GH3 Medium" feel—predictable, rhythmic, and fair.
- **Batch Processing:** Queue system allows dragging multiple files or folders to chart entire albums sequentially.

### 🖥️ User Interface

- **Modern GUI:** Clean, vertical layout with integrated Dark Mode.
- **Metadata Management:** Auto-fetches Title, Artist, Album, and Year using MusicBrainz.
- **Album Art:** Drag and drop cover art support with automatic downloading from metadata sources.
- **Advanced Controls:** Fine-tune the engine with sliders for Chord Density, Sustain Length, and "No Orange" mode.
- **Action Bar:** Unified footer with easy access to Logs, Help, and Generation controls.

### ⚙️ Engine Capabilities

- **Smart Delay:** Automatically shifts the chart start time to provide a 3-second "runway" before the first note hits.
- **Lane Logic:** Weighted probabilistic generation that favors ergonomic finger movements.
- **Star Power:** Algorithmic placement of Star Power phrases.
- **Determinism:** Seed-based generation ensures the same settings always produce the exact same chart.

### 🛡️ Validation & Polish

- **Health Check:** Integrated validator scans for errors (empty charts, bad durations, density spikes) immediately after generation.
- **Safe Inputs:** Dropdowns and spinners are scroll-locked to prevent accidental value changes.
- **Output Management:** Quick actions to open the destination folder or the generated song file immediately.
