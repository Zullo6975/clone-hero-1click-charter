# CloneHero 1-Click Charter

**CloneHero 1-Click Charter** is a desktop application that creates **fun, playable lead guitar charts** from any audio file in seconds.

It is designed for players who want to expand their library without spending hours manually charting.

Assisted by ChatGPT and Gemini.

![Main Application](assets/images/main_app.png)

---

## ✨ Features

- **Multi-Difficulty Generation:** Automatically creates Easy, Medium, Hard, and Expert charts in one go.
- **One-Click Generation:** Drag an audio file, click "Generate", and play.
- **Moonscraper Support:** Option to export `.chart` files for manual editing.
- **Batch Queueing:** Drag an entire folder of songs to process them automatically with a detailed summary report.
- **Smart Difficulty:** Charts are "groove-locked" to a 1/8 beat grid to ensure they feel musical, not random.
- **Auto-Metadata:** Fetches Album Art, Year, and Album Title from MusicBrainz automatically.
- **Smart Delay:** Automatically shifts the chart to ensure you have a "runway" before the first note hits.
- **Validation:** Built-in health check scans for errors (like impossible patterns or silence) before you even launch the game.
- **Density Visualizer:** See graphs of the song's difficulty spikes for every difficulty level.
- **User Presets:** Save and load your own custom configuration profiles.

### 🎛 Advanced Customization

While the defaults are tuned for a "GH3 feel", you can tweak the engine:

![Advanced Settings Baseline](assets/images/settings_panel1.png)
![Advanced Settings Difficulty Gap](assets/images/settings_panel2.png)

- **Difficulty Scaling:** Set specific **Target NPS** (Notes Per Second) for Easy, Medium, and Hard to fine-tune the difficulty curve.
- **User Presets:** Save your favorite settings (e.g., "Chill", "Chaotic") and load them instantly.
- **Manual Overrides:** Rename sections (like "Guitar Solo") before the chart is built.
- **Chord Density:** Slide from "All Taps" to "Power Chord Heavy".
- **Sustain Length:** Control how "sticky" the notes are.

---

## 🚀 Installation

### 1. Download

Grab the latest version for **Windows** or **macOS** from the [Releases Page](../../releases).

### 2. Run

- **Windows:** Extract the zip and run `1ClickCharter.exe`.
- **macOS:** Extract the zip and run `1ClickCharter.app`.

---

## 🎮 How to Use

1. **Input Audio:** Drag & Drop audio files (`.mp3`, `.ogg`, `.wav`) into the top box.
   - _Tip:_ Drag multiple files to add them to the **Pending Queue**.
2. **Metadata:** Verify the Song Title and Artist. The app will try to auto-fill these.
3. **Cover Art:** Drag an image into the "Album Art" box (optional).
4. **Output:** Select where you want the song folder to be saved (e.g., your Clone Hero `Songs` folder).
5. **Review (Optional):** If you enabled "Review Sections", you'll see the visualizer before generation.

![Section Review/Visualizer](assets/images/section_review.png)

1. **Generate:** Click the **GENERATE CHART** button.
2. **Next Song:** If you queued multiple files, the app automatically loads the next one for you to review.

---

## 🗺 Roadmap

### v1.0 - v2.0 (Completed)

- [x] Full GUI with Dark Mode
- [x] Batch Queue System
- [x] Multi-Difficulty Generation (Easy -> Expert)
- [x] Difficulty Scaling & Visualizers

### v2.1: Interoperability (Completed)

- [x] **Chart Export:** Option to export in `.chart` format for Moonscraper.
- [x] **Batch Reporting:** Summary screen after large batch jobs ("Processed 50 songs: 48 Success, 2 Failed").
- [x] **Resilient Queue:** Failures no longer stop the entire batch.
- [x] **Auto-Update:** In-app notification for new GitHub Releases.
- [x] **Batch Workflow Fix:** Consistent metadata autofill for all queued songs.

### Future Goals

- [ ] **v2.2.0:** Basic Lyric support (Metadata fetching & Track scaffolding).
- [ ] **v2.2.1:** Smart Lyric support (Rhythmic alignment).
- [ ] **v3.0.0:** Full Band support (Bass, Rhythm).

---

## 💙 Support & Contact

If this tool saved you time, consider buying me a coffee (or a beer) to keep the development going!

- **Venmo:** [@oneclickcharter](https://venmo.com/u/oneclickcharter)
- **Support Email:** [oneclickcharter-support@outlook.com](mailto:oneclickcharter-support@outlook.com)

---

## 🤝 Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for style guides and design philosophy.

## 📄 License

MIT License. Free to use, modify, and distribute.
