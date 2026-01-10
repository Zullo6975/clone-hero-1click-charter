# Project Roadmap

## 🟢 v1.1: The "Musicality" Update (COMPLETE)

**Focus:** Making the engine smarter so charts feel less "random" and more like the song.

- [x] **Pitch Contouring:** Analyze audio pitch direction (Up/Down).
- [x] **Sustain Physics:** Tuned sustain engine with adjustable gap and buffer logic.
- [x] **Rhythmic Glue:** Detect repeated rhythmic motifs and force consistent patterns.
- [x] **Smart Sections:** Dynamic "Solo" detection based on note density spikes.
- [x] **Audio Normalization:** Auto-gain input audio to a standard -14 LUFS.

---

## 🟡 v1.2: Power User Controls (COMPLETE)

**Focus:** Giving users granular control over the generation parameters.

- [x] **User Presets:** Save and load custom configuration profiles (e.g., "My Thrash Metal Settings") to a local JSON file.
- [x] **Manual Overrides:** A simple table view to review/edit data before generation.
- [x] **Density Visualizer:** A small graph in the UI showing note density over time.

---

## 🟠 v2.0: Multi-Difficulty Architecture (NEXT)

**Focus:** Moving from a single "Medium" chart to a full difficulty suite.

- [ ] **The "Expert" Engine:** Create a new generation profile for Expert (1/16 grid, complex chords, 3-note chords allowed).
- [ ] **Reduction Algorithm:** Create a logic system to "dumb down" an Expert chart.
  - _Expert -> Hard:_ Remove 20% of notes, simplify complex chords.
  - _Hard -> Medium:_ Remove Orange, enforce 1/8 grid strictness.
  - _Medium -> Easy:_ On-beat only, mostly single notes.
- [ ] **Unified MIDI Writer:** Update `midi.py` to write `PART GUITAR`, `EASY`, `MEDIUM`, `HARD`, and `EXPERT` tracks into a single `.mid` file.

---

## 🔴 Long-term Goals

**Focus:** Features for sharing and distribution.

- [ ] **Chart Export:** Option to export in `.chart` format (text-based) for editing in Moonscraper.
- [ ] **Auto-Update:** In-app notification when a new GitHub Release is available.
- [ ] **Batch Reporting:** A summary screen after a large batch job ("Processed 50 songs: 48 Success, 2 Failed").
- [ ] **Lyrics:** Provide lyrics with the song being charted.
- [ ] **Full Band:** Possible addition of further instruments.
- [ ] **UI Refinement:** Always ongoing, nit-picking my GUI configurations.
