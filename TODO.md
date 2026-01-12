# Project Roadmap

## 🟢 v1.1: The "Musicality" Update (COMPLETE)

**Focus:** Making the engine smarter so charts feel less "random" and more like the song.

- [x] **Pitch Contouring:** Analyze audio pitch direction (Up/Down).
- [x] **Sustain Physics:** Tuned sustain engine with adjustable gap and buffer logic.
- [x] **Rhythmic Glue:** Detect repeated rhythmic motifs and force consistent patterns.
- [x] **Smart Sections:** Dynamic "Solo" detection based on note density spikes.
- [x] **Audio Normalization:** Auto-gain input audio to a standard -14 LUFS.

---

## 🟢 v1.2: Power User Controls (COMPLETE)

**Focus:** Giving users granular control over the generation parameters.

- [x] **User Presets:** Save and load custom configuration profiles (e.g., "My Thrash Metal Settings") to a local JSON file.
- [x] **Manual Overrides:** A simple table view to review/edit data before generation.
- [x] **Density Visualizer:** A small graph in the UI showing note density over time.

---

## 🟢 v2.0: Multi-Difficulty Architecture (COMPLETE)

**Focus:** Moving from a single "Medium" chart to a full difficulty suite.

- [x] **The "Expert" Engine:** Create a new generation profile for Expert (1/16 grid, complex chords, 3-note chords allowed).
- [x] **Reduction Algorithm:** Create a logic system to "dumb down" an Expert chart.
  - _Expert -> Hard:_ Remove 20% of notes, simplify complex chords.
  - _Hard -> Medium:_ Remove Orange, enforce 1/8 grid strictness.
  - _Medium -> Easy:_ On-beat only, mostly single notes.
- [x] **Unified MIDI Writer:** Update `midi.py` to write `PART GUITAR`, `EASY`, `MEDIUM`, `HARD`, and `EXPERT` tracks into a single `.mid` file.
- [x] **Difficulty Scaling Control:** GUI tab to fine-tune the reduction parameters (Gap/NPS).

---

## 🟢 v2.1: Interoperability (COMPLETE)

**Focus:** Making it easier to use 1-Click Charter with other tools and improving batch reliability.

- [x] **Chart Export:** Option to export in `.chart` format (text-based) for editing in Moonscraper.
- [x] **Batch Reporting:** A summary screen after a large batch job.
- [x] **Resilient Queue:** Ensure one failed song doesn't stop the whole queue.
- [x] **Auto-Update:** In-app notification when a new GitHub Release is available.
- [x] **Unified Batch Metadata:** (v2.1.1) Ensure queue runner autofills metadata for all items, ignoring manual inputs for the first song.

---

## 🟡 v2.2: Lyric Support (NEXT)

**Focus:** Adding vocal engagement to the charts.

- [ ] **v2.2.0 (Basic):** Retrieve lyrics from metadata services and implement basic `PART VOCALS` track structure.
- [ ] **v2.2.1 (Smart):** Intelligent syllable alignment and rhythmic placement of lyric events.

---

## 🟡 v3.0: Full Band (FUTURE)

**Focus:** Transforming from a guitar tool to a full band suite.

- [ ] **Instrument Expansion:** Support for Bass and Rhythm Guitar generation.
- [ ] **Stem Separation:** (Potential) Integration of source separation to isolate bass lines.
