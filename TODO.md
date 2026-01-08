# Project Roadmap

## 🟢 v1.1: The "Musicality" Update (Next)

**Focus:** Making the engine smarter so charts feel less "random" and more like the song.

- [ ] **Pitch Contouring:** Analyze audio pitch direction.
  - *Goal:* If the melody climbs, notes move Right (Green -> Orange). If it falls, notes move Left.
- [ ] **Rhythmic Glue:** Detect repeated rhythmic motifs (e.g., "dun-dun-bap").
  - *Goal:* Force the engine to use the same chord/strum pattern when the audio repeats a rhythm.
- [ ] **Smart Sections:** Improve segmentation logic.
  - *Goal:* Identify "Solo" sections based on high note density/frequency and label them automatically.
- [ ] **Audio Normalization:** Auto-gain input audio to a standard -14 LUFS.
  - *Goal:* Consistent volume levels in-game for all charts.

---

## 🟡 v1.2: Power User Controls

**Focus:** Giving users granular control over the generation parameters.

- [ ] **User Presets:** Save and load custom configuration profiles (e.g., "My Thrash Metal Settings") to a local JSON file.
- [ ] **Manual Overrides:** A simple table view to review/edit data before generation.
  - *Features:* Rename sections, adjust specific section difficulty, or tweak the start offset manually.
- [ ] **Density Visualizer:** A small graph in the UI showing note density over time.
  - *Goal:* Let users see where the difficulty spikes are before they play.

---

## 🟠 v2.0: Multi-Difficulty Architecture

**Focus:** Moving from a single "Medium" chart to a full difficulty suite.

- [ ] **The "Expert" Engine:** Create a new generation profile for Expert (1/16 grid, complex chords, 3-note chords allowed).
- [ ] **Reduction Algorithm:** Create a logic system to "dumb down" an Expert chart.
  - *Expert -> Hard:* Remove 20% of notes, simplify complex chords.
  - *Hard -> Medium:* Remove Orange, enforce 1/8 grid strictness.
  - *Medium -> Easy:* On-beat only, mostly single notes.
- [ ] **Unified MIDI Writer:** Update `midi.py` to write `PART GUITAR`, `EASY`, `MEDIUM`, `HARD`, and `EXPERT` tracks into a single `.mid` file.

---

## 🔴 v2.1 and beyond: Community & Polish (Long Term)

**Focus:** Features for sharing and distribution.

- [ ] **Chart Export:** Option to export in `.chart` format (text-based) for editing in Moonscraper.
- [ ] **Auto-Update:** In-app notification when a new GitHub Release is available.
- [ ] **Batch Reporting:** A summary screen after a large batch job ("Processed 50 songs: 48 Success, 2 Failed").
- [ ] 