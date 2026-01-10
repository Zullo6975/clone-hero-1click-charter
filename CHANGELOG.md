# Changelog

## [1.3.0] - 2026-01-10

### 🩹 Critical Fixes & Polish

- **Clone Hero Sections:** Fixed a major bug where sections were invisible in-game. The engine now correctly injects standard "Text Events" into a dedicated `EVENTS` track (Track 1), complying with strict Clone Hero MIDI standards.
- **Star Power 2.0:** Overhauled the SP generation logic. It now targets high-density sections (solos/choruses) and includes a safety buffer to ensure activation phrases never extend past the song's end.
- **Validator Upgrade:** The health check now verifies that sections exist on the correct track ("EVENTS") and detects formatting issues.
- **UI Polish:** Success popups are now wider (600px) by default to prevent long output file paths from wrapping.
- **Warning Detection:** The log parser is now case-insensitive, ensuring "Warning: ..." lines are correctly flagged in the completion popup.
- **Dynamic Complexity:** Charts now display a calculated difficulty rating (0-6 dots) in the Clone Hero song list instead of `?`.

## [1.2.1] - 2026-01-09

### Community Standards

Updating the repo to meet all GitHub community standards.

## [1.2.0] - 2026-01-09

### The "Power User" Update

This update puts control in your hands. You can now save your favorite settings, visualize the song's difficulty structure before generating, and rename sections to match the song perfectly.

### 🎛️ New Features

- **User Presets:** Save your custom engine settings (NPS, Gap, Density) into named presets like "My Thrash Settings" for easy recall.
- **Density Visualizer:** A new interactive graph in the Review window shows note intensity peaks over time, letting you "see" the difficulty spikes before you play.
- **Section Overrides:** New "Override Section Names" checkbox allows you to review detected sections and rename them (e.g., "Guitar Solo", "Verse 1") before the chart is generated.

### 🖥️ UI/UX Polish

- **Status Bar:** Added padding to the status bar for a cleaner look.
- **Log Window:** Fixed default sizing to ensure logs are readable immediately upon opening.
- **Review Dialog:** Interactive table for renaming sections with locked timestamps to preserve rhythmic integrity.

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
