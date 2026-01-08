# CloneHero 1-Click Generator

**CloneHero 1-Click Generator** is a Python-based tool that creates **fun, playable lead guitar charts** from any audio file in seconds.

It is designed for players who want to expand their library without spending hours manually charting. The focus is on **Medium-difficulty** gameplay that feels good—predictable, rhythmic, and fair.

(Assisted by ChatGPT, and Gemini)

---

## ✨ Features

- **One-Click Generation:** Drag an audio file, click "Generate", and play.
- **Smart Difficulty:** Charts are "groove-locked" to a 1/8 beat grid to ensure they feel musical, not random.
- **Auto-Metadata:** Fetches Album Art, Year, and Album Title from MusicBrainz automatically.
- **Smart Delay:** Automatically shifts the chart to ensure you have a "runway" before the first note hits (no more instant-fail starts).
- **Validation:** Built-in health check scans for errors (like impossible patterns or silence) before you even launch the game.

### 🎛 Advanced Customization

While the defaults are tuned for a "GH3 Medium" feel, you can tweak the engine:

- **No Orange Toggle:** Disable the 5th lane for a purer 4-lane experience.
- **Chord Density:** Slide from "All Taps" to "Power Chord Heavy".
- **Sustain Length:** Control how "sticky" the notes are (short & punchy vs. long & flowing).
- **Grid Snap:** Loosen the timing to 1/16 notes for faster songs, or lock it to 1/4 for a march feel.

---

## 🚀 Installation

### 1. Requirements

- Python 3.10+
- Git

### 2. Setup

Clone the repo and run the install script:

```bash
git clone [https://github.com/yourusername/clone-hero-1click-charter.git](https://github.com/yourusername/clone-hero-1click-charter.git)
cd clone-hero-1click-charter
make install
```

### 3. Run the App

Launch the GUI:

```bash
make gui
```

## 🎮 How to Use

1. Input Audio: Drag & Drop an .mp3, .ogg, .wav, or .flac file into the top box.
2. Metadata: Verify the Song Title and Artist. The app will try to auto-fill these.
3. Cover Art: Drag an image into the "Album Art" box (optional).
4. Settings (Optional): Check "Show Advanced Settings" to tweak density, chords, or disable the Orange lane.
5. Generate: Click the blue button.
6. Play: Move the generated folder into your Clone Hero Songs directory and scan for changes.

## 🗺 Roadmap

### Phase 1: The Core Experience (✅ Complete)

- [x] Drag & Drop GUI with "Pointing Hand" interactions
- [x] Auto-Metadata & Cover Art
- [x] "Smart Delay" start buffer
- [x] Advanced Tuning (Chords, Sustains, Orange Lane)
- [x] Validation & Error Reporting

### Phase 2: Batch Processing (Next Up)

- [ ] Queue System: Drag multiple songs at once.
- [ ] Batch Worker: Process an entire album in the background.
- [ ] Summary Report: "10 Succeeded, 2 Failed".

### Phase 3: Multi-Difficulty Architecture (Long Term)

- [ ] The "4-Stream" Engine: Generate Easy, Medium, Hard, and Expert charts simultaneously.
- [ ] Cascading Reduction: Generate Expert first, then algorithmically reduce notes for lower difficulties to ensure consistency across tiers.
- [ ] Unified Output: One folder containing all 4 difficulties ready for full party play.

## 🤝 Contributing

See [CONTRIBUTING.md](/clone-hero-1click-charter/CONTRIBUTING.md) for style guides and design philosophy.

## 📄 License

MIT License. Free to use, modify, and distribute.
