# Changelog

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
