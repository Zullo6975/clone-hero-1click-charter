# Changelog

<!-- markdownlint-disable md024 -->

## [2.1.3] - 2026-01-25

### 💅 GUI Polish

- **Modern Windows Theme:** Overhauled the application stylesheet for a cleaner, modern look on Windows 11.
  - Added rounded corners to buttons, inputs, and group boxes.
  - Refined internal padding and margins to reduce the "cramped" feel of the Fusion style.
  - Updated scrollbar and status bar styling for a seamless look.
- **Layout Adjustments:**
  - **Window Size:** Increased default window height to ensure all controls are visible on launch.
  - **Sidebar:** Optimized the "Album Art" preview size (reduced to 200px) to prevent vertical overflow.
  - **Spacing:** Tuned the whitespace between the Sidebar and Main Panel to let the UI breathe without pushing content off-screen.

### 🐛 Bug Fixes

- **Windows Console Safety:** Replaced all emoji characters in CLI scripts (`audio.py`, `make_icons.py`, `setup_ffmpeg.py`, `Makefile`) with text-based equivalents (e.g., `[OK]`, `[ERROR]`). This resolves `UnicodeEncodeError` crashes on Windows systems using legacy console encodings like cp1252.

## [2.1.2] - 2026-01-13

### 🐛 Bug Fixes

- **Medium Difficulty Tuning:** Enforced stricter chord gap rules for Medium difficulty.
  - Chords are now limited to **adjacent notes** (Lane Diff 1) and **1-fret gaps** (Lane Diff 2).
  - Spans larger than 1 fret (e.g., Green+Blue, Diff 3) are now reduced to single notes to prevent awkward stretches.
- **Solo Detection:** Relaxed the thresholds for detecting "Guitar Solos".
  - Time window widened to 40%-90% of the song duration.
  - Density Requirement lowered to 65% of the song's peak (was 80%), helping to catch solos in less dense tracks.

## [2.1.1] - 2026-01-12

### 🩹 Batch Workflow Hotfix

- **Consistent Autofill:** The "Run Queue" command now forces metadata autofill (Title/Artist) for the _entire_ batch, including the currently loaded song. This overrides manual text entry in the main window to ensure that large batches processed from folders utilize the correct metadata from the file tags every time.

## [2.1.0] - 2026-01-12

### 🔌 The "Interoperability" Update

This release focuses on making 1-Click Charter play nicely with other tools and improving the experience for power users processing large libraries.

### 🌟 New Features

- **.chart Export:** You can now generate `.chart` files alongside the standard MIDI. This allows for immediate editing in **Moonscraper** without conversion. Enable this in the "Advanced Settings" tab.
- **Batch Reporting:** The batch processor is now smarter.
  - **Continue-on-Error:** If one song fails, the queue will log it and keep going instead of stopping.
  - **Summary Screen:** At the end of a batch, a detailed table shows which songs succeeded and which failed.
- **Auto-Update Check:** The app now checks for new releases on startup and displays a notification button in the footer if an update is available.

### 🛠 Improvements

- **Queue Stability:** Fixed issues where the UI could freeze between songs in a large queue.
- **Error Handling:** Improved error logging for audio normalization failures.

## [2.0.0] - 2026-01-11

### 🚀 The "Full Stack" Update

This major release brings 1-Click Charter up to industry standards by generating full difficulty stacks (Easy, Medium, Hard, Expert) automatically.

### 🌟 New Features

- **Multi-Difficulty Generation:** The engine now produces 4 separate difficulty tracks (`PART GUITAR`, `EASY`, `MEDIUM`, `HARD`, `EXPERT`) in a single MIDI file.
- **Difficulty Scaling:** A new **"Difficulty Scaling"** tab in Advanced Settings allows you to tune the reduction logic. Set a **"Target NPS"** (e.g., 5.0 NPS for Medium) and the engine calculates the required millisecond gap automatically.
- **Review Tabs:** The Density Visualizer now has tabs for **Expert, Hard, Medium, and Easy**, letting you inspect the difficulty curve for every level before generating.
- **Preset Ordering:** Default presets are now numbered 1-4, and custom presets start at 5, keeping your list organized.

### 🛠 Improvements

- **Reduction Algorithm:** Expert charts are intelligently "reduced" to create lower difficulties:
  - **Hard:** Simplifies complex chords and reduces density by ~20%.
  - **Medium:** Removes 5th lane (Orange) and enforces stricter timing.
  - **Easy:** Focuses on downbeats and single notes.
- **UI Polish:** The progress bar now animates (bounces) to show activity during long generation tasks.
- **Documentation:** Added a "Help" (Info) button to the Settings panel explaining the new scaling controls.

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
