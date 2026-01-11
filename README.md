# CloneHero 1-Click Charter

**CloneHero 1-Click Charter** is a desktop application that creates **fun, playable lead guitar charts** from any audio file in seconds.

It is designed for players who want to expand their library without spending hours manually charting.

Assisted by ChatGPT and Gemini.

---

## ✨ Features

- **Multi-Difficulty Generation:** Automatically creates Easy, Medium, Hard, and Expert charts in one go.
- **One-Click Generation:** Drag an audio file, click "Generate", and play.
- **Batch Queueing:** Drag an entire folder of songs to process them one by one automatically.
- **Smart Difficulty:** Charts are "groove-locked" to a 1/8 beat grid to ensure they feel musical, not random.
- **Auto-Metadata:** Fetches Album Art, Year, and Album Title from MusicBrainz automatically.
- **Smart Delay:** Automatically shifts the chart to ensure you have a "runway" before the first note hits.
- **Validation:** Built-in health check scans for errors (like impossible patterns or silence) before you even launch the game.
- **Density Visualizer:** See graphs of the song's difficulty spikes for every difficulty level.
- **User Presets:** Save and load your own custom configuration profiles.

### 🎛 Advanced Customization

While the defaults are tuned for a "GH3 feel", you can tweak the engine:

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
5. **Generate:** Click the **GENERATE CHART** button.
6. **Next Song:** If you queued multiple files, the app automatically loads the next one for you to review.

---

## 🗺 Roadmap

### v1.0 - v1.3 (Completed)

- [x] Full GUI with Dark Mode
- [x] Batch Queue System
- [x] Auto-Metadata & Cover Art
- [x] Chart Validation & Health Checks
- [x] User Presets & Density Visualization
- [x] Dynamic Difficulty Rating

### v2.0 (Completed)

- [x] **Multi-Difficulty:** Generate Easy, Medium, Hard, and Expert charts simultaneously.
- [x] **Cascading Reduction:** Algorithmically reduce Expert charts to create lower difficulties.
- [x] **Unified Output:** One folder containing all 4 difficulties ready for full party play.
- [x] **Difficulty Scaling GUI:** Fine-tune the reduction parameters using Target NPS.

## v2.1: Interoperability (NEXT)

- [ ] **Chart Export:** Option to export in `.chart` format (text-based) for editing in Moonscraper.
- [ ] **Batch Reporting:** A summary screen after a large batch job ("Processed 50 songs: 48 Success, 2 Failed").
- [ ] **Lyrics:** Basic lyric generation integration.
- [ ] **Auto-Update:** In-app notification when a new GitHub Release is available.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for style guides and design philosophy.

## 📄 License

MIT License. Free to use, modify, and distribute.
